#!/usr/bin/env python3
"""Add shiso labels to all stock data files."""
import json

SHISO_TICKERS = {
    'AAOI','LITE','COHR','SIVE','SOI','IQE','MTSI','POET','FOCI',
    'AXTI','SHUNSIN','NVTS','POWI','WOLF','XFAB','RPI','LPK','ALRIB','VPG'
}

SHISO_NOTES = {
    'AAOI': 'InP激光器美国少数供应商，上游瓶颈',
    'LITE': 'OCS光开关近乎垄断，Google TPU唯一供应商',
    'COHR': '激光器龙头，关键光电子器件',
    'SIVE': 'CPO激光器全球关键瓶颈，仅此一家',
    'SOI': 'SOI基板垄断，全球仅此一家',
    'IQE': '外延晶圆产能隐形冠军',
    'MTSI': 'RF/光电子利基龙头',
    'POET': '光引擎独特技术，上游瓶颈',
    'FOCI': '光纤组件利基供应商',
    'AXTI': '磷化铟衬底，全球仅2-3家供应商',
    'SHUNSIN': '光模块封装利基',
    'NVTS': 'GaN功率半导体领军',
    'POWI': '高压电源IC利基龙头',
    'WOLF': 'SiC衬底龙头',
    'XFAB': '美国唯一高量产SiC代工厂',
    'RPI': '边缘计算硬件利基龙头',
    'LPK': '玻璃基板激光加工近乎垄断',
    'ALRIB': '量子+光电子双寡头',
    'VPG': '精密传感器利基龙头'
}

def add_shiso_to_file(filepath):
    with open(filepath) as f:
        d = json.load(f)
    
    for s in d['stocks']:
        t = s['ticker']
        s['shiso'] = t in SHISO_TICKERS
        if s['shiso']:
            s['shiso_note'] = SHISO_NOTES.get(t, '产业链上游瓶颈')
    
    count = sum(1 for s in d['stocks'] if s.get('shiso'))
    print(f'{filepath}: {count}/{len(d["stocks"])} 紫苏叶')
    
    with open(filepath, 'w') as f:
        json.dump(d, f, ensure_ascii=False, indent=2)

BASE = '/var/minis/workspace/stock-heatmap/data'
for src in ['aleabitoreddit', 'leopoldasch']:
    add_shiso_to_file(f'{BASE}/stocks_{src}.json')

# Also update heatmap data files
for src in ['aleabitoreddit', 'leopoldasch']:
    fp = f'{BASE}/heatmap_{src}.json'
    try:
        with open(fp) as f:
            d = json.load(f)
        for s in d['stocks']:
            t = s['ticker']
            s['shiso'] = t in SHISO_TICKERS
            if s['shiso']:
                s['shiso_note'] = SHISO_NOTES.get(t, '产业链上游瓶颈')
        with open(fp, 'w') as f:
            json.dump(d, f, ensure_ascii=False, indent=2)
        count = sum(1 for s in d['stocks'] if s.get('shiso'))
        print(f'{fp}: {count}/{len(d["stocks"])} 紫苏叶(h)')
    except FileNotFoundError:
        pass

print('\n✅ 所有数据文件已更新')
