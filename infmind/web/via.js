/* ∞Mind — L2 可視化 / VIA 24の強み
   環：24の強みを徳性ごとに並べ、活性の強さで灯す。
   2因子：理性⇄感情 × 個人内⇄個人間 に散らし、重心を置く。 */

const TAU = Math.PI * 2;

function fit(canvas, cssH) {
  const r = canvas.getBoundingClientRect();
  if (!r.width) return null;
  const dpr = Math.min(window.devicePixelRatio || 1, 2);
  const h = cssH || r.width;
  canvas.style.height = h + 'px';
  canvas.width = Math.round(r.width * dpr);
  canvas.height = Math.round(h * dpr);
  const ctx = canvas.getContext('2d');
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx.clearRect(0, 0, r.width, h);
  return { ctx, W: r.width, H: h };
}

function rgbOf(hex) {
  let h = hex.replace('#', '');
  if (h.length === 3) h = h[0] + h[0] + h[1] + h[1] + h[2] + h[2];
  const n = parseInt(h, 16);
  return `${(n >> 16) & 255},${(n >> 8) & 255},${n & 255}`;
}

/* ── 24の強みの環 ───────────────────────────────────────────── */
export function drawRing(canvas, catalog, profile, hot) {
  const f = fit(canvas, canvas.getBoundingClientRect().width);
  if (!f) return [];
  const { ctx, W, H } = f;
  const cx = W / 2, cy = H / 2;
  const R = Math.min(W, H) * 0.365;

  const score = new Map((profile || []).map(p => [p.jp, p.normalized]));
  const vcolor = new Map((catalog.virtues || []).map(v => [v.key, v.color]));

  // 徳性ごとに固まるよう並べ替える
  const order = (catalog.virtues || []).map(v => v.key);
  const list = [...(catalog.strengths || [])].sort(
    (a, b) => order.indexOf(a.virtue) - order.indexOf(b.virtue)
  );
  if (!list.length) return [];

  // 徳性の弧
  ctx.lineWidth = 1;
  let i0 = 0;
  for (const vk of order) {
    const n = list.filter(s => s.virtue === vk).length;
    if (!n) continue;
    const a0 = (i0 / list.length) * TAU - Math.PI / 2 - 0.045;
    const a1 = ((i0 + n) / list.length) * TAU - Math.PI / 2 - 0.045;
    ctx.strokeStyle = `rgba(${rgbOf(vcolor.get(vk) || '#c9a227')},.26)`;
    ctx.beginPath();
    ctx.arc(cx, cy, R + 20, a0 + 0.035, a1 - 0.035);
    ctx.stroke();
    i0 += n;
  }

  // 内円
  ctx.strokeStyle = 'rgba(201,162,39,.12)';
  ctx.beginPath(); ctx.arc(cx, cy, R * 0.44, 0, TAU); ctx.stroke();

  const hits = [];
  list.forEach((s, i) => {
    const ang = (i / list.length) * TAU - Math.PI / 2;
    const v = score.get(s.jp) || 0;
    const col = vcolor.get(s.virtue) || '#c9a227';
    const x = cx + Math.cos(ang) * R, y = cy + Math.sin(ang) * R;
    const isHot = hot === s.jp;

    // 中心から伸びる糸（活性の強さ）
    ctx.strokeStyle = `rgba(${rgbOf(col)},${(0.06 + v * 0.34).toFixed(3)})`;
    ctx.lineWidth = isHot ? 1.3 : 0.6;
    ctx.beginPath();
    ctx.moveTo(cx + Math.cos(ang) * R * 0.44, cy + Math.sin(ang) * R * 0.44);
    ctx.lineTo(x, y);
    ctx.stroke();

    // 灯
    const rad = 2.4 + v * 6.4 + (isHot ? 2.4 : 0);
    const g = ctx.createRadialGradient(x, y, 0, x, y, rad * 3.4);
    g.addColorStop(0, `rgba(${rgbOf(col)},${(0.34 + v * 0.5).toFixed(3)})`);
    g.addColorStop(1, `rgba(${rgbOf(col)},0)`);
    ctx.fillStyle = g;
    ctx.beginPath(); ctx.arc(x, y, rad * 3.4, 0, TAU); ctx.fill();
    ctx.fillStyle = `rgba(${rgbOf(col)},${(0.5 + v * 0.5).toFixed(3)})`;
    ctx.beginPath(); ctx.arc(x, y, rad, 0, TAU); ctx.fill();

    // 紋（一文字）
    const lx = cx + Math.cos(ang) * (R + 38), ly = cy + Math.sin(ang) * (R + 38);
    ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    ctx.font = `${isHot ? 16 : 14}px "Hiragino Mincho ProN","Yu Mincho","Noto Serif JP",serif`;
    ctx.fillStyle = `rgba(${rgbOf(col)},${(0.42 + v * 0.58).toFixed(3)})`;
    ctx.fillText(s.key, lx, ly);

    hits.push({ x: lx, y: ly, r: 15, jp: s.jp });
    hits.push({ x, y, r: Math.max(9, rad * 2), jp: s.jp });
  });

  return hits;
}

/* ── 2因子バランスマップ ────────────────────────────────────── */
export function drawFactor(canvas, catalog, profile, balance, hot) {
  const f = fit(canvas, Math.min(canvas.getBoundingClientRect().width, 330));
  if (!f) return [];
  const { ctx, W, H } = f;
  // 2つの軸は同じ尺度で読ませたいので、中央に正方形の作図域を取る
  const pad = 30;
  const side = Math.min(W, H) - pad * 2;
  const ox = (W - side) / 2, oy = (H - side) / 2;
  const px = v => ox + ((v + 1) / 2) * side;
  const py = v => oy + ((1 - v) / 2) * side;

  // 四分割
  ctx.strokeStyle = 'rgba(230,225,214,.08)';
  ctx.lineWidth = 0.6;
  ctx.beginPath();
  ctx.moveTo(ox - 8, py(0)); ctx.lineTo(ox + side + 8, py(0));
  ctx.moveTo(px(0), oy - 8); ctx.lineTo(px(0), oy + side + 8);
  ctx.stroke();

  ctx.fillStyle = 'rgba(150,145,135,.5)';
  ctx.font = '8px "Helvetica Neue","Hiragino Sans",system-ui,sans-serif';
  ctx.textBaseline = 'middle';
  ctx.textAlign = 'left';   ctx.fillText('感情', ox - 24, py(0) - 9);
  ctx.textAlign = 'right';  ctx.fillText('理性', ox + side + 24, py(0) - 9);
  ctx.textAlign = 'center'; ctx.fillText('個人内', px(0), oy - 14);
  ctx.fillText('個人間', px(0), oy + side + 14);

  const score = new Map((profile || []).map(p => [p.jp, p.normalized]));
  const vcolor = new Map((catalog.virtues || []).map(v => [v.key, v.color]));
  const hits = [];

  for (const s of catalog.strengths || []) {
    const v = score.get(s.jp) || 0;
    const col = vcolor.get(s.virtue) || '#c9a227';
    const x = px(s.rational), y = py(s.intra);
    const isHot = hot === s.jp;
    const r = 2.2 + v * 4.6 + (isHot ? 2 : 0);
    ctx.fillStyle = `rgba(${rgbOf(col)},${(0.22 + v * 0.62).toFixed(3)})`;
    ctx.beginPath(); ctx.arc(x, y, r, 0, TAU); ctx.fill();
    if (isHot) {
      ctx.strokeStyle = 'rgba(232,200,106,.8)'; ctx.lineWidth = 1;
      ctx.beginPath(); ctx.arc(x, y, r + 4, 0, TAU); ctx.stroke();
      ctx.fillStyle = 'rgba(230,225,214,.85)';
      ctx.font = '9px "Hiragino Sans","Noto Sans JP",system-ui,sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText(s.jp, x, y - r - 9);
    }
    hits.push({ x, y, r: Math.max(8, r + 3), jp: s.jp });
  }

  // 重心
  if (balance) {
    const bx = px(balance.rational), by = py(balance.intra);
    const spread = Math.max(6, (balance.spread || 0) * side * 0.5);
    ctx.strokeStyle = 'rgba(201,162,39,.24)';
    ctx.setLineDash([2, 3]); ctx.lineWidth = 0.8;
    ctx.beginPath(); ctx.arc(bx, by, spread, 0, TAU); ctx.stroke();
    ctx.setLineDash([]);
    ctx.strokeStyle = 'rgba(232,200,106,.9)'; ctx.lineWidth = 1.1;
    ctx.beginPath();
    ctx.moveTo(bx - 6, by); ctx.lineTo(bx + 6, by);
    ctx.moveTo(bx, by - 6); ctx.lineTo(bx, by + 6);
    ctx.stroke();
  }
  return hits;
}

export function bindHits(canvas, getHits, onPick) {
  function pick(ev) {
    const r = canvas.getBoundingClientRect();
    const x = ev.clientX - r.left, y = ev.clientY - r.top;
    let best = null, bd = Infinity;
    for (const h of getHits() || []) {
      const d = Math.hypot(h.x - x, h.y - y);
      if (d < h.r && d < bd) { bd = d; best = h.jp; }
    }
    onPick(best);
  }
  canvas.addEventListener('mousemove', pick);
  canvas.addEventListener('mouseleave', () => onPick(null));
  canvas.addEventListener('click', pick);
}
