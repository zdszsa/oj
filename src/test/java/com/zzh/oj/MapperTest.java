package com.zzh.oj;

import com.zzh.oj.entity.Problem;
import com.zzh.oj.entity.TestCase;
import com.zzh.oj.mapper.ProblemMapper;
import com.zzh.oj.mapper.TestCaseMapper;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;

import java.util.List;

import static org.junit.jupiter.api.Assertions.*;

@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.NONE)
class  MapperTest {

    @Autowired
    private ProblemMapper problemMapper;

    @Autowired
    private TestCaseMapper testCaseMapper;

    @Test
    void 题目列表能查出来() {
        List<Problem> list = problemMapper.selectAll();
        list.forEach(p -> System.out.println("  " + p));
        assertEquals(3, list.size(), "应该有 3 道题");
    }

    @Test
    void 题目详情带题面() {
        Problem p = problemMapper.selectById(2L);
        System.out.println("  " + p);
        assertNotNull(p);
        assertNotNull(p.getDescription());
        assertTrue(p.getDescription().contains("回文"), "题面里应该包含标题相关内容");
    }

    @Test
    void 测试用例按题目查得到且有序() {
        List<TestCase> cases = testCaseMapper.selectByProblemId(1L);
        cases.forEach(c -> System.out.println("  " + c));
        assertEquals(3, cases.size());
        assertEquals(1, cases.get(0).getOrdinal(), "第一条应该 ordinal = 1");
    }
}
