# -*- coding: utf-8 -*-
"""
生成 OJ 扩充题库 SQL（27 道，id 4-30）
期望输出全部由参考解计算，避免手写用例出错。
输出：src/main/resources/db/data_extra_27.sql
"""
import math

OUT = "src/main/resources/db/data_extra_27.sql"


def lines(s):
    return s.replace("\r\n", "\n").rstrip("\n").split("\n")


def first_line(s):
    return s.rstrip("\n").split("\n")[0]


# ---------------- 参考解 ----------------
def s_max3(s):
    a, b, c = map(int, s.split())
    return str(max(a, b, c))


def s_sum_n(s):
    n = int(s.strip())
    return str(n * (n + 1) // 2)


def s_leap(s):
    y = int(s.strip())
    return "true" if (y % 4 == 0 and y % 100 != 0) or y % 400 == 0 else "false"


def s_grade(s):
    g = int(s.strip())
    if g >= 90:
        return "A"
    if g >= 80:
        return "B"
    if g >= 70:
        return "C"
    if g >= 60:
        return "D"
    return "F"


def _arr(s):
    it = lines(s)
    n = int(it[0])
    return n, list(map(int, it[1].split()[:n]))


def s_arr_sum(s):
    n, a = _arr(s)
    return str(sum(a))


def s_arr_max(s):
    n, a = _arr(s)
    return str(max(a))


def s_arr_rev(s):
    n, a = _arr(s)
    return " ".join(map(str, reversed(a)))


def s_ascii(s):
    return str(ord(s.strip()[0]))


def s_strlen(s):
    return str(len(first_line(s)))


def s_prime(s):
    n = int(s.strip())
    if n < 2:
        return "false"
    for i in range(2, int(n ** 0.5) + 1):
        if n % i == 0:
            return "false"
    return "true"


def s_gcd(s):
    a, b = map(int, s.split())
    return str(math.gcd(a, b))


def s_lcm(s):
    a, b = map(int, s.split())
    return str(a * b // math.gcd(a, b))


def s_fact(s):
    n = int(s.strip())
    r = 1
    for i in range(2, n + 1):
        r *= i
    return str(r)


def s_fib(s):
    n = int(s.strip())
    if n == 1:
        return "1"
    a, b = 1, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return str(b)


def s_digit_sum(s):
    return str(sum(int(c) for c in s.strip()))


def s_bin(s):
    n = int(s.strip())
    return "0" if n == 0 else bin(n)[2:]


def s_reverse(s):
    return first_line(s)[::-1]


def s_vowel(s):
    line = first_line(s).lower()
    return str(sum(1 for c in line if c in "aeiou"))


def s_dedup(s):
    n, a = _arr(s)
    return " ".join(map(str, sorted(set(a))))


def s_bsearch(s):
    it = lines(s)
    n = int(it[0])
    a = list(map(int, it[1].split()[:n]))
    t = int(it[2])
    try:
        return str(a.index(t))
    except ValueError:
        return "-1"


def s_sort(s):
    n, a = _arr(s)
    return " ".join(map(str, sorted(a)))


def s_transpose(s):
    it = lines(s)
    m, n = map(int, it[0].split())
    mat = [list(map(int, it[1 + i].split()[:n])) for i in range(m)]
    out = []
    for j in range(n):
        out.append(" ".join(str(mat[i][j]) for i in range(m)))
    return "\n".join(out)


def s_bracket(s):
    line = s.strip()
    st = []
    pairs = {")": "(", "]": "[", "}": "{"}
    for c in line:
        if c in "([{":
            st.append(c)
        elif c in pairs:
            if not st or st[-1] != pairs[c]:
                return "false"
            st.pop()
        else:
            return "false"
    return "true" if not st else "false"


def s_max_sub(s):
    n, a = _arr(s)
    best = cur = a[0]
    for x in a[1:]:
        cur = max(x, cur + x)
        best = max(best, cur)
    return str(best)


def s_lis_cont(s):
    n, a = _arr(s)
    best = cur = 1
    for i in range(1, n):
        cur = cur + 1 if a[i] > a[i - 1] else 1
        best = max(best, cur)
    return str(best)


def s_josephus(s):
    n, k = map(int, s.split())
    r = 0
    for i in range(2, n + 1):
        r = (r + k) % i
    return str(r + 1)


def s_compress(s):
    line = first_line(s)
    out, i = [], 0
    while i < len(line):
        j = i
        while j < len(line) and line[j] == line[i]:
            j += 1
        cnt = j - i
        out.append(line[i] + (str(cnt) if cnt > 1 else ""))
        i = j
    return "".join(out)


# ---------------- 题目定义 ----------------
P = [
    (4, "三个数的最大值", 1,
     "输入一行三个整数 a、b、c（用空格分隔），输出其中的最大值。\n\n输入格式：一行，三个整数，范围 -10^9 ~ 10^9。\n输出格式：一个整数，即最大值。\n\n输入示例：3 7 5\n输出示例：7",
     s_max3, ["3 7 5", "-1 -5 -3", "100 100 99"]),

    (5, "1 到 N 求和", 1,
     "输入一个正整数 N，输出 1 + 2 + ... + N 的结果。\n\n输入格式：一行，一个整数 N（1 ≤ N ≤ 10000）。\n输出格式：一个整数。\n\n输入示例：10\n输出示例：55",
     s_sum_n, ["10", "1", "100"]),

    (6, "判断闰年", 1,
     "输入一个年份，判断是否为闰年。闰年的规则：能被 4 整除但不能被 100 整除，或者能被 400 整除。\n\n输入格式：一行，一个整数年份（1 ≤ year ≤ 9999）。\n输出格式：是闰年输出 true，否则输出 false。\n\n输入示例：2024\n输出示例：true",
     s_leap, ["2024", "1900", "2000"]),

    (7, "成绩等级", 1,
     "输入一个百分制成绩，按区间输出等级：90-100 为 A，80-89 为 B，70-79 为 C，60-69 为 D，60 以下为 F。\n\n输入格式：一行，一个整数（0 ≤ score ≤ 100）。\n输出格式：一个大写字母。\n\n输入示例：95\n输出示例：A",
     s_grade, ["95", "80", "59"]),

    (8, "数组求和", 1,
     "第一行输入数组长度 n，第二行输入 n 个整数，输出所有元素之和。\n\n输入格式：第一行一个整数 n（1 ≤ n ≤ 1000）；第二行 n 个整数，用空格分隔。\n输出格式：一个整数。\n\n输入示例：\n5\n1 2 3 4 5\n输出示例：15",
     s_arr_sum, ["5\n1 2 3 4 5", "3\n-1 -2 -3", "1\n100"]),

    (9, "数组最大值", 1,
     "第一行输入数组长度 n，第二行输入 n 个整数，输出其中的最大值。\n\n输入格式：第一行一个整数 n（1 ≤ n ≤ 1000）；第二行 n 个整数。\n输出格式：一个整数。\n\n输入示例：\n5\n3 9 2 7 5\n输出示例：9",
     s_arr_max, ["5\n3 9 2 7 5", "4\n-5 -2 -9 -1", "1\n42"]),

    (10, "数组逆序输出", 1,
     "第一行输入数组长度 n，第二行输入 n 个整数，按相反顺序输出。\n\n输入格式：第一行一个整数 n（1 ≤ n ≤ 1000）；第二行 n 个整数。\n输出格式：一行，逆序后的 n 个整数，用单个空格分隔。\n\n输入示例：\n5\n1 2 3 4 5\n输出示例：5 4 3 2 1",
     s_arr_rev, ["5\n1 2 3 4 5", "3\n7 8 9", "1\n5"]),

    (11, "字符转 ASCII", 1,
     "输入一个可见 ASCII 字符，输出它的 ASCII 码。\n\n输入格式：一行，一个字符。\n输出格式：一个整数。\n\n输入示例：A\n输出示例：65",
     s_ascii, ["A", "a", "0"]),

    (12, "统计字符串长度", 1,
     "输入一行字符串（可能包含空格），输出它的字符个数。\n\n输入格式：一行字符串，长度不超过 100。\n输出格式：一个整数。\n\n输入示例：hello\n输出示例：5",
     s_strlen, ["hello", "abc def", "Java"]),

    (13, "判断素数", 2,
     "输入一个整数 n，判断它是否为素数。素数是大于 1 且只能被 1 和自身整除的整数。\n\n输入格式：一行，一个整数 n（2 ≤ n ≤ 100000）。\n输出格式：是素数输出 true，否则输出 false。\n\n输入示例：17\n输出示例：true",
     s_prime, ["17", "18", "2"]),

    (14, "最大公约数", 2,
     "输入两个正整数，输出它们的最大公约数。\n\n输入格式：一行，两个整数 a、b（1 ≤ a, b ≤ 10^9）。\n输出格式：一个整数。\n\n输入示例：12 18\n输出示例：6",
     s_gcd, ["12 18", "7 13", "100 75"]),

    (15, "最小公倍数", 2,
     "输入两个正整数，输出它们的最小公倍数。\n\n输入格式：一行，两个整数 a、b（1 ≤ a, b ≤ 10000）。\n输出格式：一个整数。\n\n输入示例：4 6\n输出示例：12",
     s_lcm, ["4 6", "7 13", "100 75"]),

    (16, "阶乘", 2,
     "输入一个非负整数 n，输出 n 的阶乘（n! = 1 × 2 × ... × n，规定 0! = 1）。\n\n输入格式：一行，一个整数 n（0 ≤ n ≤ 20）。\n输出格式：一个整数。\n\n输入示例：5\n输出示例：120",
     s_fact, ["5", "0", "20"]),

    (17, "斐波那契数列", 2,
     "斐波那契数列定义为 F(1)=1，F(2)=1，F(n)=F(n-1)+F(n-2)。输入 n，输出第 n 项。\n\n输入格式：一行，一个整数 n（1 ≤ n ≤ 50）。\n输出格式：一个整数。\n\n输入示例：10\n输出示例：55",
     s_fib, ["1", "10", "50"]),

    (18, "各位数字之和", 2,
     "输入一个非负整数，输出它各位数字之和。\n\n输入格式：一行，一个非负整数 n（0 ≤ n ≤ 10^18）。\n输出格式：一个整数。\n\n输入示例：12345\n输出示例：15",
     s_digit_sum, ["12345", "0", "9999999999"]),

    (19, "十进制转二进制", 2,
     "输入一个非负整数，输出它的二进制表示（不含前导零，0 输出 0）。\n\n输入格式：一行，一个整数 n（0 ≤ n ≤ 10^9）。\n输出格式：一个由 0 和 1 组成的字符串。\n\n输入示例：10\n输出示例：1010",
     s_bin, ["10", "0", "255"]),

    (20, "字符串反转", 2,
     "输入一行字符串（不含空格），输出反转后的字符串。\n\n输入格式：一行字符串，长度不超过 1000。\n输出格式：反转后的字符串。\n\n输入示例：hello\n输出示例：olleh",
     s_reverse, ["hello", "abc", "a"]),

    (21, "统计元音字母", 2,
     "输入一行字符串，统计其中元音字母（a、e、i、o、u）的个数，不区分大小写。\n\n输入格式：一行字符串，可能包含空格。\n输出格式：一个整数。\n\n输入示例：hello\n输出示例：2",
     s_vowel, ["hello", "AEIOU", "xyz"]),

    (22, "数组去重并排序", 2,
     "第一行输入数组长度 n，第二行输入 n 个整数，输出去重后按升序排列的结果。\n\n输入格式：第一行一个整数 n（1 ≤ n ≤ 1000）；第二行 n 个整数。\n输出格式：一行，去重升序后的整数，用单个空格分隔。\n\n输入示例：\n6\n3 1 2 3 1 4\n输出示例：1 2 3 4",
     s_dedup, ["6\n3 1 2 3 1 4", "3\n5 5 5", "5\n9 8 7 6 5"]),

    (23, "二分查找", 2,
     "第一行输入数组长度 n，第二行输入 n 个严格升序排列的整数，第三行输入目标值 target。若 target 存在，输出它的下标（从 0 开始）；否则输出 -1。\n\n输入格式：第一行 n（1 ≤ n ≤ 10000）；第二行 n 个升序整数；第三行一个整数 target。\n输出格式：一个整数。\n\n输入示例：\n5\n1 3 5 7 9\n5\n输出示例：2",
     s_bsearch, ["5\n1 3 5 7 9\n5", "5\n1 3 5 7 9\n4", "1\n10\n10"]),

    (24, "冒泡排序", 2,
     "第一行输入数组长度 n，第二行输入 n 个整数，按升序输出排序结果。\n\n输入格式：第一行一个整数 n（1 ≤ n ≤ 1000）；第二行 n 个整数。\n输出格式：一行，升序排列的 n 个整数，用单个空格分隔。\n\n输入示例：\n5\n5 3 8 1 2\n输出示例：1 2 3 5 8",
     s_sort, ["5\n5 3 8 1 2", "3\n9 9 1", "1\n7"]),

    (25, "矩阵转置", 2,
     "第一行输入矩阵的行数 m 和列数 n，接下来 m 行每行 n 个整数，输出该矩阵的转置。\n\n输入格式：第一行两个整数 m、n（1 ≤ m, n ≤ 100）；接下来 m 行，每行 n 个整数。\n输出格式：共 n 行，每行 m 个整数，用单个空格分隔。\n\n输入示例：\n2 3\n1 2 3\n4 5 6\n输出示例：\n1 4\n2 5\n3 6",
     s_transpose, ["2 3\n1 2 3\n4 5 6", "3 1\n1\n2\n3", "1 1\n5"]),

    (26, "括号匹配", 3,
     "输入一个只包含 ()、[]、{} 三种括号的字符串，判断括号是否正确匹配。\n\n输入格式：一行字符串，长度不超过 10000。\n输出格式：匹配输出 true，否则输出 false。\n\n输入示例：{[()]}\n输出示例：true",
     s_bracket, ["()[]{}", "(]", "{[()]}", "("]),

    (27, "最大子段和", 3,
     "第一行输入数组长度 n，第二行输入 n 个整数（可能为负），求连续子数组的最大和（子数组至少包含一个元素）。\n\n输入格式：第一行一个整数 n（1 ≤ n ≤ 100000）；第二行 n 个整数。\n输出格式：一个整数。\n\n输入示例：\n5\n-2 1 -3 4 -1\n输出示例：4",
     s_max_sub, ["5\n-2 1 -3 4 -1", "3\n-5 -2 -9", "6\n1 2 3 4 5 6"]),

    (28, "最长连续递增子序列", 3,
     "第一行输入数组长度 n，第二行输入 n 个整数，求最长的严格递增连续子数组的长度。\n\n输入格式：第一行一个整数 n（1 ≤ n ≤ 100000）；第二行 n 个整数。\n输出格式：一个整数。\n\n输入示例：\n6\n1 3 5 2 4 6\n输出示例：3",
     s_lis_cont, ["6\n1 3 5 2 4 6", "5\n5 4 3 2 1", "4\n1 2 3 4"]),

    (29, "约瑟夫环", 3,
     "n 个人围成一圈，编号 1 到 n，从 1 号开始报数，报到 k 的人出圈，下一个人重新从 1 开始报数，求最后剩下的人的编号。\n\n输入格式：一行，两个整数 n、k（1 ≤ n ≤ 100000，1 ≤ k ≤ 1000）。\n输出格式：一个整数，即最后剩下的人的编号。\n\n输入示例：5 2\n输出示例：3",
     s_josephus, ["5 2", "10 3", "1 1"]),

    (30, "字符串压缩", 3,
     "输入一行只含小写字母的字符串，把连续相同的字符压缩为「字符 + 次数」，次数为 1 时只输出字符、不输出数字。\n\n输入格式：一行字符串，长度不超过 10000。\n输出格式：压缩后的字符串。\n\n输入示例：aaabbc\n输出示例：a3b2c",
     s_compress, ["aaabbc", "abc", "aaaa"]),
]


def esc(t):
    return t.replace("\\", "\\\\").replace("\n", "\\n").replace("'", "''")


def main():
    p_sql = []
    t_sql = []
    for pid, title, diff, desc, fn, tests in P:
        p_sql.append("(%d, '%s', '%s', %d, 2000, 256)" % (pid, esc(title), esc(desc), diff))
        for idx, inp in enumerate(tests, 1):
            out = fn(inp)
            t_sql.append("(%d, '%s', '%s', %d)" % (pid, esc(inp), esc(out), idx))

    with open(OUT, "w", encoding="utf-8") as f:
        f.write("-- ============================================================\n")
        f.write("--  OJ 扩充题库：27 道题（id 4-30），共 %d 个测试用例\n" % len(t_sql))
        f.write("--  在 data.sql 之后执行；期望输出由参考解生成\n")
        f.write("-- ============================================================\n\n")
        f.write("USE oj;\n\n")
        f.write("INSERT INTO problem (id, title, description, difficulty, time_limit_ms, memory_limit_mb) VALUES\n")
        f.write(",\n".join(p_sql) + ";\n\n")
        f.write("INSERT INTO test_case (problem_id, input_data, expected_output, ordinal) VALUES\n")
        f.write(",\n".join(t_sql) + ";\n")

    print("已生成 %s" % OUT)
    print("题目 %d 道，用例 %d 个" % (len(P), len(t_sql)))
    from collections import Counter
    c = Counter(x[2] for x in P)
    print("难度分布：简单 %d / 中等 %d / 困难 %d" % (c[1], c[2], c[3]))


if __name__ == "__main__":
    main()
