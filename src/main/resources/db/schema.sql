-- ============================================================
--  OJ 在线判题系统 · 建表脚本
--  MySQL 8.0  |  字符集 utf8mb4
-- ============================================================

CREATE DATABASE IF NOT EXISTS oj
    DEFAULT CHARACTER SET utf8mb4
    COLLATE utf8mb4_general_ci;

USE oj;

-- ------------------------------------------------------------
-- 1. 题目表
-- ------------------------------------------------------------
DROP TABLE IF EXISTS problem;
CREATE TABLE problem (
    id              BIGINT       NOT NULL AUTO_INCREMENT COMMENT '题目 ID',
    title           VARCHAR(100) NOT NULL                COMMENT '标题',
    description     TEXT         NOT NULL                COMMENT '题面描述',
    difficulty      TINYINT      NOT NULL DEFAULT 1      COMMENT '难度 1简单 2中等 3困难',
    time_limit_ms   INT          NOT NULL DEFAULT 2000   COMMENT '时间限制（毫秒）',
    memory_limit_mb INT          NOT NULL DEFAULT 256    COMMENT '内存限制（MB）',
    created_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (id)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COMMENT = '题目';

-- ------------------------------------------------------------
-- 2. 测试用例表
-- ------------------------------------------------------------
DROP TABLE IF EXISTS test_case;
CREATE TABLE test_case (
    id              BIGINT   NOT NULL AUTO_INCREMENT COMMENT '用例 ID',
    problem_id      BIGINT   NOT NULL                COMMENT '所属题目',
    input_data      TEXT     NOT NULL                COMMENT '喂给程序的标准输入',
    expected_output TEXT     NOT NULL                COMMENT '期望输出',
    ordinal         INT      NOT NULL DEFAULT 1      COMMENT '第几个用例（执行顺序）',
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY idx_problem (problem_id)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COMMENT = '测试用例';

-- ------------------------------------------------------------
-- 3. 提交记录表（列表页只用这张，不含代码）
-- ------------------------------------------------------------
DROP TABLE IF EXISTS submission;
CREATE TABLE submission (
    id         BIGINT      NOT NULL AUTO_INCREMENT COMMENT '提交 ID',
    user_id    BIGINT      NOT NULL DEFAULT 1       COMMENT '提交人（暂无登录，写死 1）',
    problem_id BIGINT      NOT NULL                 COMMENT '题目 ID',
    language   VARCHAR(20) NOT NULL DEFAULT 'java'  COMMENT '语言',
    status     TINYINT     NOT NULL                 COMMENT '1OK 2CE 3RE 4TLE 5WA 6PENDING 7SYSTEM_ERROR',
    time_ms    INT         NOT NULL DEFAULT 0       COMMENT '耗时（毫秒）',
    created_at DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '提交时间',
    PRIMARY KEY (id),
    KEY idx_user_time    (user_id, created_at),
    KEY idx_problem_time (problem_id, created_at)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COMMENT = '提交记录';

-- ------------------------------------------------------------
-- 4. 提交详情表（大字段单独放，主键与 submission 一对一）
-- ------------------------------------------------------------
DROP TABLE IF EXISTS submission_detail;
CREATE TABLE submission_detail (
    submission_id BIGINT     NOT NULL COMMENT '对应 submission.id',
    code          MEDIUMTEXT NOT NULL COMMENT '用户提交的源码',
    output        TEXT       NULL     COMMENT '判题输出 / 编译错误 / 异常栈',
    ai_review     TEXT       NULL     COMMENT 'AI 代码评审结果',
    PRIMARY KEY (submission_id)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COMMENT = '提交详情';
