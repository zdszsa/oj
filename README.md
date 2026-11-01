# 在线判题系统（OJ）

一个支持在线编写、提交、自动判题的 Java 代码评测系统。

## 功能

- 题目列表、题目详情
- 在线编写 Java 代码并提交
- **自动判题**：通过 / 答案错误 / 编译错误 / 运行错误 / 超时
- 提交记录查询（分页、详情含代码与输出）
- 基于 Redis 的提交频率限制
- **AI 代码点评**（接入 DeepSeek，异步生成）

## 技术栈

`Spring Boot 3.2` · `MyBatis` · `MySQL 8` · `Redis` · `Nginx` · `Rocky Linux 9` · `DeepSeek API`

## 整体架构

```
浏览器 → Nginx(反向代理) → Spring Boot(8081) → MySQL
                                              → Redis
                                              → ProcessBuilder → javac / java（独立进程）
```

## 判题流程

1. **限流**：Redis + Lua 脚本按用户计数，超限直接拒绝
2. **落库**：先写入一条 `PENDING` 提交记录（即使后续崩溃也能查到）
3. **逐用例执行**：
   - 代码写入临时目录 → `javac` 编译（失败即 `COMPILE_ERROR`）
   - 启动独立 `java` 进程，喂入标准输入后**关闭 stdin 发送 EOF**
   - `waitFor` 带超时等待，超时则 `destroyForcibly` 强杀
4. **比对输出**：归一化（统一换行符、去行尾空格）后比较，不一致即 `WRONG_ANSWER`
5. **失败即返回**：任一用例失败立刻停止，不再执行剩余用例
6. **异步 AI 点评**：固定线程池 + 有界队列，与判题主流程完全解耦

## 几个关键设计

| 问题 | 做法 |
|---|---|
| 用户代码可能 `System.exit` 杀掉整个 JVM | 用**独立进程**执行，而不是线程或反射 |
| 死循环代码拖垮服务器 | `waitFor(2s)` + `destroyForcibly()` 强杀 |
| 用户代码一直等输入导致超时 | 写完 stdin 必须 `close()`，发送 EOF |
| `readAllBytes` 阻塞导致超时判断失效 | 必须在 `waitFor` **之后**读取输出 |
| 答案错误时泄露正确答案 → 可作弊 | 只返回"第几组用例未通过" |
| 判题耗时长，占用数据库连接 | 判题**不放在事务内**，拆成「落库 → 判题 → 回写」 |
| Redis 挂了导致提交全部失败 | 限流自动**降级放行**，不影响核心判题 |
| 大模型调用失败拖垮判题 | 异步 + 有界队列 + 静默降级 |
| 判题工具路径写死，无法跨平台 | 路径外置为配置项，Windows/Linux 共用同一份 jar |

## 本地运行

```bash
# 1. 建库并导入初始数据
mysql -uroot -p < src/main/resources/db/schema.sql
mysql -uroot -p < src/main/resources/db/data.sql

# 2. 配置本地环境
cp src/main/resources/application-local.properties.example \
   src/main/resources/application-local.properties
# 填入你的 DeepSeek API Key（不填也能跑，只是没有 AI 点评）

# 3. 启动
mvn spring-boot:run
```

访问 http://localhost:8080

> Redis 没启动也能跑，提交限流会自动降级为"不限制"，判题正常。

## 项目结构

```
src/main/java/com/zzh/oj
├── ai/          AI 代码点评
├── common/      统一响应体、全局异常、分页结果
├── config/      线程池、RestTemplate
├── controller/  接口层
├── dto/         出入参
├── entity/      实体
├── judge/       判题内核（CodeRunner / JudgeService / JudgeStatus）
├── limit/       Redis 限流
├── mapper/      MyBatis Mapper
└── service/     业务逻辑
```
