#!/usr/bin/env python3
"""Update heatmap data with new tweet mentions."""
import json, os, time

BASE = "/var/minis/workspace/stock-heatmap/data"

# New mentions from this batch
new_mentions = {
    'SIVE': 6, 'AAOI': 4, 'SHUNSIN': 3, 'JBL': 2, 'LITE': 2, 'AVGO': 2,
    'NVDA': 2, 'AMD': 2, 'FOCI': 2, 'LPK': 1, 'AAPL': 1, 'MRVL': 1,
    'NBIS': 1, 'RKLB': 1, 'CRM': 1, 'FIG': 1, 'SNDK': 1, 'AXTI': 1,
    'XFAB': 1, 'TSM': 1, 'DELL': 1, 'INTC': 1, 'RPI': 1, 'IREN': 1,
    'HPSA': 1, 'EWY': 1
}

# Existing mentions from stocks_aleabitoreddit
existing = {
    'SIVE':12,'NVDA':9,'XFAB':8,'LITE':6,'AAOI':5,'SOI':5,'NVTS':5,
    'AMZN':5,'IQE':4,'AXTI':4,'MRVL':4,'MSFT':3,'COHR':3,'POWI':3,
    'WOLF':3,'MTSI':2,'GOOGL':2,'META':2,'NOK':2,'MU':2,
    'POET':1,'FOCI':1,'AMD':1,'INTC':1,'RPI':1,'LPK':1,'ALRIB':1,
    'TSLA':1,'NBIS':1,'IREN':1,'VPG':1,'SHUNSIN':1
}

# Merge (new gets more weight since they're more recent)
merged = {}
for t in set(list(existing.keys()) + list(new_mentions.keys())):
    merged[t] = existing.get(t, 0) + new_mentions.get(t, 0) * 3  # New mentions weighted 3x

max_count = max(merged.values()) if merged else 1

# Update stocks file
with open(f"{BASE}/stocks_aleabitoreddit.json") as f:
    d = json.load(f)

for s in d['stocks']:
    t = s['ticker']
    s['mention_count'] = merged.get(t, 0)
    s['heat_score'] = round(0.05 + 0.95 * s['mention_count'] / max_count, 3) if s['mention_count'] > 0 else 0.05

with open(f"{BASE}/stocks_aleabitoreddit.json", 'w') as f:
    json.dump(d, f, ensure_ascii=False, indent=2)

# Rebuild heatmap file
ticker_mentions = {s['ticker']: s['mention_count'] for s in d['stocks']}

sector_summary = {}
for s in d['stocks']:
    sec = s['sector']
    if sec not in sector_summary:
        sector_summary[sec] = {"count": 0, "total_score": 0, "stocks": []}
    sector_summary[sec]["count"] += 1
    sector_summary[sec]["total_score"] += s['heat_score']
    sector_summary[sec]["stocks"].append(s['ticker'])

# Add tweet previews from new tweets
tweet_previews = {
    'SIVE': [
        "markets went from doubting $SIVE customers to doubting execution to doubting share... Now 77% pipeline growth",
        "$SIVE earnings transcript: demand outstrips supply, 60% gross margins, production orders imminent",
        "$SIVE revenue pipeline grew 77% in 3 months - clearest inflection of CPO supercycle"
    ],
    'AAOI': [
        "I'm actually even more bullish on $AAOI at $13B MC given laser bottlenecks",
        "$AAOI will post $471M/month by H1 2027, TAM increases exponentially 2028",
        "software bros vs AI names - $AAOI casually up 200-1000%"
    ],
    'SHUNSIN': [
        "Foxconn CPO switch products Q3 2026 - who handles the work? Shunsin (6451)",
        "Shunsin at $2B MC - markets don't know what's coming"
    ],
    'FOCI': [
        "Foci - $NVDA/$TSM FAU supplier and bottleneck for COUPE. Only $2.8B?",
        "BOM share for passive components + FAU are massive in 2028"
    ],
    'LITE': ["$SIVE vs $LITE competition - turns out Sivers is primary supplier for Ayar"],
    'NVDA': ["$NVDA pushing 800vdc, SiC/GaN foundries go brr"],
    'XFAB': ["$XFAB central to EU CHIPS act 2 for silicon photonics at $1.5B MC"]
}

for s in d['stocks']:
    t = s['ticker']
    if t in tweet_previews:
        s['recent_tweets'] = [{"text": txt, "url": f"https://x.com/aleaboreddit", "time": "latest", "likes": "100"} for txt in tweet_previews[t]]
    elif not s.get('recent_tweets'):
        s['recent_tweets'] = []

# Add new tickers not in original list (JBL, AVGO, AAPL, DELL, etc.)
new_stocks_to_add = {
    'JBL': {'name': 'Jabil Inc', 'sector': 'Semiconductors', 'industry': 'Manufacturing', 'sub_industry': 'EMS', 'desc': '电子制造服务，$SIVE 合作伙伴'},
    'AVGO': {'name': 'Broadcom', 'sector': 'Semiconductors', 'industry': 'Networking', 'sub_industry': 'ASIC/Switches', 'desc': '半导体/网络芯片巨头'},
    'AAPL': {'name': 'Apple Inc', 'sector': 'Tech Giants', 'industry': 'Consumer Tech', 'sub_industry': 'AI Devices', 'desc': '消费电子/AI'},
    'DELL': {'name': 'Dell Technologies', 'sector': 'Tech Giants', 'industry': 'Hardware', 'sub_industry': 'AI Servers', 'desc': 'AI服务器制造商'},
    'RKLB': {'name': 'Rocket Lab', 'sector': 'Tech Giants', 'industry': 'Space', 'sub_industry': 'Launch/Space Systems', 'desc': '火箭发射/航天系统'},
    'CRM': {'name': 'Salesforce', 'sector': 'Tech Giants', 'industry': 'Enterprise AI', 'sub_industry': 'CRM/AI', 'desc': '企业CRM AI'},
    'SNDK': {'name': 'SanDisk', 'sector': 'Semiconductors', 'industry': 'Storage', 'sub_industry': 'NAND Flash', 'desc': 'NAND闪存龙头'}
}

existing_tickers = {s['ticker'] for s in d['stocks']}
for t, info in new_stocks_to_add.items():
    if t not in existing_tickers:
        n = {'ticker': t, 'name': info['name'], 'sector': info['sector'],
             'industry': info['industry'], 'sub_industry': info['sub_industry'],
             'desc': info['desc'], 'shiso': False, 'mcap': 0,
             'mention_count': merged.get(t, 1), 'heat_score': round(0.05 + 0.95 * merged.get(t, 1) / max_count, 3),
             'recent_tweets': []}
        d['stocks'].append(n)
        # Update sector summary
        sec = n['sector']
        if sec not in sector_summary:
            sector_summary[sec] = {"count": 0, "total_score": 0, "stocks": []}
        sector_summary[sec]["count"] += 1
        sector_summary[sec]["total_score"] += n['heat_score']
        sector_summary[sec]["stocks"].append(t)

# Update sector_summary in stocks file
# Add new relations
existing_rels = {(r['source'], r['target']) for r in d['relations']}
new_rels = [
    {'source': 'SIVE', 'target': 'JBL', 'type': 'supplier', 'label': '可插拔光收发器合作'},
    {'source': 'SIVE', 'target': 'AAPL', 'type': 'supplier', 'label': '潜在客户'},
    {'source': 'SIVE', 'target': 'AVGO', 'type': 'supplier', 'label': 'Win Semi代工链'},
    {'source': 'SIVE', 'target': 'RKLB', 'type': 'peer', 'label': '航空航天关注'},
    {'source': 'SHUNSIN', 'target': 'NVDA', 'type': 'supplier', 'label': 'CPO封装测试'},
    {'source': 'FOCI', 'target': 'NVDA', 'type': 'supplier', 'label': 'FAU/COUPE瓶颈'},
    {'source': 'FOCI', 'target': 'TSM', 'type': 'supplier', 'label': 'COUPE合作'},
    {'source': 'DELL', 'target': 'NVDA', 'type': 'customer', 'label': 'AI服务器'},
    {'source': 'DELL', 'target': 'INTC', 'type': 'customer', 'label': '供应链'},
]
for r in new_rels:
    pair = (r['source'], r['target'])
    if pair not in existing_rels and (r['target'], r['source']) not in existing_rels:
        d['relations'].append(r)
        existing_rels.add(pair)

# Save
from datetime import timedelta, timezone, datetime
bjt_tz = timezone(timedelta(hours=8))
d['last_updated'] = datetime.now(bjt_tz).strftime('%Y-%m-%dT%H:%M:%S+08:00')

with open(f"{BASE}/stocks_aleabitoreddit.json", 'w') as f:
    json.dump(d, f, ensure_ascii=False, indent=2)

# Now build heatmap data
heatmap = {
    "source": d["source"],
    "source_label": d["source_label"],
    "source_bio": d.get("source_bio", ""),
    "source_color": d.get("source_color", "#FF6B6B"),
    "stocks": d["stocks"],
    "relations": d["relations"],
    "sector_colors": d["sector_colors"],
    "industry_groups": d["industry_groups"],
    "sector_summary": sector_summary,
    "tweet_count": sum(merged.values()),
    "last_updated": d["last_updated"]
}

with open(f"{BASE}/heatmap_aleabitoreddit.json", 'w') as f:
    json.dump(heatmap, f, ensure_ascii=False, indent=2)

# Update index
with open(f"{BASE}/index.json") as f:
    idx = json.load(f)
for s in idx['sources']:
    if s['id'] == 'aleaboreddit' or s['id'] == 'aleabitoreddit':
        s['stock_count'] = len(d['stocks'])
        s['stock_count'] = len(heatmap['stocks'])
idx['last_updated'] = heatmap['last_updated']
with open(f"{BASE}/index.json", 'w') as f:
    json.dump(idx, f, ensure_ascii=False, indent=2)

print(f"✅ 更新完成: {len(heatmap['stocks'])}支股票, {len(heatmap['relations'])}条关系")
print(f"🔥 热度Top5: ", end="")
for s in sorted(heatmap['stocks'], key=lambda x: -x['heat_score'])[:5]:
    print(f"{s['ticker']}({s['heat_score']:.2f}) ", end="")
print()
