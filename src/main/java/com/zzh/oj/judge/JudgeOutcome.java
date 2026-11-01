package com.zzh.oj.judge;

import lombok.AllArgsConstructor;
import lombok.Data;

/**
 * 一道题判完之后的结果
 */
@Data
@AllArgsConstructor
public class JudgeOutcome {

    /** 最终状态 */
    private JudgeStatus status;

    /** 所有用例里最慢的那次耗时（毫秒） */
    private long timeMs;

    /** 展示给用户的信息：编译错误原文 / 异常栈 / 第几个用例挂了 */
    private String output;

    /** 通过了几组用例 */
    private int passedCases;

    /** 一共几组用例 */
    private int totalCases;
}
