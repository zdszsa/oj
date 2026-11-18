# -*- coding: utf-8 -*-
import json
import urllib.request

URL = "http://localhost:8080/api/submissions"

CASES = [
    (30, "字符串压缩", """import java.util.*;
public class Main{
 public static void main(String[] a){
  Scanner sc=new Scanner(System.in);
  String s=sc.hasNextLine()?sc.nextLine():"";
  StringBuilder sb=new StringBuilder();
  int i=0;
  while(i<s.length()){
   int j=i;
   while(j<s.length()&&s.charAt(j)==s.charAt(i))j++;
   int c=j-i;
   sb.append(s.charAt(i));
   if(c>1)sb.append(c);
   i=j;
  }
  System.out.println(sb);
 }
}"""),
    (29, "约瑟夫环", """import java.util.*;
public class Main{
 public static void main(String[] a){
  Scanner sc=new Scanner(System.in);
  int n=sc.nextInt(),k=sc.nextInt();
  int r=0;
  for(int i=2;i<=n;i++) r=(r+k)%i;
  System.out.println(r+1);
 }
}"""),
    (25, "矩阵转置", """import java.util.*;
public class Main{
 public static void main(String[] a){
  Scanner sc=new Scanner(System.in);
  int m=sc.nextInt(),n=sc.nextInt();
  int[][] g=new int[m][n];
  for(int i=0;i<m;i++)for(int j=0;j<n;j++)g[i][j]=sc.nextInt();
  StringBuilder sb=new StringBuilder();
  for(int j=0;j<n;j++){
   for(int i=0;i<m;i++){ if(i>0)sb.append(' '); sb.append(g[i][j]); }
   if(j<n-1)sb.append('\\n');
  }
  System.out.println(sb);
 }
}"""),
    (26, "括号匹配", """import java.util.*;
public class Main{
 public static void main(String[] a){
  Scanner sc=new Scanner(System.in);
  String s=sc.hasNextLine()?sc.nextLine().trim():"";
  Deque<Character> st=new ArrayDeque<>();
  boolean ok=true;
  for(char c:s.toCharArray()){
   if(c=='('||c=='['||c=='{')st.push(c);
   else{
    if(st.isEmpty()){ok=false;break;}
    char t=st.pop();
    if((c==')'&&t!='(')||(c==']'&&t!='[')||(c=='}'&&t!='{')){ok=false;break;}
   }
  }
  if(!st.isEmpty())ok=false;
  System.out.println(ok);
 }
}"""),
    (12, "统计字符串长度", """import java.util.*;
public class Main{
 public static void main(String[] a){
  Scanner sc=new Scanner(System.in);
  String s=sc.hasNextLine()?sc.nextLine():"";
  System.out.println(s.length());
 }
}"""),
    (18, "各位数字之和", """import java.util.*;
public class Main{
 public static void main(String[] a){
  Scanner sc=new Scanner(System.in);
  long n=sc.nextLong();
  long s=0;
  while(n>0){s+=n%10;n/=10;}
  System.out.println(s);
 }
}"""),
]

STATUS = {1: "通过", 2: "编译错误", 3: "运行错误", 4: "超时", 5: "答案错误", 6: "判题中", 7: "系统错误"}
ok_all = True
for pid, name, code in CASES:
    body = json.dumps({"problemId": pid, "code": code}).encode()
    req = urllib.request.Request(URL, data=body, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=60) as r:
        d = json.loads(r.read().decode())
    data = d.get("data") or {}
    st = data.get("status")
    print("%-3d %-12s 状态=%-4s %s  耗时=%sms" % (pid, name, st, STATUS.get(st, "?"), data.get("timeMs")))
    if st != 1:
        ok_all = False
        print("     输出片段:", (data.get("output") or "")[:300])

print("\n结论:", "全部通过" if ok_all else "存在未通过，需检查题面或用例")
