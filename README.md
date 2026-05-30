# 📊 推特股票热图 — Twitter Stock Heatmap

多源股票监控热图 + 行业关系网络图，基于推特（Nitter）实时抓取数据，D3.js 可视化。

## 功能

- **多源切换** — 支持多个推特账号来源（@aleabitoreddit / @leopoldasch），互不混同
- **共同关注** — 自动计算多个来源同时提及的股票，生成交集页面
- **🔥 热图卡片** — 每支股票一张卡片，热度条显示提及频率，颜色按行业区分
- **🌿 紫苏叶理论** — 紫色标识上游垄断瓶颈股，一键筛选"产业链紫苏叶"
- **🕸️ 行业关系网络** — D3.js 力导向图，箭头表示供应商/客户/代工/合作关系，节点大小=热度
- **☁️ 标签云** — 按热度比例展示股票代码云
- **📂 行业分布** — 板块热度汇总 + 分类说明
- **🔍 详情弹窗** — 点击任意卡片/节点，展示行业链、相关推文、关联关系
- **🔄 每日自动更新** — 通过 refresh.sh + Shortcuts 自动化定时刷新

## 快速开始

```bash
# 1. 克隆项目
git clone <repo-url>
cd stock-heatmap

# 2. 初始化数据
python3 build_data.py

# 3. 在浏览器中打开
open index.html
```

## 数据源

| 来源 | 账号 | 股票数 | 行业焦点 |
|------|------|--------|----------|
| 🔴 @aleabitoreddit | WSB 交易员/供应链分析师 | 31 | 光子/CPO、半导体供应链 |
| 🟣 @leopoldasch | Leopold Aschenbrenner | 21 | AI 安全、算力基建、数据中心能源 |
| 🟡 共同关注 | 交集 | 8 | NVDA, MSFT, AMZN, GOOGL, META, AMD, INTC, TSLA |

## 项目结构

```
stock-heatmap/
├── index.html              # 主页面（HTML + CSS + 内联 JS）
├── build_data.py           # 热图数据生成器
├── refresh.sh              # 每日刷新脚本
├── data/
│   ├── index.json                          # 来源索引
│   ├── heatmap_aleabitoreddit.json         # 来源1 热图数据
│   ├── heatmap_leopoldasch.json            # 来源2 热图数据
│   ├── heatmap_overlap.json                # 共同关注数据
│   ├── stocks_aleabitoreddit.json          # 来源1 原始股票/关系数据
│   └── stocks_leopoldasch.json             # 来源2 原始股票/关系数据
└── README.md
```

## 数据格式

每支股票包含：
- `ticker` — 股票代码
- `name` — 公司名
- `sector` — 行业分类（用于颜色）
- `industry` / `sub_industry` — 细分行业
- `mcap` — 市值
- `desc` — 描述
- `heat_score` — 热度分数 0-1
- `mention_count` — 提及次数
- `recent_tweets` — 最近提及推文

行业关系：
- `source` / `target` — 关系两端股票代码
- `type` — supplier（供应商）/ customer（客户）/ peer（同业）/ partner（合作）/ foundry（代工）
- `label` — 关系描述

## 添加新来源

1. 创建 `data/stocks_<sourcename>.json`（参考现有格式）
2. 在 `build_data.py` 的 `SOURCES` 列表中添加来源名
3. 运行 `python3 build_data.py` 自动生成热图数据

## 自动更新（iOS 快捷指令）

1. 打开 Apple「快捷指令」App
2. 创建个人自动化 → 定时（如每天 9:00）
3. 添加操作「运行脚本」
4. 输入：`sh /path/to/stock-heatmap/refresh.sh`

## 技术栈

- **D3.js v7** — 力导向图、数据绑定
- **Nitter** — 免登录 X/Twitter 前端
- **纯前端** — 零后端依赖，静态 JSON 驱动
- **静默更新** — minis-browser-use CLI 抓取推文

## License

MIT
