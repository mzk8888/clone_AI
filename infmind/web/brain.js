/* ∞Mind — L2 可視化 / 脳ゾーンマップ
   点群で脳の形を作り、6つのゾーンを灯す。走る光は概念どうしの結び。 */

export function createBrain(canvas, opts = {}) {
  const ctx = canvas.getContext('2d');
  let W = 0, H = 0, dpr = 1;

  let zones = [];          // {key, jp, en, color, anchor:[x,y,z], share}
  let nodes = [];          // 概念ノード {id, weight, zone, p:[x,y,z]}
  let edges = [];          // [i, j]
  let cloud = [];          // 脳の形をつくる点群

  let yaw = -0.62, pitch = 0.2, autoRotate = true, showLinks = true;
  let dragging = false, lastX = 0, lastY = 0;
  let pulses = [], raf = null, t0 = performance.now();
  const rgbCache = new Map();

  // ── 脳の外形 ─────────────────────────────────────────────────
  // 球面をパラメータで走査し、半径を脳の形へ変形させる（皮質のしわ込み）。
  // 棄却サンプリングより形が安定して読める。
  function cerebrumRadius(u, v) {
    // u: 0..2π（前後〜側方）, v: 0..π（上〜下）
    const gyri =
      0.052 * Math.sin(7 * u) * Math.sin(5 * v) +
      0.034 * Math.sin(12 * u + 1.3) * Math.sin(8 * v + 0.6) +
      0.022 * Math.cos(5 * u - 1.1) * Math.cos(11 * v + 2.0);
    return 1 + gyri;
  }

  function cerebrumPoint(u, v) {
    const r = cerebrumRadius(u, v);
    const sv = Math.sin(v), cv = Math.cos(v);
    let x = 1.16 * r * sv * Math.cos(u);
    let y = 0.80 * r * cv + 0.10;
    let z = 0.70 * r * sv * Math.sin(u);
    // 前頭極をわずかに落とし、後頭極を張り出させる（横顔の輪郭）
    x += 0.06 * Math.sin(v) * (x > 0 ? -1 : 1.25);
    // 下面を平らに（脳梁より下は空ける）
    if (y < -0.30) y = -0.30 + (y + 0.30) * 0.34;
    return [x, y, z];
  }

  function cerebellumPoint(u, v) {
    const folia = 0.05 * Math.sin(22 * v) + 0.03 * Math.sin(15 * u);
    const r = 1 + folia;
    const sv = Math.sin(v);
    return [
      -0.74 + 0.32 * r * sv * Math.cos(u),
      -0.46 + 0.21 * r * Math.cos(v),
      0.38 * r * sv * Math.sin(u),
    ];
  }

  function stemPoint(t, a) {
    const taper = 0.115 - 0.045 * t;
    return [
      -0.27 - 0.07 * t + taper * Math.cos(a),
      -0.26 - 0.62 * t,
      taper * 0.92 * Math.sin(a),
    ];
  }

  function buildCloud(count) {
    const pts = [];
    const push = (p) => pts.push({
      x: p[0], y: p[1], z: p[2],
      zone: nearestZone(p[0], p[1], p[2]),
      tw: Math.random() * Math.PI * 2,
    });
    const cere = Math.round(count * 0.76);
    for (let i = 0; i < cere; i++) {
      // 球面上に一様分布させる（v は cos で取る）
      const u = Math.random() * Math.PI * 2;
      const v = Math.acos(1 - 2 * Math.random());
      push(cerebrumPoint(u, v));
    }
    const cb = Math.round(count * 0.16);
    for (let i = 0; i < cb; i++) {
      const u = Math.random() * Math.PI * 2;
      const v = Math.acos(1 - 2 * Math.random());
      push(cerebellumPoint(u, v));
    }
    const st = count - cere - cb;
    for (let i = 0; i < st; i++) {
      push(stemPoint(Math.random(), Math.random() * Math.PI * 2));
    }
    return pts;
  }

  function nearestZone(x, y, z) {
    let best = null, bd = Infinity;
    for (const zn of zones) {
      const [ax, ay, az] = zn.anchor;
      const d = (x - ax) ** 2 + (y - ay) ** 2 + (z - Math.abs(az)) ** 2;
      if (d < bd) { bd = d; best = zn.key; }
    }
    return best;
  }

  // ── 概念ノードを、属するゾーンの周りに散らす ──────────────────
  function placeNodes(list) {
    const byZone = new Map();
    for (const n of list) {
      if (!byZone.has(n.zone)) byZone.set(n.zone, []);
      byZone.get(n.zone).push(n);
    }
    const out = [];
    const GOLDEN = Math.PI * (3 - Math.sqrt(5));
    for (const [zkey, group] of byZone) {
      const zn = zones.find(z => z.key === zkey) || zones[0];
      if (!zn) continue;
      const [ax, ay, az] = zn.anchor;
      group.forEach((n, i) => {
        const k = i + 0.5, R = 0.17 * Math.sqrt(k / group.length) + 0.05;
        const th = GOLDEN * i, ph = Math.acos(1 - 2 * (k / Math.max(group.length, 1)));
        out.push({
          ...n,
          p: [
            ax + R * Math.sin(ph) * Math.cos(th),
            ay + R * Math.sin(ph) * Math.sin(th),
            az + R * Math.cos(ph) * 0.8,
          ],
          color: zn.color,
        });
      });
    }
    return out;
  }

  function buildEdges(links, placed) {
    const idx = new Map(placed.map((n, i) => [n.id, i]));
    const out = [];
    for (const l of links) {
      const a = idx.get(l.source), b = idx.get(l.target);
      if (a === undefined || b === undefined) continue;
      const pa = placed[a].p, pb = placed[b].p;
      const d = Math.hypot(pa[0] - pb[0], pa[1] - pb[1], pa[2] - pb[2]);
      if (d > 0.95) continue;   // 脳をまたぐ長い線は形を壊すので描かない
      out.push([a, b, l.weight || 1]);
    }
    return out;
  }

  // ── 射影 ──────────────────────────────────────────────────────
  function project(x, y, z) {
    const cy = Math.cos(yaw), sy = Math.sin(yaw);
    const cp = Math.cos(pitch), sp = Math.sin(pitch);
    const x1 = x * cy - z * sy, z1 = x * sy + z * cy;
    const y1 = y * cp - z1 * sp, z2 = y * sp + z1 * cp;
    const scale = Math.min(W, H) * 0.42;
    const persp = 2.7 / (2.7 + z2);
    return [W / 2 + x1 * scale * persp, H / 2 - y1 * scale * persp, z2, persp];
  }

  function rgb(hex) {
    let v = rgbCache.get(hex);
    if (!v) {
      let h = hex.replace('#', '');
      if (h.length === 3) h = h[0] + h[0] + h[1] + h[1] + h[2] + h[2];
      const n = parseInt(h, 16);
      v = `${(n >> 16) & 255},${(n >> 8) & 255},${n & 255}`;
      rgbCache.set(hex, v);
    }
    return v;
  }

  // ── 描画 ──────────────────────────────────────────────────────
  function frame(now) {
    raf = requestAnimationFrame(frame);
    const t = (now - t0) / 1000;
    if (autoRotate && !dragging) yaw += 0.0022;

    ctx.clearRect(0, 0, W, H);
    if (!W || !H) return;

    const zoneMap = new Map(zones.map(z => [z.key, z]));
    const glow = new Map(zones.map(z => [z.key, 0.34 + (z.share || 0) * 2.0]));

    // 点群
    const drawn = [];
    for (const p of cloud) {
      const [sx, sy, z2, ps] = project(p.x, p.y, p.z);
      const zn = zoneMap.get(p.zone);
      const depth = Math.max(0.12, Math.min(1, (1.35 - z2) / 2.0));
      const tw = 0.55 + 0.45 * Math.sin(t * 1.2 + p.tw);
      const a = Math.min(0.92, depth * 0.95 * tw * (glow.get(p.zone) || 0.35));
      if (a < 0.02) continue;
      drawn.push([sx, sy, ps, a, zn ? zn.color : '#666']);
    }
    drawn.sort((a, b) => a[2] - b[2]);
    for (const [sx, sy, ps, a, color] of drawn) {
      ctx.fillStyle = `rgba(${rgb(color)},${a.toFixed(3)})`;
      ctx.fillRect(sx, sy, Math.max(0.7, ps * 1.25), Math.max(0.7, ps * 1.25));
    }

    // 結び（シナプス）
    if (showLinks && edges.length) {
      ctx.lineWidth = 0.7;
      for (const [a, b, w] of edges) {
        const na = nodes[a], nb = nodes[b];
        const pa = project(...na.p), pb = project(...nb.p);
        ctx.strokeStyle = `rgba(201,162,39,${Math.min(0.3, 0.07 + w * 0.035).toFixed(3)})`;
        ctx.beginPath();
        ctx.moveTo(pa[0], pa[1]);
        ctx.lineTo(pb[0], pb[1]);
        ctx.stroke();
      }
    }

    // 走る光
    for (let i = pulses.length - 1; i >= 0; i--) {
      const pu = pulses[i];
      pu.t += pu.spd * 0.012;
      if (pu.t >= 1) { pulses.splice(i, 1); continue; }
      const e = edges[pu.e];
      if (!e) { pulses.splice(i, 1); continue; }
      const na = nodes[e[0]], nb = nodes[e[1]];
      const u = pu.dir > 0 ? pu.t : 1 - pu.t;
      const [sx, sy, , ps] = project(
        na.p[0] + (nb.p[0] - na.p[0]) * u,
        na.p[1] + (nb.p[1] - na.p[1]) * u,
        na.p[2] + (nb.p[2] - na.p[2]) * u,
      );
      const fade = Math.sin(pu.t * Math.PI);
      ctx.beginPath();
      ctx.arc(sx, sy, 1.5 * ps, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(232,200,106,${(0.85 * fade).toFixed(3)})`;
      ctx.fill();
      ctx.beginPath();
      ctx.arc(sx, sy, 5 * ps, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(232,200,106,${(0.1 * fade).toFixed(3)})`;
      ctx.fill();
    }
    if (edges.length && pulses.length < 14 && Math.random() < 0.09) {
      pulses.push({
        e: (Math.random() * edges.length) | 0, t: 0,
        dir: Math.random() < 0.5 ? 1 : -1, spd: 0.5 + Math.random() * 0.8,
      });
    }

    // ゾーンの核
    const labels = [];
    for (const zn of zones) {
      const [sx, sy, z2, ps] = project(zn.anchor[0], zn.anchor[1], zn.anchor[2]);
      const share = zn.share || 0;
      const r = (3.2 + share * 16) * ps;
      const breath = 0.74 + 0.26 * Math.sin(t * 0.85 + zn.anchor[0] * 3);
      const halo = Math.max(r * 5.5, 14);
      const g = ctx.createRadialGradient(sx, sy, 0, sx, sy, halo);
      g.addColorStop(0, `rgba(${rgb(zn.color)},${(0.62 * breath * (0.4 + share * 1.6)).toFixed(3)})`);
      g.addColorStop(0.45, `rgba(${rgb(zn.color)},${(0.16 * breath).toFixed(3)})`);
      g.addColorStop(1, `rgba(${rgb(zn.color)},0)`);
      ctx.fillStyle = g;
      ctx.beginPath(); ctx.arc(sx, sy, halo, 0, Math.PI * 2); ctx.fill();
      ctx.fillStyle = `rgba(255,255,255,${(0.45 + share * 0.5).toFixed(3)})`;
      ctx.beginPath(); ctx.arc(sx, sy, Math.max(1.3, r * 0.3), 0, Math.PI * 2); ctx.fill();
      ctx.fillStyle = `rgba(${rgb(zn.color)},${Math.min(1, 0.7 + share).toFixed(3)})`;
      ctx.beginPath(); ctx.arc(sx, sy, Math.max(2.2, r * 0.58), 0, Math.PI * 2); ctx.fill();
      labels.push({ kind: 'zone', sx, sy, z2, zn, share });
    }

    // 概念の核（銘は後で衝突を見て置く）
    const concepts = [];
    for (const n of nodes) {
      const [sx, sy, z2, ps] = project(...n.p);
      ctx.fillStyle = `rgba(${rgb(n.color)},${Math.min(0.8, 0.32 + n.weight * 0.1).toFixed(3)})`;
      ctx.beginPath(); ctx.arc(sx, sy, Math.max(1, 1.15 * ps), 0, Math.PI * 2); ctx.fill();
      concepts.push({ kind: 'concept', sx, sy, z2, n });
    }

    // 銘は重ならないものだけ描く（ゾーン優先 → 重い概念順）
    const boxes = [];
    const free = (x, y, w, h) => {
      for (const b of boxes) {
        if (Math.abs(x - b.x) < (w + b.w) / 2 && Math.abs(y - b.y) < (h + b.h) / 2) return false;
      }
      boxes.push({ x, y, w, h });
      return true;
    };
    ctx.textAlign = 'center';
    for (const L of labels.sort((a, b) => a.z2 - b.z2)) {
      const w = L.zn.jp.length * 12 + 10;
      if (!free(L.sx, L.sy - 20, w, 26)) continue;
      ctx.font = '11.5px "Hiragino Sans","Noto Sans JP",system-ui,sans-serif';
      ctx.fillStyle = `rgba(${rgb(L.zn.color)},${Math.min(1, 0.68 + L.share).toFixed(3)})`;
      ctx.fillText(L.zn.jp, L.sx, L.sy - 20);
      ctx.font = '7.5px "Helvetica Neue",system-ui,sans-serif';
      ctx.letterSpacing = '1.6px';
      ctx.fillStyle = 'rgba(160,155,145,.62)';
      ctx.fillText(L.zn.region_en, L.sx, L.sy - 10);
      ctx.letterSpacing = '0px';
    }
    ctx.font = '9.5px "Hiragino Sans","Noto Sans JP",system-ui,sans-serif';
    let placed = 0;
    for (const C of concepts.sort((a, b) => b.n.weight - a.n.weight)) {
      if (placed >= 9 || C.z2 > 1.05) continue;
      const w = C.n.id.length * 10 + 8;
      if (!free(C.sx, C.sy - 8, w, 14)) continue;
      ctx.fillStyle = `rgba(230,225,214,${Math.min(0.66, 0.26 + C.n.weight * 0.1).toFixed(3)})`;
      ctx.fillText(C.n.id, C.sx, C.sy - 8);
      placed++;
    }
  }

  // ── 外部 API ──────────────────────────────────────────────────
  function resize() {
    const r = canvas.getBoundingClientRect();
    if (!r.width || !r.height) return;
    dpr = Math.min(window.devicePixelRatio || 1, 2);
    W = r.width; H = r.height;
    canvas.width = Math.round(W * dpr);
    canvas.height = Math.round(H * dpr);
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    if (!cloud.length && zones.length) cloud = buildCloud(opts.points || 5200);
  }

  function setData(state) {
    const dist = state.analysis.zone_distribution || [];
    const shareBy = new Map(dist.map(d => [d.zone, d.share]));
    zones = (state.zones || []).map(z => ({ ...z, share: shareBy.get(z.key) || 0 }));
    cloud = buildCloud(opts.points || 5200);
    nodes = placeNodes((state.analysis.top_concepts || []).slice(0, 34));
    edges = buildEdges(state.analysis.links || [], nodes);
    pulses = [];
  }

  function setAuto(v) { autoRotate = v; }
  function setLinks(v) { showLinks = v; }
  function view(name) {
    autoRotate = false;
    if (name === 'side') { yaw = -0.62; pitch = 0.2; }
    else if (name === 'front') { yaw = -1.57; pitch = 0.12; }
    else { yaw = -0.62; pitch = 1.16; }
  }

  // ── 操作 ──────────────────────────────────────────────────────
  canvas.addEventListener('pointerdown', e => {
    dragging = true; lastX = e.clientX; lastY = e.clientY;
    canvas.classList.add('drag'); canvas.setPointerCapture(e.pointerId);
  });
  canvas.addEventListener('pointermove', e => {
    if (!dragging) return;
    yaw += (e.clientX - lastX) * 0.006;
    pitch = Math.max(-1.45, Math.min(1.45, pitch + (e.clientY - lastY) * 0.005));
    lastX = e.clientX; lastY = e.clientY;
  });
  const stop = () => { dragging = false; canvas.classList.remove('drag'); };
  canvas.addEventListener('pointerup', stop);
  canvas.addEventListener('pointercancel', stop);

  const ro = new ResizeObserver(resize);
  ro.observe(canvas);
  resize();
  raf = requestAnimationFrame(frame);

  return { setData, setAuto, setLinks, view, resize, destroy: () => { cancelAnimationFrame(raf); ro.disconnect(); } };
}
