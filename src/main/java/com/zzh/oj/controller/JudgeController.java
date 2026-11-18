package com.zzh.oj.controller;

import com.zzh.oj.common.Result;
import com.zzh.oj.judge.JudgeDispatcher;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

/**
 * 判题队列的运行时状态
 *
 * 单机内存队列最怕的是「悄悄堆满」：用户看到一直在转圈，运维什么都不知情。
 * 把排队数和拒绝数暴露出来，队列水位就能被监控到 —— 这是压测和排查的依据，
 * 也是后面接 Prometheus 的挂载点。
 */
@RestController
@RequestMapping("/api/judge")
@RequiredArgsConstructor
public class JudgeController {

    private final JudgeDispatcher judgeDispatcher;

    @GetMapping("/stats")
    public Result<String> stats() {
        return Result.ok(judgeDispatcher.stats());
    }
}
