package com.zzh.oj.judge;

/**
 * 判题任务：队列里流动的最小信息
 *
 * 只带 id 和代码，不带 Submission 实体 —— 实体里有一堆字段，
 * 放着让 worker 自己去查反而更清楚，队列里的对象越小越好。
 */
public record JudgeTask(Long submissionId, Long problemId, String code) {
}
