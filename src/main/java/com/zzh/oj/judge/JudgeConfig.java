package com.zzh.oj.judge;

import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

/**
 * 判题要用的字节码工具路径。
 *
 * 为什么不能写死在 CodeRunner 里：
 * Windows 上是 D:\Dev\jdk-17\bin\javac.exe，Linux 上是 /usr/local/jdk-17/bin/javac，
 * 连后缀都不一样。写死之后在本机能跑，一部署到服务器就找不到命令。
 *
 * 所以做成配置项，CodeRunner 用静态方法读这里。
 */
@Slf4j
@Component
public class JudgeConfig {

    private static String javacPath;
    private static String javaPath;

    @Value("${oj.judge.javac:javac}")
    public void setJavacPath(String v) {
        javacPath = v;
    }

    @Value("${oj.judge.java:java}")
    public void setJavaPath(String v) {
        javaPath = v;
    }

    public static String javac() {
        if (javacPath == null) {
            log.warn("oj.judge.javac 未配置，回退到 PATH 里的 javac");
            return "javac";
        }
        return javacPath;
    }

    public static String java() {
        if (javaPath == null) {
            log.warn("oj.judge.java 未配置，回退到 PATH 里的 java");
            return "java";
        }
        return javaPath;
    }
}
