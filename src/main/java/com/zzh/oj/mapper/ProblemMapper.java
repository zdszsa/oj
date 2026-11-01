package com.zzh.oj.mapper;

import com.zzh.oj.entity.Problem;
import org.apache.ibatis.annotations.Mapper;

import java.util.List;

@Mapper
public interface ProblemMapper {

    /** 题目列表（不含题面大字段） */
    List<Problem> selectAll();

    /** 题目详情 */
    Problem selectById(Long id);
}
