/* ∞Mind — 4層を繋ぐ ↻
   入力(対話) → 可視化(脳ゾーン+VIA) → 分析(分析マップ) → 統合(第二の脳) → 入力… */

import { createBrain } from '/brain.js';
import { drawRing, drawFactor, bindHits } from '/via.js';

const $ = id => document.getElementById(id);
const esc = s => String(s).replace(/[&<>]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' }[c]));

let STATE = null;
let catalog = { virtues: [], strengths: [] };
let hot = null;
let ringHits = [], factorHits = [];
let brain = null;
let busy = false;

/* ── API ────────────────────────────────────────────────────── */
async function api(path, opts = {}) {
  const res = await fetch('/api' + path, {
    headers: { 'Content-Type': 'application/json' },
    ...opts,
  });
  const body = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(body.detail || `${res.status} ${res.statusText}`);
  return body;
}

/* ── 壱 入力 ────────────────────────────────────────────────── */
function addMsg(role, text, zone) {
  const log = $('chatLog');
  const who = role === 'user' ? 'You' : role === 'mind' ? '∞Mind' : 'System';
  const mark = zone
    ? `<span class="zone-mark" style="color:${zone.color};border:1px solid ${zone.color}44">${zone.jp}</span>`
    : '';
  const el = document.createElement('div');
  el.className = `msg ${role} fade`;
  el.innerHTML = `<div class="who">${who}${mark}</div><div class="body">${esc(text)}</div>`;
  log.appendChild(el);
  log.scrollTop = log.scrollHeight;
  return el;
}

async function send() {
  const input = $('chatInput');
  const text = input.value.trim();
  if (!text || busy) return;
  busy = true;
  input.value = '';
  $('sendBtn').disabled = true;
  addMsg('user', text);

  const online = STATE && STATE.online;
  const pending = addMsg('mind', online ? '…' : '刻んでいます…');

  try {
    if (online) {
      const r = await api('/chat', { method: 'POST', body: JSON.stringify({ message: text }) });
      pending.querySelector('.body').textContent = r.reply;
      const z = zoneOf(r.entry.zone);
      if (z) pending.querySelector('.who').innerHTML +=
        `<span class="zone-mark" style="color:${z.color};border:1px solid ${z.color}44">${z.jp}</span>`;
      STATE.analysis = r.analysis;
      render();
    } else {
      const r = await api('/observe', { method: 'POST', body: JSON.stringify({ text }) });
      const z = zoneOf(r.entry.zone);
      pending.remove();
      addMsg('sys',
        `「${z ? z.jp : r.entry.zone}」ゾーンに刻みました。` +
        (r.entry.concepts.length ? ` 概念: ${r.entry.concepts.slice(0, 5).join('、')}` : ''));
      STATE.analysis = r.analysis;
      render();
    }
  } catch (e) {
    pending.remove();
    addMsg('sys', '届きませんでした — ' + e.message);
  } finally {
    busy = false;
    $('sendBtn').disabled = false;
    input.focus();
  }
}

/* ── 弐 可視化 ──────────────────────────────────────────────── */
const zoneOf = key => (STATE?.zones || []).find(z => z.key === key);

function renderZones(a) {
  $('zoneList').innerHTML = [...a.zone_distribution]
    .sort((x, y) => y.share - x.share)
    .map(d => `
      <div class="zone-row">
        <div class="top">
          <span class="jp" style="color:${d.color}">${d.jp}</span>
          <span class="pct">${(d.share * 100).toFixed(1)}%</span>
        </div>
        <div class="en">${d.region_en}</div>
        <div class="track"><div class="fill" style="background:${d.color}"></div></div>
      </div>`).join('');
  requestAnimationFrame(() => {
    const sorted = [...a.zone_distribution].sort((x, y) => y.share - x.share);
    const peak = sorted[0]?.share || 1;
    document.querySelectorAll('#zoneList .fill').forEach((el, i) => {
      el.style.width = `${Math.min(100, (sorted[i].share / peak) * 100)}%`;
    });
  });
}

function renderVia(a) {
  ringHits = drawRing($('viaRing'), catalog, a.strength_profile, hot);
  factorHits = drawFactor($('factorMap'), catalog, a.strength_profile, a.balance, hot);

  const vcol = new Map(catalog.virtues.map(v => [v.key, v.color]));
  $('strengthRows').innerHTML = a.strength_profile.slice(0, 8).map(s => {
    const c = vcol.get(s.virtue) || '#c9a227';
    return `
      <div class="srow" data-jp="${esc(s.jp)}">
        <span class="glyph" style="color:${c}">${s.key}</span>
        <div class="meta">
          <div class="nm">${esc(s.jp)}</div>
          <div class="track"><div class="fill" style="background:${c}"></div></div>
        </div>
        <span class="val">${(s.normalized * 100).toFixed(0)}</span>
      </div>`;
  }).join('');
  requestAnimationFrame(() => {
    document.querySelectorAll('#strengthRows .fill').forEach((el, i) => {
      el.style.width = `${(a.strength_profile[i].normalized * 100).toFixed(1)}%`;
    });
  });
}

/* ── 参 分析 ────────────────────────────────────────────────── */
function renderAnalysis(a) {
  $('virtueRows').innerHTML = a.virtue_profile.map(v => `
    <div class="vrow">
      <div class="top">
        <span class="jp" style="color:${v.color}">${v.jp}</span>
        <span class="en">${v.en}</span>
      </div>
      <div class="track"><div class="fill" style="background:${v.color}"></div></div>
    </div>`).join('');
  requestAnimationFrame(() => {
    document.querySelectorAll('#virtueRows .fill').forEach((el, i) => {
      el.style.width = `${(a.virtue_profile[i].normalized * 100).toFixed(1)}%`;
    });
  });

  $('tendencyList').innerHTML = a.tendencies.map(t => `<li>${esc(t)}</li>`).join('');

  $('conceptCloud').innerHTML = a.top_concepts.slice(0, 30).map(c =>
    `<span style="border-color:${c.color}33;color:${c.color}">${esc(c.id)}<i>${c.weight}</i></span>`
  ).join('') || '<span style="border-color:transparent;color:var(--washi-far)">まだありません</span>';

  const d = a.depth;
  $('depthPct').textContent = `${Math.round(d.overall * 100)}%`;
  $('depthArc').setAttribute('stroke-dasharray', `${(d.overall * 201).toFixed(1)} 201`);
  $('depthBars').innerHTML = [
    ['量', 'volume'], ['広さ', 'breadth'],
    ['強みの覆い', 'strength_coverage'], ['継続', 'continuity'],
  ].map(([label, k]) => `
    <div class="dbar">
      <div class="top"><span>${label}</span><i>${Math.round(d[k] * 100)}%</i></div>
      <div class="track"><div class="fill" data-w="${d[k]}"></div></div>
    </div>`).join('');
  requestAnimationFrame(() => {
    document.querySelectorAll('#depthBars .fill').forEach(el => {
      el.style.width = `${(parseFloat(el.dataset.w) * 100).toFixed(1)}%`;
    });
  });
}

/* ── 全体 ───────────────────────────────────────────────────── */
function render() {
  const a = STATE.analysis;
  $('s-entries').textContent = String(a.entries).padStart(3, '0');
  $('s-concepts').textContent = String(a.concepts).padStart(3, '0');
  $('s-depth').textContent = `${Math.round(a.depth.overall * 100)}%`;
  $('s-dot').className = 'dot' + (STATE.online ? ' on' : '');
  $('s-link').textContent = STATE.online ? 'CLAUDE LIVE' : 'OFFLINE';

  $('chatNote').innerHTML = STATE.online
    ? '対話するたび、発話は脳ゾーンへ刻まれ、24の強みと分析マップが更新されます。'
    : '<b>Claude 未接続</b> — 送った言葉は辞書ベースで解析され、脳ゾーンと分析マップには反映されます。'
      + '対話を有効にするには <code>ANTHROPIC_API_KEY</code> を設定して再起動してください。';

  renderZones(a);
  renderVia(a);
  renderAnalysis(a);
  if (brain) brain.setData(STATE);
}

/* ── 強みの詳細 ─────────────────────────────────────────────── */
function openSheet(jp) {
  const s = catalog.strengths.find(x => x.jp === jp);
  if (!s) return;
  const v = catalog.virtues.find(x => x.key === s.virtue);
  const z = zoneOf(s.zone);
  const score = STATE.analysis.strength_profile.find(x => x.jp === jp);
  $('sheetGlyph').textContent = s.key;
  $('sheetGlyph').style.color = v ? v.color : '#c9a227';
  $('sheetName').textContent = s.jp;
  $('sheetEn').textContent = s.en;
  $('sheetTags').innerHTML = [
    v ? `<span style="color:${v.color};border-color:${v.color}33">${v.jp} / ${v.en}</span>` : '',
    z ? `<span style="color:${z.color};border-color:${z.color}33">${z.jp} / ${z.region_en}</span>` : '',
    score ? `<span>活性 ${(score.normalized * 100).toFixed(0)}</span>` : '',
    ...s.related.map(r => `<span>${esc(r)}</span>`),
  ].join('');
  $('sheetDef').textContent = s.definition;
  $('sheetUnder').textContent = s.under;
  $('sheetOver').textContent = s.over;
  $('sheet').classList.add('open');
}

function setHot(jp) {
  if (hot === jp) return;
  hot = jp;
  const a = STATE?.analysis;
  if (a) renderVia(a);
}

/* ── 肆 統合 ────────────────────────────────────────────────── */
function paintSynthesis(text) {
  const html = esc(text)
    .split(/\n{2,}/)
    .map(p => `<p>${p.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>').replace(/\n/g, '<br>')}</p>`)
    .join('');
  $('synthBody').className = 'synth-body fade';
  $('synthBody').innerHTML = html;
}

async function synthesize() {
  const btn = $('synthBtn');
  btn.disabled = true;
  const prev = btn.textContent;
  btn.textContent = '統合中…';
  try {
    const r = await api('/synthesize', { method: 'POST' });
    paintSynthesis(r.synthesis);
  } catch (e) {
    $('synthBody').className = 'synth-empty';
    $('synthBody').textContent = '統合できませんでした — ' + e.message;
  } finally {
    btn.disabled = false;
    btn.textContent = prev;
  }
}

/* ── 起動 ───────────────────────────────────────────────────── */
async function boot() {
  brain = createBrain($('brain'), { points: 5200 });

  try {
    STATE = await api('/state');
  } catch (e) {
    addMsg('sys', 'サーバに届きませんでした — ' + e.message);
    return;
  }
  catalog = STATE.via;
  render();

  $('synthBody').className = 'synth-empty';
  $('synthBody').textContent = STATE.online
    ? '分析マップの数字を踏まえ、いま灯っているところ・そこから見える軸・まだ暗いところを書き起こします。'
    : '統合には Claude への接続が必要です。ANTHROPIC_API_KEY を設定して再起動してください。'
      + '「分析マップを開く」は接続なしで使えます。';

  try {
    const g = await api('/greeting');
    addMsg('mind', g.greeting);
  } catch { /* 挨拶は無くても動く */ }

  // 操作
  $('sendBtn').onclick = send;
  $('chatInput').addEventListener('keydown', e => { if (e.key === 'Enter') send(); });
  $('synthBtn').onclick = synthesize;

  $('reportBtn').onclick = async () => {
    try {
      const r = await api('/report');
      $('synthBody').className = 'synth-body fade';
      $('synthBody').innerHTML =
        `<pre style="font-family:var(--mono);font-size:11px;line-height:1.75;white-space:pre-wrap;margin:0;color:var(--washi-dim)">${esc(r.report)}</pre>`;
    } catch (e) { alert(e.message); }
  };

  $('resetBtn').onclick = async () => {
    if (!confirm('刻まれた記憶をすべて消します。元に戻せません。')) return;
    try {
      const r = await api('/brain', { method: 'DELETE' });
      STATE.analysis = r.analysis;
      $('chatLog').innerHTML = '';
      addMsg('sys', '脳を消しました。ここからまた刻んでいけます。');
      $('synthBody').className = 'synth-empty';
      $('synthBody').textContent = 'まだ統合するものがありません。';
      render();
    } catch (e) { alert(e.message); }
  };

  document.querySelectorAll('.stage-ctl button').forEach(b => {
    b.onclick = () => {
      const act = b.dataset.act;
      if (act === 'auto' || act === 'links') {
        b.classList.toggle('on');
        const on = b.classList.contains('on');
        act === 'auto' ? brain.setAuto(on) : brain.setLinks(on);
      } else {
        brain.view(act);
        const auto = document.querySelector('[data-act="auto"]');
        auto.classList.remove('on');
      }
    };
  });

  bindHits($('viaRing'), () => ringHits, jp => { setHot(jp); });
  bindHits($('factorMap'), () => factorHits, jp => { setHot(jp); });
  $('viaRing').addEventListener('click', () => { if (hot) openSheet(hot); });
  $('factorMap').addEventListener('click', () => { if (hot) openSheet(hot); });
  $('strengthRows').addEventListener('click', e => {
    const row = e.target.closest('.srow');
    if (row) openSheet(row.dataset.jp);
  });

  const closeSheet = () => $('sheet').classList.remove('open');
  $('sheetClose').onclick = closeSheet;
  $('sheet').addEventListener('click', e => { if (e.target === $('sheet')) closeSheet(); });
  document.addEventListener('keydown', e => { if (e.key === 'Escape') closeSheet(); });

  // ↻ レールの現在地
  const obs = new IntersectionObserver(es => {
    for (const en of es) {
      if (en.isIntersecting) {
        document.querySelectorAll('.loop-rail a').forEach(a =>
          a.classList.toggle('active', a.dataset.layer === en.target.id));
      }
    }
  }, { rootMargin: '-45% 0px -45% 0px' });
  document.querySelectorAll('main section').forEach(s => obs.observe(s));

  let rt = null;
  window.addEventListener('resize', () => {
    clearTimeout(rt);
    rt = setTimeout(() => { if (STATE) renderVia(STATE.analysis); }, 160);
  });
  $('chatInput').focus();
}

boot();
