package com.zzh.oj.service;

import com.zzh.oj.common.BusinessException;
import com.zzh.oj.common.PageResult;
import com.zzh.oj.dto.SubmissionDetailVO;
import com.zzh.oj.dto.SubmissionVO;
import com.zzh.oj.dto.SubmitRequest;
import com.zzh.oj.dto.SubmitResponse;
import com.zzh.oj.entity.Submission;
import com.zzh.oj.entity.SubmissionDetail;
import com.zzh.oj.judge.JudgeDispatcher;
import com.zzh.oj.judge.JudgeStatus;
import com.zzh.oj.judge.JudgeTask;
import com.zzh.oj.limit.SubmitRateLimiter;
import com.zzh.oj.mapper.SubmissionDetailMapper;
import com.zzh.oj.mapper.SubmissionMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.support.TransactionTemplate;

import java.util.List;

import static com.zzh.oj.judge.JudgeStatus.PENDING;

@Slf4j
@Service
@RequiredArgsConstructor
public class SubmissionService {

    private final SubmissionMapper submissionMapper;
    private final SubmissionDetailMapper detailMapper;
    private final JudgeDispatcher judgeDispatcher;
    private final SubmitRateLimiter rateLimiter;
    private final TransactionTemplate transactionTemplate;

    /** 暂无登录，先写死用户 id */
    private static final Long DEFAULT_USER_ID = 1L;

    /**
     * 提交代码 —— 只负责「落库 + 入队」，判题交给后台 worker
     *
     * 为什么改异步：
     * 判题要起 javac + java 两个子进程，端到端约 2 秒，是纯 CPU 操作。
     * 同步判题时接口的响应时间等于判题时间，20 并发下 P99 冲到 19.7 秒 ——
     * Tomcat 线程全被占住等 CPU。改成异步后接口只剩两次 insert + 一次入队，
     * 响应时间和判题耗时彻底脱钩。
     *
     * 代价（面试要能说）：
     * 1. 用户拿不到即时结果，前端要轮询；
     * 2. 队列在内存里，进程重启会丢任务 —— 用「先落库 + 启动扫表重建队列」补上。
     *
     * 事务边界只包住两次 insert：判题可能在几秒后发生，绝不能放进事务，
     * 否则数据库连接会被占住好几秒。
     */
    public SubmitResponse submit(SubmitRequest req) {

        if (req.getProblemId() == null) {
            throw BusinessException.badRequest("problemId 不能为空");
        }
        if (req.getCode() == null || req.getCode().isBlank()) {
            throw BusinessException.badRequest("代码不能为空");
        }

        // 0. 先限流：判题是最贵的操作，不能让一个人把队列刷爆
        rateLimiter.check(DEFAULT_USER_ID);

        // 1. 落库：主记录 + 代码，两条 insert 放同一个事务
        //    提交记录先落地，后面无论入队成功与否，用户都能在列表里查到这次提交
        Long submissionId = createPendingSubmission(req);

        // 2. 入队。队列满了不阻塞、不堆积，直接失败让用户重试
        boolean accepted = judgeDispatcher.submit(
                new JudgeTask(submissionId, req.getProblemId(), req.getCode()));

        if (!accepted) {
            // 队列满 = 系统当前无法承接，这条标记为系统错误，前端提示稍后重试
            submissionMapper.updateStatus(submissionId, JudgeStatus.SYSTEM_ERROR.getCode(), 0);
            throw new BusinessException(503, "判题队列已满，请稍后重试");
        }

        return SubmitResponse.builder()
                .submissionId(submissionId)
                .status(PENDING.getCode())
                .statusText(PENDING.getText())
                .build();
    }

    /** 两次 insert 包在一个事务里，避免出现「有主记录、没代码」的半截数据 */
    private Long createPendingSubmission(SubmitRequest req) {
        return transactionTemplate.execute(status -> {
            Submission s = new Submission();
            s.setUserId(DEFAULT_USER_ID);
            s.setProblemId(req.getProblemId());
            s.setLanguage("java");
            s.setStatus(PENDING.getCode());
            s.setTimeMs(0);
            submissionMapper.insert(s);

            SubmissionDetail d = new SubmissionDetail();
            d.setSubmissionId(s.getId());
            d.setCode(req.getCode());
            detailMapper.insert(d);

            return s.getId();
        });
    }

    /**
     * 提交记录分页列表
     * size 做上限保护：防止有人传 size=100000 把内存打爆
     */
    public PageResult<SubmissionVO> list(int page, int size) {
        if (page < 1) {
            page = 1;
        }
        if (size < 1 || size > 100) {
            size = 10;
        }

        long total = submissionMapper.countByUserId(DEFAULT_USER_ID);
        List<SubmissionVO> list = submissionMapper.selectVOByUserId(
                DEFAULT_USER_ID, (page - 1) * size, size);

        // 数据库里存的是数字，转成中文给前端
        list.forEach(vo -> vo.setStatusText(JudgeStatus.of(vo.getStatus()).getText()));

        return new PageResult<>(total, page, size, list);
    }

    /** 单条提交详情（含代码和判题输出），前端轮询判题进度也走这个接口 */
    public SubmissionDetailVO detail(Long id) {
        SubmissionDetailVO vo = submissionMapper.selectDetailById(id);
        if (vo == null) {
            throw BusinessException.notFound("提交记录 " + id + " ");
        }
        vo.setStatusText(JudgeStatus.of(vo.getStatus()).getText());
        return vo;
    }
}
