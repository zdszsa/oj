# -*- coding: utf-8 -*-
"""
OJ 项目基准复现脚本（一键）
============================
跑完会在当前目录生成 bench_report.txt，包含简历里用到的全部实测数字：
  1. 成功路径端到端耗时（3 用例 / 4 用例）        -> 均摊 680ms/用例
  2. 失败即返回（首用例就错）                      -> 694ms vs 2732ms
  3. TLE 强杀                                      -> 2026ms 终止（时限 2000ms）
  4. AI 评审异步生效                               -> 主流程返回时为空，约 2s 后写入
  5. 提交限流                                      -> 前 10 次放行，第 11 次 429，拦截 6ms
  6. 联合索引效果（10 万行）                       -> 47ms 全表扫描 vs 8ms 索引查找

用法（在 D:\\IdeaProjects\\oj 目录下打开终端）：
    python bench_repro.py              # 自动启动服务 -> 全部测一遍 -> 关掉服务
    python bench_repro.py --keep       # 服务已经在跑，不启动也不关闭

前置条件：
    - MySQL 8.0 已启动（root / root）
    - Redis 可连（脚本会自己探测，连不上会提示，但不影响其它项）
"""
import json
import os
import re
import subprocess
import sys
import time
import urllib.request

# ------------------------------------------------------------------ 可改配置
PROJECT = r'D:\IdeaProjects\oj'
JAVA = r'D:\Dev\jdk-17.0.19.10-hotspot\bin\java.exe'
JAR = os.path.join(PROJECT, 'target', 'oj-0.0.1-SNAPSHOT.jar')
MYSQL = r'D:\MySQL\MySQL Server 8.0\bin\mysql.exe'
DB = 'oj'
DB_USER, DB_PASS = 'root', 'root'
PORT = 8080
BASE = 'http://localhost:%d' % PORT
# ---------------------------------------------------------------------------

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

OK1 = ('import java.util.Scanner; public class Main{public static void main(String[] a){'
       'Scanner s=new Scanner(System.in);int x=s.nextInt(),y=s.nextInt();System.out.println(x+y);}}')
OK2 = ('import java.util.Scanner; public class Main{public static void main(String[] a){'
       'Scanner s=new Scanner(System.in);int n=s.nextInt();String t=String.valueOf(n);boolean ok=true;'
       'for(int i=0,j=t.length()-1;i<j;i++,j--){if(t.charAt(i)!=t.charAt(j)){ok=false;break;}}'
       'System.out.println(ok);}}')
OK3 = ('import java.util.Scanner; public class Main{public static void main(String[] a){'
       'Scanner s=new Scanner(System.in);int n=s.nextInt();int[] r=new int[n];'
       'for(int i=0;i<n;i++)r[i]=s.nextInt();int t=s.nextInt();'
       'for(int i=0;i<n;i++)for(int j=i+1;j<n;j++)if(r[i]+r[j]==t){System.out.println(i+" "+j);return;}}}')
WA_FIRST = ('import java.util.Scanner; public class Main{public static void main(String[] a){'
            'Scanner s=new Scanner(System.in);s.nextInt();System.out.println(false);}}')
TLE = 'public class Main{public static void main(String[] a){while(true){}}}'
CE = 'public class Main{public static void main(String[] a){int x=;}}'

LINES = []


def say(msg=''):
    print(msg, flush=True)
    LINES.append(msg)


def mysql(sql, timeout=180):
    r = subprocess.run([MYSQL, '-u' + DB_USER, '-p' + DB_PASS,
                        '--default-character-set=utf8mb4', '-N', '-e', sql],
                       capture_output=True, text=True, encoding='utf-8', errors='replace',
                       timeout=timeout)
    out = [ln for ln in r.stdout.splitlines() if 'Warning' not in ln]
    return '\n'.join(out).strip()


def raw_post(pid, code):
    body = json.dumps({'problemId': pid, 'code': code}).encode('utf-8')
    req = urllib.request.Request(BASE + '/api/submissions', data=body,
                                 headers={'Content-Type': 'application/json'})
    t0 = time.perf_counter()
    with urllib.request.urlopen(req, timeout=120) as r:
        j = json.loads(r.read().decode('utf-8'))
    return (time.perf_counter() - t0) * 1000, j


def post(pid, code):
    """碰到限流（body.code == 429）就等 62 秒重试，最多 3 轮。"""
    for i in range(3):
        ms, j = raw_post(pid, code)
        if j.get('code') != 429:
            return ms, j
        say('    [限流窗口未过，等 62 秒后重试 %d/3]' % (i + 1))
        time.sleep(62)
    return ms, j


def wait_port(timeout=60):
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            with urllib.request.urlopen(BASE + '/api/problems', timeout=2):
                return True
        except Exception:
            time.sleep(1)
    return False


def check_env():
    say('=== 环境检查 ===')
    say('  jar      : %s  %s' % ('存在' if os.path.exists(JAR) else '缺失！',
                                time.strftime('%Y-%m-%d %H:%M', time.localtime(os.path.getmtime(JAR)))
                                if os.path.exists(JAR) else ''))
    try:
        say('  MySQL    : ' + (mysql('SELECT VERSION();') or '不可用'))
    except Exception as e:
        say('  MySQL    : 连接失败（%s）—— 后面索引那一项会跳过' % e)
    try:
        import socket
        s = socket.create_connection(('192.168.100.128', 6379), timeout=3)
        s.close()
        say('  Redis    : 192.168.100.128:6379 可达')
    except Exception:
        say('  Redis    : 不可达 —— 限流会走降级放行，该项结果无意义')


def start_server():
    key = ''
    cfg = os.path.join(PROJECT, 'src', 'main', 'resources', 'application-local.properties')
    if os.path.exists(cfg):
        for ln in open(cfg, encoding='utf-8', errors='replace'):
            if 'oj.ai.api-key' in ln:
                key = ln.split('=', 1)[1].strip()
                break
    cmd = [JAVA, '-jar', JAR, '--server.port=%d' % PORT]
    if key:
        cmd.append('--oj.ai.api-key=' + key)
    else:
        say('  ! 没读到 api-key，AI 评审那一项会失败')
    log = open(os.path.join(PROJECT, 'run_repro.log'), 'w', encoding='utf-8')
    p = subprocess.Popen(cmd, cwd=PROJECT, stdout=log, stderr=subprocess.STDOUT)
    say('  启动服务中（PID %d）...' % p.pid)
    if not wait_port():
        say('  ! 服务 60 秒内没起来，看 run_repro.log')
        p.kill()
        sys.exit(1)
    say('  服务就绪 %s' % BASE)
    return p


def phase_judge():
    say('\n=== 一、成功路径端到端耗时（每题 2 轮，取快的一次）===')
    post(1, OK1)  # 热身，丢弃
    stat = {}
    for pid, name, cases, code in ((1, 'A+B', 3, OK1), (2, '回文数', 4, OK2), (3, '两数之和', 3, OK3)):
        ts = []
        for _ in range(2):
            ms, j = post(pid, code)
            d = j.get('data') or {}
            ts.append((ms, d.get('statusText')))
            time.sleep(0.5)
        ts.sort()
        stat[pid] = ts[0][0]
        say('  题%d %-9s %d 用例   最快 %7.1f ms   状态=%s' % (pid, name, cases, ts[0][0], ts[0][1]))
    p1, p2 = stat[1] / 3, stat[2] / 4
    say('  -> 均摊：%.0f ms/用例（题1）、%.0f ms/用例（题2）—— 与算法复杂度无关，是进程开销'
        % (p1, p2))
    return stat


def phase_failfast(stat):
    say('\n=== 二、失败即返回（回文数 4 个用例，第一个用例就错）===')
    ms, j = post(2, WA_FIRST)
    d = j.get('data') or {}
    say('  首用例失败  端到端 %7.1f ms   状态=%s' % (ms, d.get('statusText')))
    say('  同题全通过  端到端 %7.1f ms' % stat[2])
    say('  -> 少跑 3 个用例，快 %.1f%%' % ((1 - ms / stat[2]) * 100))


def phase_tle():
    say('\n=== 三、TLE 强杀（死循环，题目时限 2000ms）===')
    ms, j = post(1, TLE)
    d = j.get('data') or {}
    say('  端到端 %7.1f ms   状态=%s   判题内部计时=%s ms' % (ms, d.get('statusText'), d.get('timeMs')))


def phase_ai():
    say('\n=== 四、AI 评审是否真的异步 ===')
    ms, j = post(1, OK1)
    d = j.get('data') or {}
    if not d:
        say('  ! 提交被拒：%s' % j.get('message'))
        return
    sid = d['submissionId']
    say('  提交返回：%.0f ms，submission_id=%s' % (ms, sid))

    def ai_len():
        t = mysql('USE %s; SELECT IFNULL(LENGTH(ai_review),0) FROM submission_detail '
                  'WHERE submission_id=%d;' % (DB, sid))
        return int(t) if t.isdigit() else -1

    say('  返回瞬间 ai_review = %d 字节' % ai_len())
    t0 = time.time()
    for _ in range(10):
        time.sleep(1)
        n = ai_len()
        if n > 0:
            say('  %.0f 秒后 ai_review = %d 字节  <-- 异步写入完成' % (time.time() - t0, n))
            return
    say('  10 秒内没等到 —— 看 run_repro.log 里的 AI 调用异常')


def phase_limit():
    say('\n=== 五、提交限流（阈值 10 次 / 60 秒）===')
    say('  先等 62 秒清空计数窗口...')
    time.sleep(62)
    for i in range(1, 13):
        ms, j = raw_post(1, CE)
        code = j.get('code')
        if code == 429:
            say('  第 %2d 次  code=429  %4.0f ms  %s' % (i, ms, j.get('message')))
        else:
            say('  第 %2d 次  code=%-4d  %4.0f ms  放行' % (i, code, ms))
        time.sleep(0.12)


def phase_index():
    say('\n=== 六、联合索引效果（10 万行）===')
    q = ('SELECT id, problem_id, language, status, time_ms, created_at FROM submission_bench '
         'WHERE user_id=1 ORDER BY created_at DESC LIMIT 10')
    try:
        mysql('USE %s; DROP TABLE IF EXISTS submission_bench;' % DB)
        mysql('''USE %s;
CREATE TABLE submission_bench (
  id BIGINT NOT NULL AUTO_INCREMENT,
  user_id BIGINT NOT NULL DEFAULT 1,
  problem_id BIGINT NOT NULL,
  language VARCHAR(20) NOT NULL DEFAULT 'java',
  status TINYINT NOT NULL,
  time_ms INT NOT NULL DEFAULT 0,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;''' % DB)
        say('  灌 10 万行...')
        mysql('''USE %s;
SET SESSION cte_max_recursion_depth = 200000;
INSERT INTO submission_bench (user_id, problem_id, status, time_ms, created_at)
WITH RECURSIVE seq AS (SELECT 1 AS n UNION ALL SELECT n+1 FROM seq WHERE n < 100000)
SELECT 1 + (n %% 10), 1 + (n %% 3), 1 + (n %% 5), n %% 2000, NOW() - INTERVAL n SECOND FROM seq;''' % DB)

        def explain(tag):
            """跑 3 次取中位数；行数取各节点里的最大值（即真正扫描的行数）。"""
            times, rows = [], 0
            for _ in range(3):
                out = mysql('USE %s; EXPLAIN ANALYZE %s;' % (DB, q))
                # 只认 "actual time=..x rows=n" 这一对，避免把优化器的估算行数也抓进来
                pairs = re.findall(r'actual time=[\d.]+\.\.([\d.]+) rows=(\d+)', out)
                if pairs:
                    times.append(float(pairs[0][0]))          # 第一个是顶层节点，即总耗时
                    rows = max(rows, max(int(p[1]) for p in pairs))
            if not times:
                say('  %s  执行计划解析失败' % tag)
                return None, None
            times.sort()
            med = times[len(times) // 2]
            say('  %s  %.1f ms   扫描 %s 行' % (tag, med, rows or '-'))
            return med, rows

        t1, r1 = explain('无索引')
        mysql('USE %s; ALTER TABLE submission_bench ADD KEY idx_user_time (user_id, created_at);' % DB)
        t2, r2 = explain('加索引')
        if t1 and t2:
            say('  -> 提速 %.1f 倍，扫描行数 %d -> %d' % (t1 / t2, r1, r2))
        mysql('USE %s; DROP TABLE IF EXISTS submission_bench;' % DB)
        say('  临时表已删除')
    except Exception as e:
        say('  跳过（%s）' % e)


def main():
    keep = '--keep' in sys.argv
    only = None
    if '--only' in sys.argv:
        i = sys.argv.index('--only')
        if i + 1 < len(sys.argv):
            only = sys.argv[i + 1].strip().lower()
    say('OJ 基准复现  %s' % time.strftime('%Y-%m-%d %H:%M:%S'))
    check_env()

    if only == 'index':                      # 这一项只查 MySQL，不用起服务
        phase_index()
        write_report()
        return

    proc = None
    if keep:
        if not wait_port(5):
            say('  ! --keep 模式下 %s 没有服务在跑' % BASE)
            sys.exit(1)
        say('  使用已在运行的服务')
    else:
        proc = start_server()
    try:
        if only in (None, 'judge', 'fail'):
            stat = phase_judge()
            if only in (None, 'fail'):
                phase_failfast(stat)
        if only in (None, 'tle'):
            phase_tle()
        if only in (None, 'ai'):
            phase_ai()
        if only in (None, 'limit'):
            phase_limit()
        if only is None:
            phase_index()
    finally:
        if proc is not None:
            say('\n关闭服务（PID %d）' % proc.pid)
            proc.terminate()
            try:
                proc.wait(timeout=10)
            except Exception:
                proc.kill()

    write_report()


def write_report():
    out = os.path.join(PROJECT, 'bench_report.txt')
    with open(out, 'w', encoding='utf-8') as f:
        f.write('\n'.join(LINES) + '\n')
    say('\n结果已写入 %s' % out)


if __name__ == '__main__':
    main()
