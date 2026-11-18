"""异步判题冒烟测试：验证 PENDING -> 终态 的完整链路"""
import json
import time
import urllib.request

BASE = "http://127.0.0.1:8080"

CODE_OK = """
import java.util.Scanner;
public class Main {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int a = sc.nextInt(), b = sc.nextInt();
        System.out.println(a + b);
    }
}
"""

CODE_WA = """
import java.util.Scanner;
public class Main {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int a = sc.nextInt(), b = sc.nextInt();
        System.out.println(a * b);   // 故意写错
    }
}
"""

CODE_CE = """
public class Main {
    public static void main(String[] args) { int x = ; }
}
"""


def post(path, body):
    req = urllib.request.Request(
        BASE + path,
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
        method="POST")
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read().decode())


def get(path):
    with urllib.request.urlopen(BASE + path) as r:
        return json.loads(r.read().decode())


def run_case(name, code, expect):
    t0 = time.time()
    resp = post("/api/submissions", {"problemId": 1, "code": code})
    submit_ms = (time.time() - t0) * 1000
    assert resp["code"] == 0, resp
    sid = resp["data"]["submissionId"]
    immediate = resp["data"]["status"]

    # 轮询
    polls = 0
    while True:
        polls += 1
        d = get(f"/api/submissions/{sid}")["data"]
        if d["status"] != 6:
            break
        if (time.time() - t0) > 40:
            print(f"  {name}: 超时未完成")
            return
        time.sleep(0.15)

    total = time.time() - t0
    ok = "OK" if d["status"] == expect else f"FAIL(期望{expect} 实际{d['status']})"
    print(f"  {name:9s} POST {submit_ms:6.1f}ms -> 立即返回status={immediate}(判题中) "
          f"| 轮询{polls}次 {total:5.2f}s | 终态={d['status']}({d['statusText']}) "
          f"用例 {d.get('passedCases')}/{d.get('totalCases')} | {ok}")


print("=== 异步链路冒烟 ===")
run_case("AC 通过", CODE_OK, 1)
run_case("WA 错答", CODE_WA, 5)
run_case("CE 编译错", CODE_CE, 2)

print("\n=== 队列状态 ===")
print(" ", get("/api/judge/stats")["data"])
