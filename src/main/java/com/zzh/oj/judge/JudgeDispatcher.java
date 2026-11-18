package com.zzh.oj.judge;

import com.zzh.oj.ai.AiReviewService;
import com.zzh.oj.entity.Problem;
import com.zzh.oj.mapper.ProblemMapper;
import com.zzh.oj.mapper.SubmissionDetailMapper;
import com.zzh.oj.mapper.SubmissionMapper;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.context.event.ApplicationReadyEvent;
import org.springframework.context.event.EventListener;
import org.springframework.stereotype.Component;

import java.util.List;
import java.util.concurrent.ArrayBlockingQueue;
import java.util.concurrent.RejectedExecutionException;
import java.util.concurrent.ThreadPoolExecutor;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicLong;

/**
 * 判题调度器：提交与判题解耦
 *
 * 【为什么要有这一层】
 * 判题一次要起 javac + java 两个子进程，端到端约 2 秒，是 CPU 密集操作。
 * 原来提交接口同步判题，20 并发时 P99 直接冲到 19.7 秒 —— 请求全在 Tomcat
 * 线程池里排队等 CPU，接口被判题拖死。
 *
 * 现在：提交只做「限流 + 落库 + 入队」，几十毫秒返回 submissionId，
 * 判题交给固定线程数的 worker 慢慢消化。接口的响应时间从此和判题耗时无关。
 *
 * 【为什么不用 RabbitMQ】
 * 单机部署、任务只由本进程消费，引入 MQ 要多维护一个中间件和一套序列化，
 * 收益是「跨进程 + 重启不丢」。后者用启动扫表补上了（见 recoverPending），
 * 前者当前场景不需要。等判题机要横向扩成多台时再换 MQ，那时它才真正有价值。
 */
@Slf4j
@Component
public class JudgeDispatcher {

    private final ThreadPoolExecutor pool;
    private final int queueCapacity;

    private final SubmissionMapper submissionMapper;
    private final SubmissionDetailMapper detailMapper;
    private final JudgeService judgeService;
    private final AiReviewService aiReviewService;
    private final ProblemMapper problemMapper;

    /** 队列水位与处理量，给 /api/judge/stats 用，压测时能直接看到积压 */
    private final AtomicLong acceptedCount = new AtomicLong();
    private final AtomicLong rejectedCount = new AtomicLong();
    private final AtomicLong completedCount = new AtomicLong();

    public JudgeDispatcher(SubmissionMapper submissionMapper,
                           SubmissionDetailMapper detailMapper,
                           JudgeService judgeService,
                           AiReviewService aiReviewService,
                           ProblemMapper problemMapper,
                           @Value("${oj.judge.workers:4}") int workers,
                           @Value("${oj.judge.queue-capacity:200}") int queueCapacity) {

        this.submissionMapper = submissionMapper;
        this.detailMapper = detailMapper;
        this.judgeService = judgeService;
        this.aiReviewService = aiReviewService;
        this.problemMapper = problemMapper;
        this.queueCapacity = queueCapacity;

        // core == max：线程数固定，不搞弹性扩容。
        // 判题吃的是 CPU，线程数超过核数只会互相抢，反而更慢。
        this.pool = new ThreadPoolExecutor(
                workers, workers,
                0L, TimeUnit.MILLISECONDS,
                new ArrayBlockingQueue<>(queueCapacity),
                r -> {
                    Thread t = new Thread(r, "judge-worker");
                    t.setDaemon(true);      // 不阻止 JVM 退出
                    return t;
                },
                // 队列满了直接抛，由 submit() 捕获转成 false。
                // 不能让它无限堆积 —— 堆的是任务，炸的是内存。
                new ThreadPoolExecutor.AbortPolicy());

        log.info("判题调度器已启动：worker={} 队列容量={}", workers, queueCapacity);
    }

    /**
     * 投递判题任务
     *
     * @return true 已入队；false 队列已满，调用方需要把这条提交标记为失败并告知用户重试
     */
    public boolean submit(JudgeTask task) {
        try {
            pool.execute(() -> handle(task));
            acceptedCount.incrementAndGet();
            return true;
        } catch (RejectedExecutionException e) {
            rejectedCount.incrementAndGet();
            log.warn("判题队列已满，拒绝 submissionId={}（当前排队 {}）",
                    task.submissionId(), pool.getQueue().size());
            return false;
        }
    }

    /** worker 的实际工作：判题 → 回写 → 触发 AI 评审 */
    private void handle(JudgeTask task) {
        Long id = task.submissionId();
        long t0 = System.currentTimeMillis();

        JudgeOutcome outcome;
        try {
            outcome = judgeService.judge(task.problemId(), task.code());
        } catch (Exception e) {
            // worker 里抛异常没人接，线程池只会静默丢掉任务，
            // 这条提交就会永远停在「判题中」。所以必须自己兜住。
            log.error("判题异常 submissionId={}", id, e);
            outcome = new JudgeOutcome(JudgeStatus.SYSTEM_ERROR, 0,
                    "判题系统异常: " + e.getMessage(), 0, 0);
        }

        // 带状态条件的回写：只有还处于 PENDING 才写入。
        // 重复投递（比如启动恢复时同一个任务被投了两次）第二次影响 0 行，直接丢弃。
        int updated = submissionMapper.finishIfPending(
                id,
                outcome.getStatus().getCode(),
                (int) outcome.getTimeMs(),
                outcome.getPassedCases(),
                outcome.getTotalCases());

        if (updated == 0) {
            log.warn("submissionId={} 已不是待判题状态，跳过回写", id);
            return;
        }

        if (outcome.getOutput() != null && !outcome.getOutput().isEmpty()) {
            detailMapper.updateOutput(id, outcome.getOutput());
        }

        // 编译都过不了的代码没什么可评审的，跳过省一次调用
        if (outcome.getStatus() != JudgeStatus.COMPILE_ERROR) {
            try {
                Problem p = problemMapper.selectById(task.problemId());
                if (p != null) {
                    aiReviewService.reviewAsync(id, p.getTitle(), task.code());
                }
            } catch (Exception e) {
                log.warn("触发 AI 评审失败 submissionId={}", id, e);
            }
        }

        completedCount.incrementAndGet();
        log.info("判题完成 submissionId={} status={} 耗时={}ms 队列剩余={}",
                id, outcome.getStatus().getText(),
                System.currentTimeMillis() - t0, pool.getQueue().size());
    }

    /**
     * 启动时把库里遗留的「判题中」重新入队
     *
     * 内存队列的代价：进程重启，队列里的任务就没了，数据库里会留下一批
     * 永远 PENDING 的记录。这一步是给内存队列打的补丁 —— 只要提交先落库，
     * 任务就不算丢。
     */
    @EventListener(ApplicationReadyEvent.class)
    public void recoverPending() {
        List<JudgeTask> pending;
        try {
            pending = submissionMapper.selectPendingTasks(2000);
        } catch (Exception e) {
            log.error("扫描待判题记录失败，跳过恢复", e);
            return;
        }
        if (pending.isEmpty()) {
            return;
        }
        int ok = 0;
        for (JudgeTask t : pending) {
            if (submit(t)) {
                ok++;
            } else {
                break;      // 队列满就停，剩下的下次重启再说
            }
        }
        log.info("启动恢复：库里 {} 条待判题，重新入队 {} 条", pending.size(), ok);
    }

    /** 给监控/压测看的运行时快照 */
    public String stats() {
        return String.format(
                "workers=%d 排队=%d 容量=%d 已接收=%d 已完成=%d 已拒绝=%d",
                pool.getCorePoolSize(), pool.getQueue().size(), queueCapacity,
                acceptedCount.get(), completedCount.get(), rejectedCount.get());
    }
}
