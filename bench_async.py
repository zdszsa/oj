# -*- coding: utf-8 -*-
"""
OJ 异步架构压测（零依赖）

和 bench_concurrency.py 的区别：
改成异步后，POST 只做「限流 + 落库 + 入队」就返回，判题在后台跑。
所以这里测两件事，必须分开测，混在一起没有意义：

  1) 接口受理能力 —— POST 的 QPS / P99。这才是用户感知的响应时间。
  2) 判题吞吐 —— 系统每秒能判完多少题。这是硬上限，由 worker 数和单题耗时决定。

用法
----
# 启动（队列放大 + 放开限流，避免测出来的是限流行为）
java -jar target/oj-0.0.1-SNAPSHOT.jar --server.port=8080 \
     --oj.rate-limit.submit.limit=1000000 --oj.judge.queue-capacity=5000

# 接口受理能力
python bench_async.py --mode accept --levels 10,50,100,200 --per-thread 2

# 判题吞吐（发 N 题，等到全部判完，算每秒消化多少题）
python bench_async.py --mode throughput --requests 60
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

BASE = "http://127.0.0.1:8080"
SUBMIT = BASE + "/api/submissions"
STATS = BASE + "/api/judge/stats"

# 3 个用例、端到端约 2s 的真实判题代码
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

# 编译即失败，worker 约 0.45s 消化一个。
# 测接口受理能力时用它：接口侧耗时与代码内容无关，
# 但队列排空快 4 倍，能少等很多时间。
CODE_FAST = """public class Main {
    public static void main(String[] args) {
        this is not valid java
    }
}
"""

CODE = CODE_REAL


def post_submit(problem_id, code, timeout=120):
    """返回 (耗时ms, body中的code, submissionId)"""
    body = json.dumps({"problemId": problem_id, "code": code}).encode("utf-8")
    req = urllib.request.Request(SUBMIT, data=body,
                                 headers={"Content-Type": "application/json"},
                                 method="POST")
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        ms = (time.perf_counter() - t0) * 1000
        data = payload.get("data") or {}
        return ms, payload.get("code"), data.get("submissionId")
    except urllib.error.HTTPError as e:
        return (time.perf_counter() - t0) * 1000, e.code, None
    except Exception:
        return (time.perf_counter() - t0) * 1000, -1, None


def queue_size():
    try:
        with urllib.request.urlopen(STATS, timeout=5) as r:
            txt = json.loads(r.read().decode("utf-8")).get("data", "")
        for part in txt.split():
            if part.startswith("排队="):
                return int(part.split("=")[1])
    except Exception:
        pass
    return -1


def wait_drain(timeout=300):
    """等队列消化完，避免上一轮的任务干扰下一轮"""
    t0 = time.time()
    while time.time() - t0 < timeout:
        q = queue_size()
        if q <= 0:
            return True
        time.sleep(1)
    return False


def pct(sorted_list, p):
    if not sorted_list:
        return 0.0
    k = min(len(sorted_list) - 1, int(round((p / 100.0) * (len(sorted_list) - 1))))
    return sorted_list[k]


def one_round(concurrency, per_thread, problem_id):
    """concurrency 个线程，每个发 per_thread 个提交，统计 POST 响应时间"""
    results = []
    lock = threading.Lock()
    barrier = threading.Barrier(concurrency)

    def worker(n):
        local = []
        barrier.wait()
        for _ in range(n):
            local.append(post_submit(problem_id, CODE))
        with lock:
            results.extend(local)

    wall0 = time.perf_counter()
    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        futs = [pool.submit(worker, per_thread) for _ in range(concurrency)]
        for f in futs:
            f.result()
    wall = time.perf_counter() - wall0

    ms = sorted(r[0] for r in results)
    ok = sum(1 for r in results if r[1] == 0)
    rejected = sum(1 for r in results if r[1] == 503)
    other = len(results) - ok - rejected

    return {
        "c": concurrency, "total": len(results), "ok": ok, "rej": rejected, "other": other,
        "avg": statistics.mean(ms) if ms else 0,
        "p50": pct(ms, 50), "p95": pct(ms, 95), "p99": pct(ms, 99),
        "wall": wall, "qps": ok / wall if wall > 0 else 0,
    }


def fmt(r):
    return ("{:>4} | {:>5} | {:>5} | {:>5} | {:>9.1f} | {:>8.1f} | {:>8.1f} | {:>9.1f} | {:>8.2f} | {:>8.1f}"
            .format(r["c"], r["total"], r["ok"], r["rej"], r["avg"],
                    r["p50"], r["p95"], r["p99"], r["wall"], r["qps"]))


HEADER = "并发 | 请求  | 受理  | 拒绝  | 平均ms    | P50ms    | P95ms    | P99ms     | 总耗时s  | QPS"
LINE = "-" * 100


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["accept", "throughput"], default="accept")
    ap.add_argument("--levels", default="10,50,100,200")
    ap.add_argument("--per-thread", type=int, default=2, help="每线程请求数（accept 模式）")
    ap.add_argument("--requests", type=int, default=60, help="总请求数（throughput 模式）")
    ap.add_argument("--problem-id", type=int, default=1)
    ap.add_argument("--code", choices=["real", "fast"], default="real",
                    help="accept 模式建议用 fast，队列排空快；throughput 必须用 real")
    ap.add_argument("--out", default="")
    args = ap.parse_args()

    global CODE
    CODE = CODE_FAST if args.code == "fast" else CODE_REAL

    out_lines = []

    def emit(s):
        print(s)
        out_lines.append(s)

    if args.mode == "accept":
        emit("OJ 异步架构 · 提交接口受理能力  %s" % time.strftime("%Y-%m-%d %H:%M:%S"))
        emit("（响应时间 = 限流 + 落库 + 入队，不含判题；判题在后台 worker 中进行）")
        emit(LINE)
        emit(HEADER)
        emit(LINE)

        # 预热：第一次请求要建连、类加载，不预热会污染第一轮
        for _ in range(10):
            post_submit(args.problem_id, CODE)
        wait_drain()

        for c in [int(x) for x in args.levels.split(",") if x.strip()]:
            r = one_round(c, args.per_thread, args.problem_id)
            emit(fmt(r))
            wait_drain()

        emit(LINE)

    else:
        emit("OJ 异步架构 · 端到端判题吞吐  %s" % time.strftime("%Y-%m-%d %H:%M:%S"))
        emit("（提交 N 题后等待全部判完，用总耗时算每秒能判多少题）")
        emit(LINE)

        wait_drain()
        n = args.requests
        t0 = time.perf_counter()
        ids = []
        for _ in range(n):
            _, code, sid = post_submit(args.problem_id, CODE)
            if code == 0:
                ids.append(sid)
        submit_done = time.perf_counter() - t0
        emit("提交 %d 题，受理耗时 %.2fs（QPS %.1f）" % (len(ids), submit_done, len(ids) / submit_done))

        # 等全部判完
        done = 0
        while True:
            done = sum(1 for _ in [0]) if False else 0
            # 用队列长度代替逐条查询
            q = queue_size()
            if q == 0:
                break
            if time.perf_counter() - t0 > 600:
                emit("等待超时，队列仍有 %d 个任务" % q)
                break
            time.sleep(1)
        total = time.perf_counter() - t0
        emit("全部判完总耗时 %.1fs，判题吞吐 %.2f 题/秒" % (total, len(ids) / total))
        emit("队列状态: %s" % json.loads(urllib.request.urlopen(STATS).read().decode())["data"])

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write("\n".join(out_lines) + "\n")
        print("\n已写入 %s" % args.out)


if __name__ == "__main__":
    sys.exit(main())
