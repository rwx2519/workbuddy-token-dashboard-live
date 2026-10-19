# WorkBuddy Token Dashboard · Live 增强版

把 WorkBuddy 的真实 token 消耗变成一张**会呼吸的看板**：霓虹深色 UI、秒级实时心跳、脉冲心电图、增量日志监视。

> 基于 [fuyi-git/token-dashboard](https://github.com/fuyi-git/token-dashboard) 深度魔改，感谢原项目。
> 数据 100% 来自本机会话日志（请求级真实 usage），不外发、不上传。

## 相比原版的增强

| 模块 | 说明 |
|---|---|
| 🎨 霓虹深色 UI | 深蓝黑底 + 电光蓝主色、高饱和模型撞色、卡片入场动画、KPI 辉光，默认深色（可切浅色） |
| ❤️ LIVE 秒表条 | 累计 Token 大数字（有请求闪绿）、今日 Token / 今日请求 / 距上次请求（秒级跳动） |
| 〰️ 脉冲心电图 | 30 分钟窗口，每个请求按真实时刻打一次 QRS 尖峰（幅度 ∝ token 量），波形常驻并随时间左移；另有 120s 滚动窗"活跃 Agent 心电图" |
| 🩸 断线指示 | 心跳点绿=实时 / 橙=延迟 / 红=离线（离线时自动回退到内嵌快照） |
| ⚡ 秒级增量监视 | `live_tokens.py` 全量扫一次后只读日志新增字节，每秒输出 `live.json`，启动快、开销小 |
| 🔄 自动刷新 | 页面 30s 比对生成时间戳，有新数据才重载（不打断下钻状态）；刷新器只在数据真变时重写 HTML |
| 📱 移动端自适应 | ≤900px 单列布局 + 横屏矮窗口压缩模式 |
| 📴 离线可看 | 生成时内嵌 live.json 快照，file:// 打开也有静态 LIVE 数据 |

## 文件结构

```
├── SKILL.md                  # WorkBuddy Skill 定义
├── README.md
├── setup_pin.ps1             # Windows：桌面快捷方式 + 任务栏钉选（Edge --app 模式）
├── check_js.js               # 生成后对 HTML 内嵌 JS 做语法自检（node）
└── scripts/
    ├── gen_dashboard.py      # 看板生成（单文件 HTML，仅标准库 3.8+）
    ├── live_tokens.py        # 秒级增量监视器 → live.json
    ├── watch_dashboard.py    # 定时重建看板（数据无变化不重写）
    └── dashboard_server.py   # 固定端口 HTTP 服务器（:8619，供秒表/手机访问）
```

## 快速开始

### 方式一：作为 WorkBuddy Skill（推荐）

```bash
git clone https://github.com/<你>/workbuddy-token-dashboard-live ~/.workbuddy/skills/token-dashboard
```

重启 WorkBuddy 会话，说一句"**看看我的 token 用量**"即可。

### 方式二：手动运行

```bash
python scripts/gen_dashboard.py                  # 生成 token-dashboard.html
python scripts/live_tokens.py                    # （可选）启动秒级实时心跳
python scripts/dashboard_server.py               # （可选）http://127.0.0.1:8619/
python scripts/watch_dashboard.py                # （可选）每 60s 自动重建看板
```

打开 `http://127.0.0.1:8619/` 即可看到实时版；手机连同一 Wi-Fi 访问 `http://<电脑IP>:8619/`。

### Windows 任务栏图标

以管理员/普通 PowerShell 运行 `setup_pin.ps1`：自动创建桌面快捷方式（Edge `--app` 模式，无地址栏独立窗口）、尝试钉选任务栏；配合启动文件夹脚本可实现开机自启三件套（server + live_tokens + watch）。

## 实时链路原理

```
~/.workbuddy/projects/**/*.jsonl
        │  增量尾巴读取（启动全量 1 次，之后每秒只读新增字节）
        ▼
live_tokens.py ──每 1s──▶ live.json {tot, today, reqs, pulses[], spark[], rate5}
        │                                   │
        ▼                                   ▼
watch_dashboard.py（数据变了才重建）    页面每 1s fetch，30s 比对 gen 时间戳按需 reload
```

## 数据与口径

- 数据源：`~/.workbuddy/projects/**/*.jsonl` 的 `providerData.rawUsage / usage`（请求级真实 usage）；子代理日志自动归属父会话。
- 预估金额基于 `gen_dashboard.py` 内 `PRICE` 表（元/百万 token [输入, 输出, 缓存命中]），按每条请求实际缓存命中计价；不同套餐价格不同，可自行修改。
- 所有数据留在本机，不外发。
