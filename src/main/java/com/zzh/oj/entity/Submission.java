package com.zzh.oj.entity;

import lombok.Data;

import java.time.LocalDateTime;

/**
 * 提交记录（列表页用，不含代码）
 */
@Data
public class Submission {

    private Long id;

    private Long userId;

    private Long problemId;

    private String language;

    /**
     * 判题状态，与 JudgeStatus 的 code 一一对应：
     * 1 OK / 2 COMPILE_ERROR / 3 RUNTIME_ERROR / 4 TIME_LIMIT_EXCEEDED
     * 5 WRONG_ANSWER / 6 PENDING / 7 SYSTEM_ERROR
     */
    private Integer status;

    /** 耗时（毫秒） */
    private Integer timeMs;

    private LocalDateTime createdAt;
}
