#!/usr/bin/env python3
# 流式全量反汇编,找引用指定字符串槽位的代码地址。
import subprocess, re, json, sys, bisect

SO = "/Users/woods/bd2web/local_device_cache/apk_20260624/lib/arm64-v8a/libil2cpp.so"
OD = subprocess.run(["xcrun","-f","llvm-objdump"],capture_output=True,text=True).stdout.strip()
methmap = json.load(open("/tmp/methmap.json"))
meth_addrs = sorted(int(a) for a in methmap)
def owner(va):
    i = bisect.bisect_right(meth_addrs, va)-1
    a = meth_addrs[i] if i>=0 else 0
    return a, methmap.get(str(a),"?")

targets = set(int(x,16) for x in sys.argv[1:])
print("targets:", [hex(t) for t in targets], flush=True)

p = subprocess.Popen([OD,"-d","--no-show-raw-insn",SO],stdout=subprocess.PIPE,text=True)
adrp = {}
line_re = re.compile(r'\s*([0-9a-f]+):\s+(\w+)\s+(.*)')
hits=[]
for ln in p.stdout:
    m = line_re.match(ln)
    if not m: continue
    addr, op, args = m.group(1), m.group(2), m.group(3)
    if op=="adrp":
        mm=re.match(r'(x\d+),\s*0x([0-9a-f]+)',args)
        if mm: adrp[mm.group(1)]=int(mm.group(2),16)
    elif op in ("ldr","add","ldrb"):
        mm=re.match(r'\w+,\s*\[?(x\d+)(?:,\s*#(\d+))?',args)
        if mm and mm.group(1) in adrp:
            va=adrp[mm.group(1)]+int(mm.group(2) or 0)
            if va in targets:
                fa,fn=owner(int(addr,16))
                hits.append((addr,hex(va),hex(fa),fn))
                print(f"HIT code@0x{addr} -> slot {hex(va)}  func@{hex(fa)} {fn[:80]}", flush=True)
print(f"done, {len(hits)} hits", flush=True)
