#!/usr/bin/env python3
"""Build heatmap data for multiple sources."""
import json, os, sys, time, random
from datetime import datetime, timezone, timedelta

DATA_DIR = "/var/minis/workspace/stock-heatmap/data"
SOURCES = ["aleabitoreddit", "leopoldasch"]

def load_source(source):
    with open(os.path.join(DATA_DIR, f"stocks_{source}.json")) as f:
        d = json.load(f)
    
    # Set mention counts and heat scores
    # Auto-expire NEW tags (>1 day)
    bjt = timezone(timedelta(hours=8))
    now = datetime.now(bjt)
    if 'newly_added_dates' in d:
        for ticker in list(d['newly_added_dates'].keys()):
            added = d['newly_added_dates'][ticker]
            try:
                dt = datetime.strptime(added, '%Y-%m-%d')
                days_old = (now - dt.replace(tzinfo=bjt)).days
                if days_old >= 1:
                    del d['newly_added_dates'][ticker]
            except: pass
    
    ticker_mentions = d.get("ticker_mentions", {})
    max_count = max(ticker_mentions.values()) if ticker_mentions else 1
    
    stocks = []
    for s in d["stocks"]:
        ticker = s["ticker"]
        count = ticker_mentions.get(ticker, 0)
        heat = round(0.05 + 0.95 * (count / max_count), 3)
        s2 = dict(s)
        s2["mention_count"] = count
        s2["heat_score"] = heat
        s2["recent_tweets"] = []
        stocks.append(s2)
    
    # Sector summary
    sector_summary = {}
    for s in stocks:
        sec = s["sector"]
        if sec not in sector_summary:
            sector_summary[sec] = {"count": 0, "total_score": 0, "stocks": []}
        sector_summary[sec]["count"] += 1
        sector_summary[sec]["total_score"] += s["heat_score"]
        sector_summary[sec]["stocks"].append(s["ticker"])
    
    return {
        "source": d["source"],
        "source_label": d["source_label"],
        "source_bio": d["source_bio"],
        "source_color": d["source_color"],
        "stocks": stocks,
        "relations": d["relations"],
        "sector_colors": d["sector_colors"],
        "industry_groups": d["industry_groups"],
        "sector_summary": sector_summary,
        "tweet_count": sum(ticker_mentions.values()),
        "last_updated": time.strftime("%Y-%m-%dT%H:%M:%S+08:00")
    }

def build_overlap(sources_data):
    """Build the overlap (common stocks) between sources."""
    src_names = [d["source"] for d in sources_data]
    
    # Get all tickers per source
    tickers_by_source = {}
    stocks_by_source = {}
    for d in sources_data:
        src = d["source"]
        tickers_by_source[src] = {s["ticker"] for s in d["stocks"]}
        stocks_by_source[src] = {s["ticker"]: s for s in d["stocks"]}
    
    # Find intersection
    common = set.intersection(*tickers_by_source.values()) if len(sources_data) > 1 else set()
    
    overlap_stocks = []
    for ticker in sorted(common):
        # Merge info from both sources
        src0 = sources_data[0]
        src1 = sources_data[1]
        s0 = src0["stocks"][next(i for i,s in enumerate(src0["stocks"]) if s["ticker"]==ticker)]
        s1 = src1["stocks"][next(i for i,s in enumerate(src1["stocks"]) if s["ticker"]==ticker)]
        
        overlap_stocks.append({
            "ticker": ticker,
            "name": s0["name"],
            "desc": f"{s0['desc']} / {s1['desc']}",
            "sector": "共同关注",
            "heat_score_0": s0["heat_score"],
            "heat_score_1": s1["heat_score"],
            "total_score": round(s0["heat_score"] + s1["heat_score"], 3),
            "mention_count_0": s0["mention_count"],
            "mention_count_1": s1["mention_count"]
        })
    
    overlap_stocks.sort(key=lambda x: -x["total_score"])
    
    # Build overlap relations: edges from both sources involving common tickers
    overlap_relations = []
    src_names_map = {d["source"]: d for d in sources_data}
    seen_pairs = set()
    
    for d in sources_data:
        src = d["source"]
        for r in d["relations"]:
            if r["source"] in common or r["target"] in common:
                pair = (r["source"], r["target"], src)
                if pair not in seen_pairs:
                    seen_pairs.add(pair)
                    overlap_relations.append({
                        "source": r["source"],
                        "target": r["target"],
                        "type": r["type"],
                        "label": f"{r['label']} [{src}]"
                    })
    
    return {
        "stocks": overlap_stocks,
        "relations": overlap_relations,
        "source1": src_names[0],
        "source2": src_names[1],
        "source1_label": src_names_map[src_names[0]]["source_label"],
        "source2_label": src_names_map[src_names[1]]["source_label"],
        "color1": src_names_map[src_names[0]]["source_color"],
        "color2": src_names_map[src_names[1]]["source_color"],
        "last_updated": time.strftime("%Y-%m-%dT%H:%M:%S+08:00")
    }

def main():
    sources_data = []
    for src in SOURCES:
        data = load_source(src)
        sources_data.append(data)
        
        out_file = os.path.join(DATA_DIR, f"heatmap_{src}.json")
        with open(out_file, "w") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"✅ {src}: {len(data['stocks'])}支股票, {len(data['relations'])}条关系 → heatmap_{src}.json")
    
    # Build overlap
    overlap = build_overlap(sources_data)
    out_overlap = os.path.join(DATA_DIR, "heatmap_overlap.json")
    with open(out_overlap, "w") as f:
        json.dump(overlap, f, ensure_ascii=False, indent=2)
    
    print(f"\n🔗 共同关注: {len(overlap['stocks'])}支股票 → heatmap_overlap.json")
    if overlap["stocks"]:
        print("   共同股票:", ", ".join(s["ticker"] for s in overlap["stocks"][:10]), 
              f"{'...' if len(overlap['stocks']) > 10 else ''}")
    
    # Create index file mapping
    index = {
        "sources": [
            {"id": "aleabitoreddit", "label": "@aleabitoreddit", "file": "heatmap_aleabitoreddit.json", 
             "desc": "光子/半导体供应链", "color": "#FF6B6B", "stock_count": len(sources_data[0]["stocks"])},
            {"id": "leopoldasch", "label": "@leopoldasch", "file": "heatmap_leopoldasch.json",
             "desc": "AI 安全/算力基建", "color": "#A855F7", "stock_count": len(sources_data[1]["stocks"])}
        ],
        "overlap": {"file": "heatmap_overlap.json", "stock_count": len(overlap["stocks"])},
        "last_updated": time.strftime("%Y-%m-%dT%H:%M:%S+08:00")
    }
    with open(os.path.join(DATA_DIR, "index.json"), "w") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)
    
    print(f"\n📋 所有数据已构建完成")

if __name__ == "__main__":
    main()
