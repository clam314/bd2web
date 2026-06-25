#!/usr/bin/env python3
# 用 ELF 重定位解析 il2cpp 字符串/方法引用,反汇编+注释一个函数。
import json, subprocess, sys, re, bisect

SO="/Users/woods/bd2web/local_device_cache/apk_20260624/lib/arm64-v8a/libil2cpp.so"
OD=subprocess.run(["xcrun","-f","llvm-objdump"],capture_output=True,text=True).stdout.strip()
strmap=json.load(open("/tmp/strmap.json"))      # {dec-addr: value}  (0xc6 string data)
methmap=json.load(open("/tmp/methmap.json"))    # {dec-addr: name}    (code addrs)
meth_addrs=sorted(int(a) for a in methmap)

# 重定位: slot_vaddr -> target_vaddr
reloc={}
for ln in open("/tmp/relocs.txt"):
    p=ln.split()
    if len(p)>=2 and "+0x" in p[1]:
        reloc[int(p[0],16)]=int(p[1].split("+0x")[1],16)

def classify(target):
    s=strmap.get(str(target))
    if s is not None: return f"STR {s!r}"
    n=methmap.get(str(target))
    if n is not None: return f"METHODPTR {n[:80]}"
    return None

def next_method(va):
    i=bisect.bisect_right(meth_addrs,va)
    return meth_addrs[i] if i<len(meth_addrs) else va+0x1000

def annotate(start_hex):
    start=int(start_hex,16); end=min(next_method(start),start+0x1600)
    out=subprocess.run([OD,"-d","--no-show-raw-insn",f"--start-address={hex(start)}",
                        f"--stop-address={hex(end)}",SO],capture_output=True,text=True).stdout
    adrp={}
    for ln in out.splitlines():
        m=re.match(r'\s*([0-9a-f]+):\s+(\w+)\s+(.*)',ln)
        if not m: continue
        addr,op,args=m.group(1),m.group(2),m.group(3).strip()
        note=""
        if op=="adrp":
            mm=re.match(r'(x\d+),\s*0x([0-9a-f]+)',args)
            if mm: adrp[mm.group(1)]=int(mm.group(2),16)
        elif op in ("ldr","add"):
            mm=re.match(r'x\d+,\s*\[?(x\d+)(?:,\s*#(\d+))?',args)
            if mm and mm.group(1) in adrp:
                slot=adrp[mm.group(1)]+int(mm.group(2) or 0)
                if slot in reloc:
                    c=classify(reloc[slot])
                    if c: note=f"   ; {c}"
                elif str(slot) in strmap:
                    note=f"   ; STRdirect {strmap[str(slot)]!r}"
        elif op in ("bl","b"):
            mm=re.match(r'0x([0-9a-f]+)',args)
            if mm:
                n=methmap.get(str(int(mm.group(1),16)))
                if n: note=f"   ; -> {n[:85]}"
        print(f"{addr}: {op:6} {args}{note}")

for a in sys.argv[1:]:
    print(f"\n===== FUNC {a} =====")
    annotate(a)
