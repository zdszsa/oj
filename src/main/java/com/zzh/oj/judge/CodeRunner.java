package com.zzh.oj.judge;

import java.io.OutputStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.concurrent.TimeUnit;

import static com.zzh.oj.judge.JudgeStatus.*;

public class CodeRunner {

    // 路径从 JudgeConfig 读，不写死 —— Windows 和 Linux 的路径、后缀都不一样
    private static String javac() {
        return JudgeConfig.javac();
    }

    private static String java() {
        return JudgeConfig.java();
    }

    /** 便捷版：没有输入、默认 2 秒 */
    public static RunResult run(String code) throws Exception {
        return run(code, null, 2000);
    }

    /**
     * 跑一次代码
     *
     * @param code         完整的 Java 源码（类名必须是 Main）
     * @param input        喂给程序的标准输入，可为 null
     * @param timeLimitMs  时间限制（毫秒）
     */
    public static RunResult run(String code, String input, int timeLimitMs) throws Exception {

        // 1. 建临时目录，把代码写成 Main.java
        Path dir = Files.createTempDirectory("oj-");
        Path src = dir.resolve("Main.java");
        Files.writeString(src, code, StandardCharsets.UTF_8);

        // 2. 编译：退出码非 0 就是编译错误
        //    ★ -J-Duser.language=en / -J-Duser.country=US：
        //      强制 javac 输出英文报错。中文 Windows 下它默认用 GBK 输出中文，
        //      我们用 UTF-8 解码就变成一串问号；部署到 Linux 后又是 UTF-8。
        //      编码不统一是最难查的一类问题，干脆统一成英文。
        Process p = new ProcessBuilder(javac(),
                "-J-Duser.language=en",
                "-J-Duser.country=US",
                "-encoding", "UTF-8",
                "Main.java")
                .directory(dir.toFile())
                .redirectErrorStream(true)
                .start();
        String compileOut = new String(p.getInputStream().readAllBytes(), StandardCharsets.UTF_8);
        if (p.waitFor() != 0) {
            return new RunResult(COMPILE_ERROR, compileOut, 0);
        }

        // 3. 运行
        long start = System.currentTimeMillis();
        Process p2 = new ProcessBuilder(java(), "Main")
                .directory(dir.toFile())
                .redirectErrorStream(true)
                .start();

        // 3.1 ★ 喂输入，然后【必须关闭】这个流
        //      close() 会给子进程发送 EOF，告诉它"输入到此为止"。
        //      不关的话，凡是读输入的程序（Scanner / BufferedReader）都会一直傻等，
        //      最后被判成超时 —— 这是最坑人的一个细节。
        try (OutputStream stdin = p2.getOutputStream()) {
            if (input != null && !input.isEmpty()) {
                stdin.write(input.getBytes(StandardCharsets.UTF_8));
                stdin.flush();
            }
        }

        // 3.2 等它结束，最多 timeLimitMs
        boolean finished = p2.waitFor(timeLimitMs, TimeUnit.MILLISECONDS);
        if (!finished) {
            p2.destroyForcibly();
            p2.waitFor();
            return new RunResult(TIME_LIMIT_EXCEEDED, "", System.currentTimeMillis() - start);
        }

        // 3.3 结束了：读输出、算耗时
        String output = new String(p2.getInputStream().readAllBytes(), StandardCharsets.UTF_8);
        long cost = System.currentTimeMillis() - start;

        if (p2.exitValue() != 0) {
            return new RunResult(RUNTIME_ERROR, output, cost);
        }
        return new RunResult(OK, output, cost);
    }

    public static void main(String[] args) throws Exception {

        String add = """
                import java.util.Scanner;
                public class Main {
                    public static void main(String[] a) {
                        Scanner sc = new Scanner(System.in);
                        int x = sc.nextInt(), y = sc.nextInt();
                        System.out.println(x + y);
                    }
                }
                """;

        System.out.println("[有输入] " + run(add, "1 2", 2000));
        System.out.println("[有输入] " + run(add, "-5 8", 2000));

        System.out.println("[不喂输入，Scanner 会等] " + run(add, null, 2000));

        System.out.println("[死循环] " + run("""
                public class Main {
                    public static void main(String[] a) { while (true) {} }
                }
                """, null, 1500));

        System.out.println("[编译错误] " + run("""
                public class Main {
                    public static void main(String[] a) { int x = ; }
                }
                """, null, 2000));
    }
}
