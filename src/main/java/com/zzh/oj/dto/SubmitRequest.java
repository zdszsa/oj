package com.zzh.oj.dto;

import lombok.Data;

@Data
public class SubmitRequest {

    private Long problemId;

    /** 完整的 Java 源码，类名必须是 Main */
    private String code;
}
