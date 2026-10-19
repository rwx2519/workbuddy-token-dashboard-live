# -*- coding: utf-8 -*-
"""Token 实时监视器（秒表版）：
增量尾巴扫描 ~/.workbuddy/projects/**/*.jsonl，每 1 秒输出 live.json：
{ts, tot, today, reqs, todayReqs, lastTs, lastModel, lastTok, recent:[...]}
页面顶部秒表条每 1s 拉取刷新。Ctrl+C 停止。"""
import json, os, time, datetime, threading

PROJ = os.path.expanduser(r"~\.workbuddy\projects")
OUT = r"C:\Users\MR.SHI\WorkBuddy\2026-09-18-21-33-18\live.json"
STATE = r"C:\Users\MR.SHI\WorkBuddy\2026-09-18-21-33-18\live_state.json"
INTERVAL = 1.0

lock = threading.Lock()
S = dict(tot=0, today=0, reqs=0, todayReqs=0, lastTs=0, lastModel="", lastTok=0)
recent = []          # 最近 8 条 [epoch, model, tok]
pulses = []          # 近 35 分钟心跳事件 [ts, model, tok]（供脉冲心电图）
buckets = {}         # epoch_minute -> tokens（仅保留近 120 分钟，供 sparkline/速率）
offsets = {}         # path -> [offset, partial_remainder]
today_str = datetime.date.today().isoformat()

def parse_ts(v):
    if isinstance(v, (int, float)):
        if v > 1e12: return v / 1000.0
        if v > 1e9: return float(v)
    if isinstance(v, str):
        s = v.strip()
        for fmt_ in ('%Y-%m-%dT%H:%M:%S.%fZ', '%Y-%m-%dT%H:%M:%SZ',
                     '%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S.%f'):
            try:
                import calendar
                return calendar.timegm(datetime.datetime.strptime(s, fmt_).timetuple())
            except Exception:
                pass
        try: return float(s) / 1000.0
        except Exception: return None
    return None

def grab(o):
    pd = o.get('providerData')
    if not isinstance(pd, dict): return None
    ru = pd.get('rawUsage') or {}; u = pd.get('usage') or {}
    tt = ru.get('total_tokens') or u.get('totalTokens')
    if not tt: return None
    model = pd.get('model') or pd.get('requestModelId') or pd.get('requestModelName') or 'unknown'
    return int(tt), model

def feed(o):
    """线程安全地累计一条记录"""
    global today_str
    g = grab(o)
    if not g: return
    tt, model = g
    ts = parse_ts(o.get('timestamp')) or 0
    with lock:
        d = datetime.date.today().isoformat()
        if d != today_str:  # 跨天：今日计数清零
            today_str = d; S['today'] = 0; S['todayReqs'] = 0
        S['tot'] += tt; S['reqs'] += 1
        if ts and datetime.datetime.fromtimestamp(ts).date().isoformat() == today_str:
            S['today'] += tt; S['todayReqs'] += 1
        if ts >= S['lastTs']:
            S['lastTs'] = ts; S['lastModel'] = model; S['lastTok'] = tt
        recent.append([round(ts), model, tt])
        del recent[:-8]
        if ts:
            m = int(ts // 60) * 60
            buckets[m] = buckets.get(m, 0) + tt
            pulses.append([int(ts), model, tt])

def process_chunk(path, chunk, is_tail):
    if path in offsets and offsets[path][1]:
        chunk = offsets[path][1] + chunk
    lines = chunk.split(b'\n')
    if is_tail:
        offsets[path][1] = lines.pop()      # 半行留到下次
    else:
        offsets[path][1] = b''
    for ln in lines:
        ln = ln.strip()
        if not ln: continue
        try: o = json.loads(ln.decode('utf-8', 'ignore'))
        except Exception: continue
        feed(o)

def full_scan():
    n = 0
    for root, _, files in os.walk(PROJ):
        for f in files:
            if not f.endswith('.jsonl'): continue
            p = os.path.join(root, f)
            try: sz = os.path.getsize(p)
            except OSError: continue
            offsets[p] = [sz, b'']
            try:
                with open(p, 'rb') as fh:
                    process_chunk(p, fh.read(), is_tail=False)
                n += 1
            except OSError:
                pass
    return n

def save_state():
    try:
        with lock:
            bk = {str(k): v for k, v in buckets.items()}
        with open(STATE, 'w', encoding='utf-8') as fh:
            json.dump({"offsets": {p: v[0] for p, v in offsets.items()}, "buckets": bk}, fh)
    except Exception: pass

def load_state():
    """用上次断点续扫：只补读增量，起点不为零"""
    try:
        with open(STATE, encoding='utf-8') as fh:
            saved = json.load(fh)
        offs = saved.get("offsets", saved)   # 兼容旧格式
        for k, v in saved.get("buckets", {}).items():
            try: buckets[int(k)] = int(v)
            except Exception: pass
    except Exception: return False
    n = 0
    for p, off in offs.items():
        try: sz = os.path.getsize(p)
        except OSError: continue
        if off >= sz: 
            offsets[p] = [sz, b'']; continue
        offsets[p] = [sz, b'']
        try:
            with open(p, 'rb') as fh:
                fh.seek(off)
                process_chunk(p, fh.read(), is_tail=False)
            n += 1
        except OSError: pass
    return True

def write_live():
    with lock:
        now_m = int(time.time() // 60) * 60
        for m in [m for m in buckets if m < now_m - 120 * 60]:
            del buckets[m]                       # 只留近 120 分钟
        spark = [buckets.get(now_m - i * 60, 0) for i in range(59, -1, -1)]
        rate5 = sum(buckets.get(now_m - i * 60, 0) for i in range(5)) / 5.0
        cut = time.time() - 2100
        while pulses and pulses[0][0] < cut:
            del pulses[0]
        data = dict(ts=time.time(), **S, recent=recent[-8:], spark=spark,
                    rate5=round(rate5), pulses=pulses[-300:])
    tmp = OUT + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as fh:
        json.dump(data, fh, ensure_ascii=False)
    for _ in range(6):                      # Windows: 目标被读占用时重试
        try:
            os.replace(tmp, OUT)
            return
        except PermissionError:
            time.sleep(0.25)
    # 仍失败：保留 tmp，下轮再试（不影响计数）

if __name__ == '__main__':
    t0 = time.time()
    n = full_scan()   # 每次启动全量重扫（~33s），保证 tot/today/buckets 绝对准确
    print(f"full scan: {n} files, {S['reqs']} reqs, {S['tot']} tokens in {time.time()-t0:.1f}s", flush=True)
    write_live()
    i = 0
    while True:
        time.sleep(INTERVAL)
        i += 1
        try:
            changed = 0
            for root, _, files in os.walk(PROJ):
                for f in files:
                    if not f.endswith('.jsonl'): continue
                    p = os.path.join(root, f)
                    try: sz = os.path.getsize(p)
                    except OSError: continue
                    if p not in offsets:
                        offsets[p] = [0, b'']
                    off = offsets[p][0]
                    if sz > off:
                        try:
                            with open(p, 'rb') as fh:
                                fh.seek(off)
                                process_chunk(p, fh.read(), is_tail=True)
                            offsets[p][0] = sz
                            changed += 1
                        except OSError: pass
                    elif sz < off:  # 日志轮转/重建
                        offsets[p] = [sz, b'']
            write_live()
            if changed or i % 30 == 0:
                with lock:
                    print(f"[{time.strftime('%H:%M:%S')}] +{changed} files changed | tot={S['tot']} today={S['today']}", flush=True)
            if i % 60 == 0:
                save_state()
        except Exception as e:
            print(f"[{time.strftime('%H:%M:%S')}] loop ERROR {e}", flush=True)
