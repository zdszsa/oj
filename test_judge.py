import json
import urllib.request

BASE = 'http://localhost:8081'


def post(path, payload):
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(BASE + path, data=data,
                                 headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode('utf-8'))


add_ok = '''import java.util.Scanner;
public class Main {
    public static void main(String[] a) {
        Scanner sc = new Scanner(System.in);
        int x = sc.nextInt(), y = sc.nextInt();
        System.out.println(x + y);
    }
}'''

add_wa = '''import java.util.Scanner;
public class Main {
    public static void main(String[] a) {
        Scanner sc = new Scanner(System.in);
        sc.nextInt(); sc.nextInt();
        System.out.println(0);
    }
}'''

ce = 'public class Main { public static void main(String[] a){ int x = ; } }'

tle = 'public class Main { public static void main(String[] a){ while(true){} } }'

re = 'public class Main { public static void main(String[] a){ int x = 1/0; } }'

cases = [
    ('OK       正确解', add_ok),
    ('WA       少个 1', add_wa),
    ('CE       语法错', ce),
    ('TLE      死循环', tle),
    ('RE       除零  ', re),
]

lines = []
for name, code in cases:
    try:
        r = post('/api/submissions', {'problemId': 1, 'code': code})
        lines.append('%-14s -> %s' % (name, json.dumps(r, ensure_ascii=False)))
    except Exception as e:
        lines.append('%-14s -> EXCEPTION %s' % (name, e))

with open(r'D:\IdeaProjects\oj\res.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))
print('done')
