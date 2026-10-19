# -*- coding: utf-8 -*-
"""Token 看板刷新器 v2：生成到临时文件，只有数据真的变了才覆盖正式文件，
避免页面无意义重载打断 LIVE 秒表。每 60 秒跑一次。Ctrl+C 停止。"""
import subprocess, time, os, re, shutil

PY = r"C:\Users\MR.SHI\.workbuddy\binaries\python\versions\3.13.12\python.exe"
GEN = r"C:\Users\MR.SHI\.workbuddy\skills\token-dashboard\scripts\gen_dashboard.py"
OUT = r"C:\Users\MR.SHI\WorkBuddy\2026-09-18-21-33-18\token-dashboard.html"
TMP = OUT + ".tmp"

def data_key(path):
    try:
        with open(path, encoding="utf-8") as fh:
            s = fh.read()
        m = re.search(r"const D=(\{.*?\});</script>", s, re.S)
        return m.group(1) if m else None
    except OSError:
        return None

i = 0
while True:
    i += 1
    try:
        r = subprocess.run([PY, GEN, "--out", TMP], capture_output=True, text=True, timeout=300)
        if r.returncode == 0:
            old_key = data_key(OUT)
            new_key = data_key(TMP)
            if new_key is not None and new_key != old_key:
                os.replace(TMP, OUT)
                print(f"[{time.strftime('%H:%M:%S')}] #{i} 数据有变化 -> 已更新看板", flush=True)
            else:
                os.remove(TMP)
                if i % 10 == 1:
                    print(f"[{time.strftime('%H:%M:%S')}] #{i} 数据无变化，跳过", flush=True)
        else:
            print(f"[{time.strftime('%H:%M:%S')}] #{i} gen failed rc={r.returncode}", flush=True)
    except Exception as e:
        print(f"[{time.strftime('%H:%M:%S')}] #{i} ERROR {e}", flush=True)
    time.sleep(60)
