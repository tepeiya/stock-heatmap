#!/bin/sh
# Refresh stock heatmap data from Twitter sources
# Run daily via Shortcuts automation or manually

DIR="/var/minis/workspace/stock-heatmap"
LOG="$DIR/data/refresh.log"
DATE=$(date '+%Y-%m-%d %H:%M:%S')

echo "[$DATE] 🔄 开始刷新热图数据..." | tee -a "$LOG"

# 1. Rebuild from stock data (no browser needed)
echo "🏗️ 重建热图数据..." | tee -a "$LOG"
python3 "$DIR/build_data.py" 2>&1 | tee -a "$LOG"

echo "✅ 热图数据已刷新" | tee -a "$LOG"
echo "---" >> "$LOG"
