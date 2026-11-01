package com.zzh.oj.dto;

import lombok.Builder;
import lombok.Data;

@Data
@Builder
public class SubmitResponse {

    private Long submissionId;

    /** 状态码，见 JudgeStatus */
    private int status;

    /** 状态中文名，前端直接显示 */
    private String statusText;

    /** 用时（毫秒） */
    private long timeMs;

    /** 编译错误、异常栈、或"第几组用例挂了" */
    private String output;

    private int passedCases;
    private int totalCases;
}
