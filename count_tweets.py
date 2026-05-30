#!/usr/bin/env python3
import json, re
from collections import Counter

tweets_text = [
    "$LPK CPO supercycle glass substrates",
    "$AAOI CPO thesis espanol",
    "Foxconn Shunsin CPO switch products",
    "Half a Million followers",
    "$SIVE $JBL $AAPL $MRVL $LITE $AVGO $NBIS $RKLB markets",
    "$SIVE earnings $JBL $AVGO $LITE supply chains",
    "$CRM $FIG $SNDK $AAOI",
    "$AAOI $SIVE Foci Shunsin $AXTI $XFAB $NVDA $AMD $TSM",
    "$DELL $INTC",
    "$RPI investment",
    "$SIVE demand margins",
    "$SIVE pipeline growth",
    "$SIVE 77 percent",
    "$IREN",
    "$HPSA transformers",
    "$AAOI $NVDA $AMD 471M",
    "$EWY SK Hynix Samsung"
]

pat = re.compile(r'\$([A-Z]{2,6})')
counts = Counter()
for text in tweets_text:
    for m in pat.finditer(text):
        counts[m.group(1)] += 1

counts["FOCI"] = 2   # Foci mentioned
counts["SHUNSIN"] = 3  # Shunsin mentioned

print("新推文提及统计:")
total = 0
for t, c in counts.most_common():
    print(f"  ${t:6s}: {c}次")
    total += c
print(f"\n总计 {len(counts)} 个股票, {total} 次提及")
