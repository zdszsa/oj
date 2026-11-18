# 在线判题系统（OJ）

一个支持在线编写、提交、自动判题的 Java 代码评测系统。

## 功能

- 题目列表、题目详情（30 道题、92 个测试用例）
- 在线编写 Java 代码并提交
- **自动判题**：通过 / 答案错误 / 编译错误 / 运行错误 / 超时
- **异步判题**：提交立即返回，判题由后台 worker 消费，前端轮询结果
- 提交记录查询（分页、详情含代码与输出）
- 基于 Redis 的提交频率限制
- **AI 代码点评**（接入 DeepSeek，异步生成）

## 技术栈

`Spring Boot 3.2` · `MyBatis` · `MySQL 8` · `Redis` · `Nginx` · `Rocky Linux 9` · `DeepSeek API`

## 整体架构

```
浏览器 → Nginx(反向代理) → Spring Boot(8081) ─┬→ MySQL
                                             ├→ Redis
                                             └→ 判题队列(有界) → judge-worker × 4
                                                                    ↓
                                                          ProcessBuilder → javac / java
```

提交与判题之间隔了一层队列。提交接口只做「限流 + 落库 + 入队」，几十毫秒返回；
判题在固定线程数的 worker 里慢慢消化，接口响应时间与判题耗时无关。

## 判题流程

1. **限流**：Redis + Lua 脚本按用户计数，超限直接拒绝
2. **落库**：在一个事务里写入 `PENDING` 提交记录 + 代码（即使后续崩溃也能查到）
3. **入队**：投进有界阻塞队列；队列满则把该条标记为系统错误并返回 503，让用户重试
4. **worker 消费**（异步，与请求线程无关）：
   - 代码写入临时目录 → `javac` 编译（失败即 `COMPILE_ERROR`）
   - 启动独立 `java` 进程，喂入标准输入后**关闭 stdin 发送 EOF**
   - `waitFor` 带超时等待，超时则 `destroyForcibly` 强杀
5. **比对输出**：归一化（统一换行符、去行尾空格）后比较，不一致即 `WRONG_ANSWER`
6. **失败即返回**：任一用例失败立刻停止，不再执行剩余用例
7. **CAS 回写**：`WHERE id=? AND status=6`，重复投递第二次影响 0 行
8. **异步 AI 点评**：固定线程池 + 有界队列，与判题主流程完全解耦

前端提交后轮询 `GET /api/submissions/{id}`，直到状态不再是 `6`（判题中）。

## 几个关键设计

| 问题 | 做法 |
|---|---|
| 判题要起子进程、端到端 2 秒，同步判题会把接口拖死 | 提交与判题**解耦**，接口只落库入队，判题走固定 worker |
| 用户代码可能 `System.exit` 杀掉整个 JVM | 用**独立进程**执行，而不是线程或反射 |
| 死循环代码拖垮服务器 | `waitFor(2s)` + `destroyForcibly()` 强杀 |
| 用户代码一直等输入导致超时 | 写完 stdin 必须 `close()`，发送 EOF |
| `readAllBytes` 阻塞导致超时判断失效 | 必须在 `waitFor` **之后**读取输出 |
| 答案错误时泄露正确答案 → 可作弊 | 只返回"第几组用例未通过" |
| 判题耗时长，占用数据库连接 | 判题**不放在事务内**，事务只包住两次 insert |
| 队列无限堆积把内存撑爆 | **有界队列 + 拒绝策略**，满了快速失败而不是排队等死 |
| 内存队列在进程重启后丢任务 | 提交先落库，启动时扫 `status=6` 的记录**重建队列** |
| 同一任务被投递两次导致重复回写 | 回写带 `AND status=6` 条件，天然幂等 |
| Redis 挂了导致提交全部失败 | 限流自动**降级放行**，不影响核心判题 |
| 大模型调用失败拖垮判题 | 异步 + 有界队列 + 静默降级 |
| 判题工具路径写死，无法跨平台 | 路径外置为配置项，Windows/Linux 共用同一份 jar |

## 性能数据

本机（i5-125H / 32G，Windows）实测，判题代码为 3 个用例的 A+B：

| 场景 | 结果 |
|---|---|
| 提交接口（异步后） | 50 并发 **QPS 418**，P50 85ms / P99 173ms |
| 提交接口（改异步前，同步判题） | 50 并发 **QPS 8.36**，P99 5.5s；20 并发时 P99 19.7s |
| 判题吞吐 | 4 worker **1.33 题/秒**（单题约 3s，瓶颈在每次提交起 JVM） |
| 背压（队列容量 50） | 300 并发提交：52 受理 / 248 快速拒绝，服务不崩、内存不涨 |

结论：接口受理能力提升约 **50 倍**，而判题吞吐受限于 CPU（每次提交要起 javac + java 两个进程），
这个上限任何架构都改变不了 —— 能做的是把它挡在接口之外，用队列 + 拒绝策略保护服务本身。

复现方式见 `bench_async.py`：

```bash
# 接口受理能力（用编译失败的代码，队列排空快）
python bench_async.py --mode accept --levels 10,50,100 --per-thread 2 --code fast
# 判题吞吐
python bench_async.py --mode throughput --requests 60
```

压测前需放开限流并放大队列：
`--oj.rate-limit.submit.limit=1000000 --oj.judge.queue-capacity=5000`

## 本地运行

```bash
# 1. 建库并导入初始数据（共 30 道题、92 个用例）
mysql --default-character-set=utf8mb4 -uroot -p < src/main/resources/db/schema.sql
mysql --default-character-set=utf8mb4 -uroot -p < src/main/resources/db/data.sql
mysql --default-character-set=utf8mb4 -uroot -p < src/main/resources/db/data_extra_27.sql
# 注意：必须带 --default-character-set=utf8mb4，否则中文 Windows 下
#      客户端按 GBK 解析脚本，会报 "Incorrect string value"

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
├── judge/       判题内核（CodeRunner 执行 / JudgeService 比对 / JudgeDispatcher 队列调度）
├── limit/       Redis 限流
├── mapper/      MyBatis Mapper
└── service/     业务逻辑
```

## 压测与验证脚本

| 文件 | 用途 |
|---|---|
| `bench_async.py` | 异步架构压测：接口受理能力 + 判题吞吐 |
| `bench_concurrency.py` | 早期同步版本的并发压测，保留用于对照 |
| `smoke_async.py` | 异步链路冒烟：验证 提交 → PENDING → 终态 全通 |
| `gen_problems.py` | 题库生成，题目与用例一起产出 |
| `verify_new_problems.py` | 用 Java 参考解验证新题的用例正确性 |

## 运行时可观测

`GET /api/judge/stats` 返回判题队列水位：

```
workers=4 排队=0 容量=200 已接收=751 已完成=747 已拒绝=0
```

排队数持续上涨说明 worker 不够或提交量超过处理能力；已拒绝数非 0 说明队列已打满。
