// ========== STATE ==========
const DATA_DIR = 'data';
let indexData = null;
let sourceData = {};
let overlapData = null;
let currentSource = 'aleabitoreddit';
let showNetLabels = true;
let svg = null, simulation = null, gNodes = null, gLinks = null, gLinkLabels = null;

// ========== LOAD ==========
function init() {
  var ts = Date.now();
  fetch(DATA_DIR + '/index.json?_t=' + ts).then(function(r) { return r.json(); }).then(function(idx) {
    indexData = idx;
    var sources = idx.sources;
    var remaining = sources.length;
    sources.forEach(function(s) {
      fetch(DATA_DIR + '/' + s.file + '?_t=' + ts).then(function(r2) { return r2.json(); }).then(function(d) {
        sourceData[s.id] = d;
        remaining--;
        if (remaining === 0 && idx.overlap) {
          fetch(DATA_DIR + '/' + idx.overlap.file + '?_t=' + ts).then(function(r3) { return r3.json(); }).then(function(ov) {
            overlapData = ov;
            renderUI();
          }).catch(function(e) { document.getElementById('updateInfo').textContent = '⚠️ 重叠数据加载失败'; });
        } else if (remaining === 0) {
          renderUI();
        }
      }).catch(function(e) { document.getElementById('updateInfo').textContent = '⚠️ 数据加载失败: ' + s.id; });
    });
  }).catch(function(e) {
    console.error('Load error:', e);
    document.getElementById('updateInfo').textContent = '⚠️ 数据加载失败';
  });
}

function renderUI() {
  renderSourceBar();
  switchSource(currentSource);
}

function renderSourceBar() {
  const bar = document.getElementById('sourceBar');
  let html = '';
  for (const s of indexData.sources) {
    html += '<button class="source-btn" data-src="' + s.id + '" onclick="switchSource(\'' + s.id + '\')" style="border-color:' + s.color + '40;color:' + s.color + '">'
      + s.label + ' <span class="count">' + s.stock_count + '支</span></button>';
  }
  if (indexData.overlap && overlapData) {
    html += '<button class="source-btn overlap-btn" data-src="overlap" onclick="switchSource(\'overlap\')" style="border-color:#F59E0B40;color:#F59E0B">'
      + '🔗 共同关注 <span class="count">' + overlapData.stocks.length + '支</span></button>';
  }
  bar.innerHTML = html;
  
  const tb = document.getElementById('tabBar');
  const tabs = [{id:'heatmap',label:'🔥 热图'},{id:'network',label:'🕸️ 关系网'},{id:'cloud',label:'☁️ 标签云'},{id:'sectors',label:'📂 行业'}];
  tb.innerHTML = tabs.map(t => '<button class="tab-btn" data-panel="' + t.id + '" onclick="switchTab(\'' + t.id + '\')">' + t.label + '</button>').join('');
  tb.querySelector('.tab-btn').classList.add('active');
}

function switchSource(src) {
  currentSource = src;
  document.querySelectorAll('.source-btn').forEach(b => b.classList.toggle('active', b.dataset.src === src));
  
  const tb = document.getElementById('tabBar');
  const oldOverlap = tb.querySelector('[data-panel="overlap"]');
  
  if (src === 'overlap') {
    if (!oldOverlap) {
      const btn = document.createElement('button');
      btn.className = 'tab-btn active';
      btn.dataset.panel = 'overlap';
      btn.textContent = '🔗 共同股票';
      btn.onclick = function() { switchTab('overlap'); };
      tb.querySelectorAll('.tab-btn').forEach(b => b.style.display = 'none');
      tb.appendChild(btn);
    }
    document.getElementById('panel-overlap').classList.add('active');
    ['panel-heatmap','panel-network','panel-cloud','panel-sectors'].forEach(function(id) {
      document.getElementById(id).classList.remove('active');
    });
    renderOverlap();
  } else {
    tb.querySelectorAll('.tab-btn').forEach(function(b) {
      b.style.display = '';
      if (b.dataset.panel === 'overlap') b.remove();
    });
    document.getElementById('panel-overlap').classList.remove('active');
    
    const data = sourceData[src];
    document.getElementById('updateInfo').textContent = '🕐 ' + data.source_label + ' • 最后更新: ' + (data.last_updated||'').replace('T',' ');
    
    renderStats(data);
    renderLegend(data);
    renderHeatmap(data);
    // Reset network on source switch
    svg = null; simulation = null; gNodes = null; gLinks = null; gLinkLabels = null;
    renderNetwork(data);
    renderCloud(data);
    renderSectors(data);
    
    const activeTab = document.querySelector('.tab-btn.active');
    switchTab(activeTab ? activeTab.dataset.panel : 'heatmap');
  }
}

function switchTab(tab) {
  document.querySelectorAll('.tab-btn').forEach(function(b) {
    b.classList.toggle('active', b.dataset.panel === tab);
  });
  document.querySelectorAll('.panel').forEach(function(p) {
    p.classList.remove('active');
  });
  var p = document.getElementById('panel-' + tab);
  if (p) p.classList.add('active');
  
  // Re-render network graph if needed
  if (tab === 'network' && currentSource !== 'overlap') {
    const wrap = document.getElementById('networkWrap');
    if (!wrap.querySelector('svg')) {
      renderNetwork(sourceData[currentSource]);
    }
  }
}

function renderStats(data) {
  const bar = document.getElementById('statsBar');
  const active = data.stocks.filter(function(s) { return s.mention_count > 0; }).length;
  bar.innerHTML = '<div class="stat-card"><div class="num" style="color:' + (data.source_color||'#58a6ff') + '">' + data.stocks.length + '</div><div class="lbl">跟踪股票</div></div>'
    + '<div class="stat-card"><div class="num">' + active + '</div><div class="lbl">近期提及</div></div>'
    + '<div class="stat-card"><div class="num">' + data.relations.length + '</div><div class="lbl">行业关系</div></div>'
    + '<div class="stat-card"><div class="num">' + (data.tweet_count||0) + '</div><div class="lbl">提及次数</div></div>';
}

function renderLegend(data) {
  const sc = data.sector_colors || {};
  const ig = data.industry_groups || {};
  document.getElementById('legendHeat').innerHTML = Object.keys(sc).map(function(k) {
    return '<span class="legend-item"><span class="dot" style="background:' + sc[k] + '"></span> ' + k + ': ' + (ig[k]||'') + '</span>';
  }).join('');
  
  const rt = {supplier:'供应商',customer:'客户',peer:'同业',partner:'合作',foundry:'代工'};
  const cc = {supplier:'#3fb950',customer:'#f0883e',peer:'#58a6ff',partner:'#6366f1',foundry:'#da3633'};
  document.getElementById('legendNet').innerHTML = Object.keys(rt).map(function(k) {
    return '<span class="legend-item"><span class="line" style="background:' + cc[k] + '"></span> ' + rt[k] + '</span>';
  }).join('');
}

function renderHeatmap(data) {
  const grid = document.getElementById('heatmapGrid');
  const sorted = data.stocks.slice().sort(function(a,b) { return (b.heat_score||0) - (a.heat_score||0); });
  const colors = data.sector_colors || {};
  
  grid.innerHTML = sorted.map(function(s) {
    const color = colors[s.sector] || '#58a6ff';
    const pct = Math.min((s.heat_score||0)*100, 100);
    const prv = s.recent_tweets && s.recent_tweets[0] ? s.recent_tweets[0].text : '';
    return '<div class="heatmap-card" onclick="showDetail(\'' + s.ticker + '\')">'
      + '<div class="heat-bar" style="width:' + pct + '%;background:' + color + '"></div>'
      + '<div class="heat-card-ticker" style="color:' + color + '">' + s.ticker + '</div>'
      + '<div class="heat-card-name">' + s.name + '</div>'
      + '<div><span class="heat-card-sector" style="background:' + color + '">' + s.sector + '</span></div>'
      + '<div class="heat-card-meta"><span>🔥 ' + (s.heat_score||0).toFixed(2) + '</span><span>📢 ' + (s.mention_count||0) + '次</span></div>'
      + (prv ? '<div class="heat-card-preview">"' + prv.substring(0,80) + '..."</div>' : '')
      + '</div>';
  }).join('');
}

function renderNetwork(data) {
  const wrap = document.getElementById('networkWrap');
  if (wrap.querySelector('svg')) return; // Already rendered
  
  const w = wrap.clientWidth || 700;
  const h = wrap.clientHeight || 400;
  
  const nodesMap = {};
  data.stocks.forEach(function(s) {
    nodesMap[s.ticker] = {id:s.ticker, name:s.name, sector:s.sector, heat:s.heat_score||0.1, mentions:s.mention_count||0, r: Math.max(7, 7 + (s.heat_score||0)*18)};
  });
  data.relations.forEach(function(r) {
    if (!nodesMap[r.source]) nodesMap[r.source] = {id:r.source,name:r.source,sector:'Other',heat:0.05,r:5,mentions:0};
    if (!nodesMap[r.target]) nodesMap[r.target] = {id:r.target,name:r.target,sector:'Other',heat:0.05,r:5,mentions:0};
  });
  
  const nodes = Object.values(nodesMap);
  const links = data.relations.map(function(r) { return {source:r.source,target:r.target,type:r.type||'supplier',label:r.label||''}; });
  const colors = data.sector_colors || {};
  
  wrap.innerHTML = '<div class="net-ctrl"><button onclick="resetNet()">↺ 重置</button><button onclick="toggleNetLabels()">🏷️ 标签</button></div>';
  
  svg = d3.select(wrap).append('svg').attr('viewBox',[0,0,w,h]);
  
  const defs = svg.append('defs');
  const arrowColors = {supplier:'#3fb950',customer:'#f0883e',peer:'#58a6ff',partner:'#6366f1',foundry:'#da3633'};
  Object.keys(arrowColors).forEach(function(t) {
    defs.append('marker').attr('id','a-'+t).attr('viewBox','0 -5 10 10').attr('refX',16).attr('markerWidth',5).attr('markerHeight',5).attr('orient','auto')
      .append('path').attr('fill',arrowColors[t]).attr('d','M0,-5L10,0L0,5');
  });
  
  const zoom = d3.zoom().scaleExtent([0.1,4]).on('zoom', function(ev) { g.attr('transform', ev.transform); });
  svg.call(zoom);
  const g = svg.append('g');
  
  gLinks = g.append('g').selectAll('line').data(links).join('line')
    .attr('stroke', function(d) { return arrowColors[d.type] || '#58a6ff'; })
    .attr('stroke-width',1).attr('opacity',0.4).attr('marker-end',function(d) { return 'url(#a-'+d.type+')'; })
    .attr('stroke-dasharray', function(d) { return d.type==='foundry' ? '4,3' : 'none'; });
  
  gLinkLabels = g.append('g').selectAll('text').data(links.filter(function(l) { return l.label; })).join('text')
    .text(function(d) { return d.label; }).attr('font-size','6px').attr('fill','#8b949e').attr('text-anchor','middle').attr('dy',-3);
  
  gNodes = g.append('g').selectAll('g').data(nodes).join('g').style('cursor','pointer')
    .call(d3.drag().on('start',function(ev,d){if(!ev.active)simulation.alphaTarget(0.3).restart();d.fx=d.x;d.fy=d.y;})
      .on('drag',function(ev,d){d.fx=ev.x;d.fy=ev.y;})
      .on('end',function(ev,d){if(!ev.active)simulation.alphaTarget(0);d.fx=null;d.fy=null;}));
  
  gNodes.append('circle').attr('r',function(d) { return d.r; })
    .attr('fill',function(d) { return colors[d.sector] || '#58a6ff'; }).attr('stroke','#fff').attr('stroke-width',1.2).attr('opacity',0.85);
  gNodes.append('text').text(function(d) { return d.id; }).attr('text-anchor','middle').attr('dy',function(d) { return d.r+12; })
    .attr('font-size',function(d) { return Math.max(8, d.r*0.8); }).attr('font-weight','600').attr('fill','#c9d1d9');
  
  gNodes.on('mouseenter',function(ev,d){
    d3.select(this).select('circle').transition().attr('stroke-width',2.5).attr('opacity',1);
    var tip=document.getElementById('tooltip');
    tip.style.display='block';
    tip.innerHTML='<strong>'+d.id+'</strong> — '+d.name+'<br>🔵 '+d.sector+'<br>🔥 '+d.heat.toFixed(2)+' • 📢 '+d.mentions+'次';
    tip.style.left=(ev.pageX+12)+'px'; tip.style.top=(ev.pageY-8)+'px';
  }).on('mousemove',function(ev){
    var tip=document.getElementById('tooltip');
    tip.style.left=(ev.pageX+12)+'px'; tip.style.top=(ev.pageY-8)+'px';
  }).on('mouseleave',function(){
    d3.select(this).select('circle').transition().attr('stroke-width',1.2).attr('opacity',0.85);
    document.getElementById('tooltip').style.display='none';
  }).on('click',function(ev,d){ showDetail(d.id); });
  
  simulation = d3.forceSimulation(nodes)
    .force('link',d3.forceLink(links).id(function(d) { return d.id; }).distance(70))
    .force('charge',d3.forceManyBody().strength(-150))
    .force('center',d3.forceCenter(w/2,h/2))
    .force('collision',d3.forceCollide().radius(function(d) { return d.r+8; }))
    .on('tick',function(){
      gLinks.attr('x1',function(d){return d.source.x;}).attr('y1',function(d){return d.source.y;}).attr('x2',function(d){return d.target.x;}).attr('y2',function(d){return d.target.y;});
      gLinkLabels.attr('x',function(d){return (d.source.x+d.target.x)/2;}).attr('y',function(d){return (d.source.y+d.target.y)/2;});
      gNodes.attr('transform',function(d){return 'translate('+d.x+','+d.y+')';});
    });
}

function resetNet() { if(svg) svg.transition().duration(500).call(d3.zoom().transform, d3.zoomIdentity); }

function toggleNetLabels() {
  showNetLabels = !showNetLabels;
  if(gNodes) gNodes.selectAll('text').attr('opacity', showNetLabels ? 1 : 0);
  if(gLinkLabels) gLinkLabels.attr('opacity', showNetLabels ? 1 : 0);
}

function renderCloud(data) {
  const wrap = document.getElementById('cloudWrap');
  const sorted = data.stocks.filter(function(s) { return s.heat_score > 0.05; }).sort(function(a,b) { return (b.heat_score||0) - (a.heat_score||0); });
  const max = Math.max.apply(null, sorted.map(function(s) { return s.heat_score||0; })) || 0.1;
  const colors = data.sector_colors || {};
  wrap.innerHTML = sorted.map(function(s) {
    const size = 0.65 + (s.heat_score||0)/max*1.5;
    const c = colors[s.sector] || '#58a6ff';
    return '<span class="cloud-tag" style="font-size:'+size+'em;background:'+c+'22;color:'+c+';border:1px solid '+c+'44" onclick="showDetail(\''+s.ticker+'\')">'+s.ticker+'</span>';
  }).join('');
}

function renderSectors(data) {
  const wrap = document.getElementById('sectorWrap');
  const sm = data.sector_summary || {};
  const cols = data.sector_colors || {};
  const ig = data.industry_groups || {};
  const maxScore = Math.max.apply(null, Object.values(sm).map(function(s) { return s.total_score; })) || 1;
  
  wrap.innerHTML = Object.keys(sm).sort(function(a,b) { return sm[b].total_score - sm[a].total_score; }).map(function(sec) {
    const info = sm[sec];
    const c = cols[sec] || '#58a6ff';
    const pct = info.total_score / maxScore * 100;
    return '<div class="sector-row"><div class="sr-n" style="color:'+c+'"><strong>'+sec+'</strong></div><div class="sr-bar"><div class="sr-fill" style="width:'+pct+'%;background:'+c+'"></div></div><div class="sr-c">'+info.count+'支</div></div>';
  }).join('');
  
  wrap.innerHTML += '<br><div style="font-size:0.78em;color:#8b949e;margin-top:8px;padding:8px;border-left:2px solid #30363d">'
    + Object.keys(ig).map(function(k) { return '<div style="margin:3px 0"><strong>'+k+'</strong>: '+ig[k]+'</div>'; }).join('') + '</div>';
}

// ========== OVERLAP ==========
function renderOverlap() {
  if (!overlapData) return;
  document.getElementById('overlapDesc').innerHTML = '两个来源<b>共同关注的股票</b>：' + overlapData.source1_label + ' ↔ ' + overlapData.source2_label;
  
  document.getElementById('overlapLegend').innerHTML = '<span class="legend-item"><span class="dot" style="background:'+overlapData.color1+'"></span> '+overlapData.source1_label+'</span>'
    + '<span class="legend-item"><span class="dot" style="background:'+overlapData.color2+'"></span> '+overlapData.source2_label+'</span>';
  
  const sorted = overlapData.stocks.slice().sort(function(a,b) { return b.total_score - a.total_score; });
  document.getElementById('overlapGrid').innerHTML = sorted.map(function(s) {
    const h1 = Math.min(s.heat_score_0 * 100, 100);
    const h2 = Math.min(s.heat_score_1 * 100, 100);
    return '<div class="overlap-card" onclick="showOverlapDetail(\''+s.ticker+'\')">'
      + '<div style="display:flex;justify-content:space-between;align-items:center">'
      + '<span class="heat-card-ticker" style="color:#F59E0B">'+s.ticker+'</span>'
      + '<span style="font-size:0.7em;color:#8b949e">🔥 '+s.total_score.toFixed(2)+'</span></div>'
      + '<div class="heat-card-name">'+s.name+'</div>'
      + '<div class="overlap-scores">'
      + '<div style="flex:1"><div class="os" style="width:100%;background:#21262d"><div style="width:'+h1+'%;height:100%;background:'+overlapData.color1+';border-radius:3px"></div></div><div class="olabel">来源1</div></div>'
      + '<div style="flex:1"><div class="os" style="width:100%;background:#21262d"><div style="width:'+h2+'%;height:100%;background:'+overlapData.color2+';border-radius:3px"></div></div><div class="olabel">来源2</div></div>'
      + '</div></div>';
  }).join('');
}

// ========== DETAIL MODAL ==========
function showDetail(ticker) {
  const data = sourceData[currentSource];
  if (!data) return;
  const s = data.stocks.find(function(x) { return x.ticker === ticker; });
  if (!s) return;
  
  const colors = data.sector_colors || {};
  document.getElementById('modalTicker').textContent = s.ticker;
  document.getElementById('modalTicker').style.color = colors[s.sector] || '#58a6ff';
  document.getElementById('modalSector').textContent = s.sector + ' > ' + s.industry + ' > ' + s.sub_industry;
  document.getElementById('modalDesc').textContent = s.desc || '';
  
  const rels = data.relations.filter(function(r) { return r.source === ticker || r.target === ticker; });
  const relEl = document.getElementById('modalRelations');
  if (rels.length) {
    relEl.innerHTML = '<div style="font-size:0.82em;margin:8px 0 4px;color:#58a6ff">行业关联</div>'
      + rels.map(function(r) {
        const isSource = r.source === ticker;
        const other = isSource ? r.target : r.source;
        const symb = r.type==='supplier'?'→':r.type==='customer'?'←':r.type==='foundry'?'⇒':'↔';
        return '<div style="font-size:0.75em;color:#8b949e;padding:2px 0">'+symb+' '+other+' — '+r.label+'</div>';
      }).join('');
  } else {
    relEl.innerHTML = '';
  }
  
  var tweets = s.recent_tweets || [];
  var twEl = document.getElementById('modalTweets');
  twEl.innerHTML = tweets.length
    ? '<div style="font-size:0.82em;margin:8px 0 4px;color:#58a6ff">相关推文</div>'
      + tweets.map(function(t) { return '<div style="font-size:0.72em;color:#8b949e;padding:3px 0;border-top:1px solid #21262d">'+t.text.substring(0,150)+'...</div>'; }).join('')
    : '';
  
  document.getElementById('modalSource').textContent = '📡 来源: ' + data.source_label;
  document.getElementById('detailModal').classList.add('show');
}

function showOverlapDetail(ticker) {
  if (!overlapData) return;
  const s = overlapData.stocks.find(function(x) { return x.ticker === ticker; });
  if (!s) return;
  
  document.getElementById('modalTicker').textContent = s.ticker;
  document.getElementById('modalTicker').style.color = '#F59E0B';
  document.getElementById('modalSector').textContent = '共同关注 · 两个来源均提及';
  document.getElementById('modalDesc').textContent = s.desc || '';
  
  const rels = overlapData.relations.filter(function(r) { return r.source === ticker || r.target === ticker; });
  const relEl = document.getElementById('modalRelations');
  relEl.innerHTML = rels.length
    ? '<div style="font-size:0.82em;margin:8px 0 4px;color:#F59E0B">行业关联</div>'
      + rels.map(function(r) {
        const isSource = r.source === ticker;
        const other = isSource ? r.target : r.source;
        return '<div style="font-size:0.72em;color:#8b949e;padding:2px 0">↔ '+other+' — '+r.label+'</div>';
      }).join('')
    : '';
  
  document.getElementById('modalTweets').innerHTML = '<div style="font-size:0.78em;margin-top:8px;color:#8b949e">'
    + '<div><span class="dot" style="background:'+overlapData.color1+'"></span> 来源1: 🔥 '+s.heat_score_0+'</div>'
    + '<div style="margin-top:4px"><span class="dot" style="background:'+overlapData.color2+'"></span> 来源2: 🔥 '+s.heat_score_1+'</div></div>';
  document.getElementById('modalSource').textContent = '📡 两者共同关注';
  document.getElementById('detailModal').classList.add('show');
}

function closeModal() { document.getElementById('detailModal').classList.remove('show'); }
document.getElementById('detailModal').addEventListener('click', function(e) { if (e.target === this) closeModal(); });

// ========== INIT ==========
function startApp() { init(); }
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', startApp);
} else {
  startApp();
}
