#!/usr/bin/env python3
"""Update heatmap data with new tweet mentions and auto-expire NEW tags."""
import json, os, time
from datetime import datetime, timezone, timedelta

BASE = "/var/minis/workspace/stock-heatmap/data"
BJT = timezone(timedelta(hours=8))
NOW = datetime.now(BJT)

# New mentions from this batch (update these counts each time)
new_mentions = {
    'SIVE': 6, 'AAOI': 4, 'SHUNSIN': 3, 'JBL': 2, 'LITE': 2, 'AVGO': 2,
    'NVDA': 2, 'AMD': 2, 'FOCI': 2, 'LPK': 1, 'AAPL': 1, 'MRVL': 1,
    'NBIS': 1, 'RKLB': 1, 'CRM': 1, 'FIG': 1, 'SNDK': 1, 'AXTI': 1,
    'XFAB': 1, 'TSM': 1, 'DELL': 1, 'INTC': 1, 'RPI': 1, 'IREN': 1,
    'HPSA': 1, 'EWY': 1
}

# Track WHEN each stock was first newly_added
NEW_ADDED_DATE = {
    # Format: 'TICKER': '2026-05-30'
    'JBL': '2026-05-30', 'AVGO': '2026-05-30', 'AAPL': '2026-05-30',
    'DELL': '2026-05-30', 'RKLB': '2026-05-30', 'CRM': '2026-05-30',
    'SNDK': '2026-05-30', 'TSM': '2026-05-30', 'FIG': '2026-05-30',
    'HPSA': '2026-05-30', 'EWY': '2026-05-30'
}

TODAY = NOW.strftime('%Y-%m-%d')

# Existing mentions from stocks_aleabitoreddit
existing = {
    'SIVE':12,'NVDA':9,'XFAB':8,'LITE':6,'AAOI':5,'SOI':5,'NVTS':5,
    'AMZN':5,'IQE':4,'AXTI':4,'MRVL':4,'MSFT':3,'COHR':3,'POWI':3,
    'WOLF':3,'MTSI':2,'GOOGL':2,'META':2,'NOK':2,'MU':2,
    'POET':1,'FOCI':1,'AMD':1,'INTC':1,'RPI':1,'LPK':1,'ALRIB':1,
    'TSLA':1,'NBIS':1,'IREN':1,'VPG':1,'SHUNSIN':1
}

# Merge counts
merged = {}
for t in set(list(existing.keys()) + list(new_mentions.keys())):
    merged[t] = existing.get(t, 0) + new_mentions.get(t, 0) * 3

max_count = max(merged.values()) if merged else 1

# Load stocks file
with open(f"{BASE}/stocks_aleabitoreddit.json") as f:
    d = json.load(f)

# Check existing newly_added dates
if 'newly_added_dates' not in d:
    d['newly_added_dates'] = {}

# Merge in new dates
for ticker, date in NEW_ADDED_DATE.items():
    if ticker not in d['newly_added_dates']:
        d['newly_added_dates'][ticker] = date

# Auto-expire: remove newly_added flag for stocks added >1 day ago
for ticker in list(d['newly_added_dates'].keys()):
    added_date = d['newly_added_dates'][ticker]
    try:
        dt = datetime.strptime(added_date, '%Y-%m-%d')
        days_old = (NOW - dt.replace(tzinfo=BJT)).days
        if days_old >= 1:
            del d['newly_added_dates'][ticker]
            print(f'⏰ 过期移除 NEW 标记: {ticker} (已{days_old}天)')
    except:
        pass

# Apply counts and flags
for s in d['stocks']:
    t = s['ticker']
    s['mention_count'] = merged.get(t, 0)
    s['heat_score'] = round(0.05 + 0.95 * s['mention_count'] / max_count, 3) if s['mention_count'] > 0 else 0.05
    s['newly_added'] = t in d['newly_added_dates']

with open(f"{BASE}/stocks_aleabitoreddit.json", 'w') as f:
    json.dump(d, f, ensure_ascii=False, indent=2)

# Rebuild heatmap
ticker_mentions = {s['ticker']: s['mention_count'] for s in d['stocks']}

sector_summary = {}
for s in d['stocks']:
    sec = s['sector']
    if sec not in sector_summary:
        sector_summary[sec] = {"count": 0, "total_score": 0, "stocks": []}
    sector_summary[sec]["count"] += 1
    sector_summary[sec]["total_score"] += s['heat_score']
    sector_summary[sec]["stocks"].append(s['ticker'])

# Save heatmap
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
    "last_updated": NOW.strftime('%Y-%m-%dT%H:%M:%S+08:00')
}

with open(f"{BASE}/heatmap_aleabitoreddit.json", 'w') as f:
    json.dump(heatmap, f, ensure_ascii=False, indent=2)

# Update index
with open(f"{BASE}/index.json") as f:
    idx = json.load(f)
for s in idx['sources']:
    if s['id'] == 'aleabitoreddit':
        s['stock_count'] = len(heatmap['stocks'])
idx['last_updated'] = heatmap['last_updated']
with open(f"{BASE}/index.json", 'w') as f:
    json.dump(idx, f, ensure_ascii=False, indent=2)

new_count = sum(1 for s in heatmap['stocks'] if s.get('newly_added'))
print(f"✅ 更新完成: {len(heatmap['stocks'])}支股票, {len(heatmap['relations'])}条关系")
print(f"🆕 当前NEW标记: {new_count}支")
print(f"🔥 热度Top5: ", end="")
for s in sorted(heatmap['stocks'], key=lambda x: -x['heat_score'])[:5]:
    print(f"{s['ticker']}({s['heat_score']:.2f}) ", end="")
print()
