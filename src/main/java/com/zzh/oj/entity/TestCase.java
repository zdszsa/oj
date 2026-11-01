package com.zzh.oj.entity;

import lombok.Data;

import java.time.LocalDateTime;

/**
 * 测试用例：一条输入 + 一条期望输出
 */
@Data
public class TestCase {

    private Long id;

    private Long problemId;

    /** 喂给程序的标准输入 */
    private String inputData;

    /** 期望输出 */
    private String expectedOutput;

    /** 第几个用例 */
    private Integer ordinal;

    private LocalDateTime createdAt;
}
