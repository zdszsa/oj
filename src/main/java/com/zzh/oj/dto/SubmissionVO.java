package com.zzh.oj.dto;

import lombok.Data;

import java.time.LocalDateTime;

/**
 * 提交记录列表项（不含代码，列表页要轻）
 */
@Data
public class SubmissionVO {

    private Long id;

    private Long problemId;

    /** 连表查出来的题目标题，省得前端再请求一次 */
    private String problemTitle;

    private int status;

    private String statusText;

    private Integer timeMs;

    /** 通过用例数 / 总用例数，列表页也展示，让用户一眼看到差多远 */
    private Integer passedCases;

    private Integer totalCases;

    private LocalDateTime createdAt;
}
