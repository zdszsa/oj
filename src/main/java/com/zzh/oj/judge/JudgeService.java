package com.zzh.oj.judge;

import com.zzh.oj.common.BusinessException;
import com.zzh.oj.entity.Problem;
import com.zzh.oj.entity.TestCase;
import com.zzh.oj.mapper.ProblemMapper;
import com.zzh.oj.mapper.TestCaseMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.util.List;

import static com.zzh.oj.judge.JudgeStatus.*;

/**
 * 判题服务：拿一组测试用例逐个跑，全部通过才算 AC
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class JudgeService {

    private final ProblemMapper problemMapper;
    private final TestCaseMapper testCaseMapper;

    public JudgeOutcome judge(Long problemId, String code) {

        Problem problem = problemMapper.selectById(problemId);
        if (problem == null) {
            throw BusinessException.notFound("题目 " + problemId + " ");
        }

        List<TestCase> cases = testCaseMapper.selectByProblemId(problemId);
        if (cases.isEmpty()) {
            throw new BusinessException(500, "题目 " + problemId + " 还没有配置测试用例");
        }

        long maxCost = 0;
        int passed = 0;

        for (TestCase c : cases) {

            RunResult r;
            try {
                r = CodeRunner.run(code, c.getInputData(), problem.getTimeLimitMs());
            } catch (Exception e) {
                // 编译/运行之外的意外（磁盘满、进程起不来……）
                log.error("判题异常 problemId={} ordinal={}", problemId, c.getOrdinal(), e);
                return new JudgeOutcome(SYSTEM_ERROR, maxCost,
                        "判题系统异常: " + e.getMessage(), passed, cases.size());
            }

            maxCost = Math.max(maxCost, r.getTimeMs());

            // 编译错误 / 运行错误 / 超时：不用再跑后面的用例了
            if (r.getStatus() != OK) {
                return new JudgeOutcome(r.getStatus(), maxCost, r.getOutput(), passed, cases.size());
            }

            if (!sameOutput(r.getOutput(), c.getExpectedOutput())) {
                // ★ 故意不返回"正确答案是什么"，否则用户可以照着凑
                String msg = "第 " + c.getOrdinal() + " 组用例答案错误";
                return new JudgeOutcome(WRONG_ANSWER, maxCost, msg, passed, cases.size());
            }

            passed++;
        }

        return new JudgeOutcome(OK, maxCost, "", passed, cases.size());
    }

    private boolean sameOutput(String actual, String expected) {
        return normalize(actual).equals(normalize(expected));
    }

    /**
     * 输出比对前的归一化：
     * 1. 换行符统一成 \n（Windows 下可能是 \r\n）
     * 2. 每行去掉行尾空格
     * 3. 整体去掉首尾空白
     *
     * 这一步很重要：用户代码 println 出来的结果，行尾经常带不可见空格，
     * 直接 equals 会误判成 WA。
     */
    private String normalize(String s) {
        if (s == null) {
            return "";
        }
        String[] lines = s.replace("\r\n", "\n").split("\n", -1);
        StringBuilder sb = new StringBuilder();
        for (String line : lines) {
            sb.append(line.stripTrailing()).append('\n');
        }
        return sb.toString().trim();
    }
}
