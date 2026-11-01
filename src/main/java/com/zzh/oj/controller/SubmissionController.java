package com.zzh.oj.controller;

import com.zzh.oj.common.PageResult;
import com.zzh.oj.common.Result;
import com.zzh.oj.dto.SubmissionDetailVO;
import com.zzh.oj.dto.SubmissionVO;
import com.zzh.oj.dto.SubmitRequest;
import com.zzh.oj.dto.SubmitResponse;
import com.zzh.oj.service.SubmissionService;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/submissions")
@RequiredArgsConstructor
public class SubmissionController {

    private final SubmissionService submissionService;

    /** 提交代码并判题 */
    @PostMapping
    public Result<SubmitResponse> submit(@RequestBody SubmitRequest req) {
        return Result.ok(submissionService.submit(req));
    }

    /** 提交记录分页列表 */
    @GetMapping
    public Result<PageResult<SubmissionVO>> list(
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "10") int size) {
        return Result.ok(submissionService.list(page, size));
    }

    /** 单条提交详情 */
    @GetMapping("/{id}")
    public Result<SubmissionDetailVO> detail(@PathVariable Long id) {
        return Result.ok(submissionService.detail(id));
    }
}
