import json
import urllib.error
import urllib.request

BASE = 'http://localhost:8081'

CODE = ('import java.util.Scanner; public class Main { '
        'public static void main(String[] a) { '
        'Scanner sc = new Scanner(System.in); '
        'System.out.println(sc.nextInt() + sc.nextInt()); } }')

lines = []
for i in range(1, 13):
    payload = json.dumps({'problemId': 1, 'code': CODE}).encode('utf-8')
    req = urllib.request.Request(BASE + '/api/submissions', data=payload,
                                 headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            j = json.loads(r.read().decode('utf-8'))
            data = j.get('data') or {}
            lines.append('%2d  HTTP %s  code=%s  %s / %s' % (
                i, r.status, j.get('code'),
                data.get('statusText', ''), j.get('message', '')))
    except urllib.error.HTTPError as e:
        lines.append('%2d  HTTP %s  %s' % (i, e.code, e.read().decode('utf-8', 'replace')[:80]))
    except Exception as e:
        lines.append('%2d  ERR %s' % (i, e))

with open(r'D:\IdeaProjects\oj\limit.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))
print('done')
