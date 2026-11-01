package com.zzh.oj.common;

import lombok.Getter;

/**
 * 业务异常：能被 GlobalExceptionHandler 捕获并转成 Result
 */
@Getter
public class BusinessException extends RuntimeException {

    private final int code;

    public BusinessException(int code, String message) {
        super(message);
        this.code = code;
    }

    public static BusinessException notFound(String what) {
        return new BusinessException(404, what + "不存在");
    }

    public static BusinessException badRequest(String message) {
        return new BusinessException(400, message);
    }
}
