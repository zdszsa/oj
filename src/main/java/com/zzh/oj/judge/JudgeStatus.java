package com.zzh.oj.judge;

/**
 * 判题状态
 *
 * 注意：code 是【写死的】，用来存数据库。
 * 千万不要用 ordinal()，因为一旦在枚举中间插入新值，历史数据的含义就全错位了。
 */
public enum JudgeStatus {

    OK(1, "通过"),
    COMPILE_ERROR(2, "编译错误"),
    RUNTIME_ERROR(3, "运行错误"),
    TIME_LIMIT_EXCEEDED(4, "超时"),
    WRONG_ANSWER(5, "答案错误"),
    PENDING(6, "判题中"),
    SYSTEM_ERROR(7, "系统错误");

    private final int code;
    private final String text;

    JudgeStatus(int code, String text) {
        this.code = code;
        this.text = text;
    }

    public int getCode() {
        return code;
    }

    public String getText() {
        return text;
    }

    public static JudgeStatus of(int code) {
        for (JudgeStatus s : values()) {
            if (s.code == code) {
                return s;
            }
        }
        throw new IllegalArgumentException("未知的判题状态: " + code);
    }
}
