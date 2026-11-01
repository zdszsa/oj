package com.zzh.oj.common;

import lombok.Data;

/**
 * 统一响应体
 * code = 0 表示成功，非 0 表示失败（沿用 HTTP 语义：400 参数错、404 找不到、500 服务端错）
 */
@Data
public class Result<T> {

    private int code;
    private String message;
    private T data;

    private Result(int code, String message, T data) {
        this.code = code;
        this.message = message;
        this.data = data;
    }

    public static <T> Result<T> ok(T data) {
        return new Result<>(0, "ok", data);
    }

    public static <T> Result<T> fail(int code, String message) {
        return new Result<>(code, message, null);
    }
}
