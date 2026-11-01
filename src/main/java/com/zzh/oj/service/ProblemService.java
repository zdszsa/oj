package com.zzh.oj.service;

import com.zzh.oj.common.BusinessException;
import com.zzh.oj.entity.Problem;
import com.zzh.oj.mapper.ProblemMapper;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.List;

/**
 * 题目业务：介于 Controller 和 Mapper 之间
 * Controller 只负责收参数、返结果；Mapper 只管 SQL；判断和组装放这里
 */
@Service
@RequiredArgsConstructor
public class ProblemService {

    private final ProblemMapper problemMapper;

    public List<Problem> list() {
        return problemMapper.selectAll();
    }

    public Problem detail(Long id) {
        Problem p = problemMapper.selectById(id);
        if (p == null) {
            throw BusinessException.notFound("题目 " + id + " ");
        }
        return p;
    }
}
