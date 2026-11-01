package com.zzh.oj.entity;

import lombok.Data;

/**
 * 提交详情：代码、判题输出、AI 点评
 * 大字段单独一张表，列表页查询不会把它们带出来
 */
@Data
public class SubmissionDetail {

    /** 与 submission.id 一对一 */
    private Long submissionId;

    /** 用户提交的源码 */
    private String code;

    /** 判题输出：编译错误、异常栈等 */
    private String output;

    /** AI 代码评审结果 */
    private String aiReview;
}
