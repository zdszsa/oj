package com.zzh.oj.mapper;

import com.zzh.oj.entity.TestCase;
import org.apache.ibatis.annotations.Mapper;

import java.util.List;

@Mapper
public interface TestCaseMapper {

    /** 按题目查所有用例，按 ordinal 升序 */
    List<TestCase> selectByProblemId(Long problemId);
}
