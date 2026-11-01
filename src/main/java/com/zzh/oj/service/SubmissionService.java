package com.zzh.oj.service;

import com.zzh.oj.ai.AiReviewService;
import com.zzh.oj.common.BusinessException;
import com.zzh.oj.common.PageResult;
import com.zzh.oj.dto.SubmissionDetailVO;
import com.zzh.oj.dto.SubmissionVO;
import com.zzh.oj.dto.SubmitRequest;
import com.zzh.oj.dto.SubmitResponse;
import com.zzh.oj.entity.Problem;
import com.zzh.oj.entity.Submission;
import com.zzh.oj.entity.SubmissionDetail;
import com.zzh.oj.judge.JudgeOutcome;
import com.zzh.oj.judge.JudgeService;
import com.zzh.oj.judge.JudgeStatus;
import com.zzh.oj.limit.SubmitRateLimiter;
import com.zzh.oj.mapper.ProblemMapper;
import com.zzh.oj.mapper.SubmissionDetailMapper;
import com.zzh.oj.mapper.SubmissionMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.util.List;

import static com.zzh.oj.judge.JudgeStatus.PENDING;

@Slf4j
@Service
@RequiredArgsConstructor
public class SubmissionService {

    private final SubmissionMapper submissionMapper;
    private final SubmissionDetailMapper detailMapper;
    private final JudgeService judgeService;
    private final SubmitRateLimiter rateLimiter;
    private final ProblemMapper problemMapper;
    private final AiReviewService aiReviewService;

    /** 暂无登录，先写死用户 id */
    private static final Long DEFAULT_USER_ID = 1L;

    /**
     * 提交并判题。
     *
     * 注意这里【没有】加 @Transactional：
     * 判题要跑好几个子进程，可能耗时几秒。如果包在事务里，
     * 数据库连接会被占住几秒，并发一高连接池就打满了。
     * 所以拆成「先落库 → 判题 → 再回写」，判题这一段不占连接。
     */
    public SubmitResponse submit(SubmitRequest req) {

        if (req.getProblemId() == null) {
            throw BusinessException.badRequest("problemId 不能为空");
        }
        if (req.getCode() == null || req.getCode().isBlank()) {
            throw BusinessException.badRequest("代码不能为空");
        }

        // 0. 先限流：判题是最贵的操作，不能让一个人把机器刷爆
        rateLimiter.check(DEFAULT_USER_ID);

        // 1. 先落一条「判题中」的记录，这样即使后面崩了也能查到这次提交
        Submission s = new Submission();
        s.setUserId(1L);                 // TODO 接入登录后换成真实用户
        s.setProblemId(req.getProblemId());
        s.setLanguage("java");
        s.setStatus(PENDING.getCode());
        s.setTimeMs(0);
        submissionMapper.insert(s);

        // 2. 代码单独存
        SubmissionDetail d = new SubmissionDetail();
        d.setSubmissionId(s.getId());
        d.setCode(req.getCode());
        detailMapper.insert(d);

        // 3. 判题
        JudgeOutcome outcome = judgeService.judge(req.getProblemId(), req.getCode());

        // 4. 回写结果
        submissionMapper.updateStatus(s.getId(), outcome.getStatus().getCode(), (int) outcome.getTimeMs());
        if (outcome.getOutput() != null && !outcome.getOutput().isEmpty()) {
            detailMapper.updateOutput(s.getId(), outcome.getOutput());
        }

        // 5. 异步 AI 评审 —— 提交出去就返回，不等它
        //    编译都过不了的代码没什么可评审的，直接跳过，省一次调用
        if (outcome.getStatus() != JudgeStatus.COMPILE_ERROR) {
            Problem p = problemMapper.selectById(req.getProblemId());
            if (p != null) {
                aiReviewService.reviewAsync(s.getId(), p.getTitle(), req.getCode());
            }
        }

        return SubmitResponse.builder()
                .submissionId(s.getId())
                .status(outcome.getStatus().getCode())
                .statusText(outcome.getStatus().getText())
                .timeMs(outcome.getTimeMs())
                .output(outcome.getOutput())
                .passedCases(outcome.getPassedCases())
                .totalCases(outcome.getTotalCases())
                .build();
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

    /** 单条提交详情（含代码和判题输出） */
    public SubmissionDetailVO detail(Long id) {
        SubmissionDetailVO vo = submissionMapper.selectDetailById(id);
        if (vo == null) {
            throw BusinessException.notFound("提交记录 " + id + " ");
        }
        vo.setStatusText(JudgeStatus.of(vo.getStatus()).getText());
        return vo;
    }
}
