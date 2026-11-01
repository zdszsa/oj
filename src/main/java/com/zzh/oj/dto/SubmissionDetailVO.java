package com.zzh.oj.dto;

import lombok.Data;

import java.time.LocalDateTime;

/**
 * 提交详情：记录信息 + 代码 + 判题输出
 */
@Data
public class SubmissionDetailVO {

    private Long id;

    private Long problemId;

    private String problemTitle;

    private int status;

    private String statusText;

    private Integer timeMs;

    private LocalDateTime createdAt;

    /** 用户提交的源码 */
    private String code;

    /** 编译错误 / 异常栈 / WA 提示 */
    private String output;

    /** AI 代码点评（异步生成，可能晚于判题结果） */
    private String aiReview;
}
