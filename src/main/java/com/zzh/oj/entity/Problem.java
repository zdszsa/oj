package com.zzh.oj.entity;

import lombok.Data;

import java.time.LocalDateTime;

/**
 * 题目
 */
@Data
public class Problem {

    private Long id;

    private String title;

    /** 题面描述 */
    private String description;

    /** 难度：1 简单 / 2 中等 / 3 困难 */
    private Integer difficulty;

    /** 时间限制（毫秒） */
    private Integer timeLimitMs;

    /** 内存限制（MB） */
    private Integer memoryLimitMb;

    private LocalDateTime createdAt;

    private LocalDateTime updatedAt;
}
