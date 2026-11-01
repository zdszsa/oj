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

    private LocalDateTime createdAt;
}
