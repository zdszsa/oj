package com.zzh.oj.controller;

import com.zzh.oj.common.Result;
import com.zzh.oj.entity.Problem;
import com.zzh.oj.service.ProblemService;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/api/problems")
@RequiredArgsConstructor
public class ProblemController {

    private final ProblemService problemService;

    /** 题目列表（不含题面） */
    @GetMapping
    public Result<List<Problem>> list() {
        return Result.ok(problemService.list());
    }

    /** 题目详情（含题面） */
    @GetMapping("/{id}")
    public Result<Problem> detail(@PathVariable Long id) {
        return Result.ok(problemService.detail(id));
    }
}
