# -*- coding: utf-8 -*-
"""
OJ 提交接口并发压测（零依赖，只用 Python 标准库）

用法
----
# 1) 启动服务时覆盖限流阈值，否则第 11 次开始全被 429 挡掉，测出来的是限流不是判题
#    java -jar target/oj-0.0.1-SNAPSHOT.jar --oj.rate-limit.submit.limit=1000000
#
# 2) 单轮
#    python bench_concurrency.py --concurrency 10 --requests 40
#
# 3) 多轮（找拐点）
#    python bench_concurrency.py --levels 1,5,10,20,50
#
# 4) 只测接口层吞吐（用编译错误的代码，几十毫秒返回）
#    python bench_concurrency.py --levels 10,50 --mode fast
"""

import argparse
import json
import statistics
import sys
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor

# ---------------- 两段测试代码 ----------------
# real：真正跑 3 个用例，端到端约 2s，用于测真实判题负载
CODE_REAL = """import java.util.Scanner;

public class Main {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int a = sc.nextInt();
        int b = sc.nextInt();
        System.out.println(a + b);
    }
}
"""

# fast：故意编译失败，只走「限流 -> 落库 -> 编译失败」短路径，几十毫秒
CODE_FAST = """public class Main {
    public static void main(String[] args) {
        this is not valid java
    }
}
"""


def one_request(url, problem_id, code, timeout):
    """发一次提交，返回 (耗时毫秒, 是否成功, 状态描述)"""
    body = json.dumps({"problemId": problem_id, "code": code}).encode("utf-8")
    req = urllib.request.Request(
        url, data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    start = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        elapsed = (time.perf_counter() - start) * 1000
        code_val = payload.get("code")
        # code == 0 视为受理成功；429 是限流；其它是判题结果（也算接口正常）
        ok = code_val == 0
        return elapsed, ok, "code=%s" % code_val
    except urllib.error.HTTPError as e:
        elapsed = (time.perf_counter() - start) * 1000
        return elapsed, False, "HTTP %s" % e.code
    except Exception as e:
        elapsed = (time.perf_counter() - start) * 1000
        return elapsed, False, type(e).__name__


def run_one_round(args, concurrency, total):
    """跑一轮：concurrency 个线程同时起跑，共发 total 个请求"""
    url = args.url
    code = CODE_FAST if args.mode == "fast" else CODE_REAL
    results = []
    lock = threading.Lock()
    barrier = threading.Barrier(concurrency)

    def worker(n):
        # 每个线程领 n 个请求，先对齐起跑线再发第一个，保证真并发
        local = []
        barrier.wait()
        for _ in range(n):
            local.append(one_request(url, args.problem_id, code, args.timeout))
        with lock:
            results.extend(local)

    per_thread = total // concurrency
    remainder = total % concurrency
    threads_num = concurrency

    wall_start = time.perf_counter()
    with ThreadPoolExecutor(max_workers=threads_num) as pool:
        futures = []
        for i in range(threads_num):
            n = per_thread + (1 if i < remainder else 0)
            if n > 0:
                futures.append(pool.submit(worker, n))
        for f in futures:
            f.result()
    wall = time.perf_counter() - wall_start

    elapsed_list = sorted(r[0] for r in results)
    ok_count = sum(1 for r in results if r[1])
    fail_count = len(results) - ok_count
    reason = {}
    for r in results:
        if not r[1]:
            reason[r[2]] = reason.get(r[2], 0) + 1

    def pct(p):
        if not elapsed_list:
            return 0.0
        k = min(len(elapsed_list) - 1, int(round((p / 100.0) * (len(elapsed_list) - 1))))
        return elapsed_list[k]

    return {
        "concurrency": concurrency,
        "total": len(results),
        "ok": ok_count,
        "fail": fail_count,
        "fail_reason": reason,
        "avg": statistics.mean(elapsed_list) if elapsed_list else 0,
        "p50": pct(50),
        "p95": pct(95),
        "p99": pct(99),
        "max": elapsed_list[-1] if elapsed_list else 0,
        "wall": wall,
        "qps": ok_count / wall if wall > 0 else 0,
    }


def fmt_row(r):
    return ("{:>4} | {:>4} | {:>4} | {:>4} | {:>8.0f} | {:>6.0f} | {:>6.0f} | {:>6.0f} | {:>8.2f} | {:>7.2f}"
            .format(r["concurrency"], r["total"], r["ok"], r["fail"],
                    r["avg"], r["p50"], r["p95"], r["p99"], r["wall"], r["qps"]))


HEADER = ("并发 | 请求 | 成功 | 失败 | 平均ms   | P50ms  | P95ms  | P99ms  | 总耗时s  | QPS")
LINE = "-" * 92


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://localhost:8080/api/submissions")
    ap.add_argument("--problem-id", type=int, default=1)
    ap.add_argument("--concurrency", type=int, default=10)
    ap.add_argument("--requests", type=int, default=0, help="默认 = 并发数 * 4")
    ap.add_argument("--levels", default="", help="多轮，如 1,5,10,20,50")
    ap.add_argument("--mode", choices=["real", "fast"], default="real")
    ap.add_argument("--timeout", type=int, default=120)
    ap.add_argument("--out", default="bench_concurrency_report.txt")
    args = ap.parse_args()

    if args.levels:
        levels = [int(x) for x in args.levels.split(",") if x.strip()]
    else:
        levels = [args.concurrency]

    lines = []
    stamp = time.strftime("%Y-%m-%d %H:%M:%S")
    head = "OJ 并发压测  %s   模式=%s   题目=%d   %s" % (stamp, args.mode, args.problem_id, args.url)
    print(head)
    print(LINE)
    print(HEADER)
    print(LINE)
    lines += [head, LINE, HEADER, LINE]

    for c in levels:
        total = args.requests if args.requests and not args.levels else c * 4
        r = run_one_round(args, c, total)
        row = fmt_row(r)
        print(row)
        lines.append(row)
        if r["fail_reason"]:
            detail = "         失败原因: " + ", ".join("%s x%d" % (k, v) for k, v in r["fail_reason"].items())
            print(detail)
            lines.append(detail)

    print(LINE)
    lines.append(LINE)
    note = ("说明：QPS = 成功请求数 / 实际耗时。real 模式单次约 2s（3 用例，瓶颈在 JVM 启动），"
            "fast 模式只测接口层。")
    print(note)
    lines.append(note)

    with open(args.out, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print("\n报告已写入: %s" % args.out)


if __name__ == "__main__":
    sys.exit(main())
