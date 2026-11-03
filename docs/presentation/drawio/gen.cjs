// Converts the presentation's UML specs (specs.json) into draw.io pages.
const fs = require("fs");
const D = require("./specs.json");
const OUT = process.argv[2];

const esc = (s) => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
const html = (s) => esc(String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/\n/g, "<br>"));
const FONT = "fontFamily=Helvetica;fontColor=#222A26;";
const INK = "strokeColor=#222A26;";

class Page {
  constructor(name) { this.name = name; this.cells = []; this.n = 0; }
  id(p) { this.n += 1; return `${p}${this.n}`; }
  v(value, x, y, w, h, style, id) {
    id = id || this.id("v");
    this.cells.push(`<mxCell id="${id}" value="${value}" style="${style}" vertex="1" parent="1"><mxGeometry x="${r(x)}" y="${r(y)}" width="${r(w)}" height="${r(h)}" as="geometry"/></mxCell>`);
    return id;
  }
  e(value, style, { source, target, sp, tp, pts, labels } = {}) {
    const id = this.id("e");
    const st = source ? ` source="${source}"` : "", tt = target ? ` target="${target}"` : "";
    let g = `<mxGeometry relative="1" as="geometry">`;
    if (sp) g += `<mxPoint x="${r(sp[0])}" y="${r(sp[1])}" as="sourcePoint"/>`;
    if (tp) g += `<mxPoint x="${r(tp[0])}" y="${r(tp[1])}" as="targetPoint"/>`;
    if (pts && pts.length) g += `<Array as="points">${pts.map((p) => `<mxPoint x="${r(p[0])}" y="${r(p[1])}"/>`).join("")}</Array>`;
    g += `</mxGeometry>`;
    this.cells.push(`<mxCell id="${id}" value="${value}" style="${style}" edge="1" parent="1"${st}${tt}>${g}</mxCell>`);
    for (const [text, pos] of labels || []) {
      this.cells.push(`<mxCell id="${this.id("l")}" value="${esc(text)}" style="edgeLabel;html=1;strokeColor=none;fillColor=none;align=center;verticalAlign=middle;resizable=0;points=[];fontSize=12;${FONT}labelBackgroundColor=#FFFFFF;" vertex="1" connectable="0" parent="${id}"><mxGeometry x="${pos}" relative="1" as="geometry"><mxPoint y="-12" as="offset"/></mxGeometry></mxCell>`);
    }
    return id;
  }
  xml() {
    return `<diagram id="${esc(this.name.replace(/\W+/g, "-"))}" name="${esc(this.name)}"><mxGraphModel dx="1200" dy="800" grid="0" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="0" pageScale="1" math="0" shadow="0" background="#FFFFFF"><root><mxCell id="0"/><mxCell id="1" parent="0"/>${this.cells.join("")}</root></mxGraphModel></diagram>`;
  }
}
const r = (x) => Math.round(x * 10) / 10;

/* ---------------------------------------------------------------- use case */
function useCase(spec, name) {
  const p = new Page(name);
  const s = spec.system;
  p.v(esc(s.label), s.x, s.y, s.w, s.h, `rounded=0;whiteSpace=wrap;html=1;fillColor=#F7F8F6;${INK}verticalAlign=top;align=left;spacingLeft=10;spacingTop=4;fontStyle=1;fontSize=14;${FONT}`);
  const ids = {};
  for (const a of spec.actors) {
    if (a.kind === "system") {
      ids[a.id] = p.v(`«system»&lt;br&gt;&lt;b&gt;${html(a.label)}&lt;/b&gt;`, a.x - 62, a.y - 30, 124, 60, `rounded=0;whiteSpace=wrap;html=1;fillColor=#FFFFFF;${INK}fontSize=12;${FONT}`);
    } else {
      ids[a.id] = p.v(html(a.label), a.x - 16, a.y - 44, 32, 64, `shape=umlActor;verticalLabelPosition=bottom;verticalAlign=top;html=1;outlineConnect=0;fillColor=#FFFFFF;${INK}fontStyle=1;fontSize=14;${FONT}`);
    }
  }
  for (const c of spec.cases) {
    const w = c.w ?? 190;
    ids[c.id] = p.v(html(c.label), c.x - w / 2, c.y - 25, w, 50, `shape=ellipse;perimeter=ellipsePerimeter;whiteSpace=wrap;html=1;fillColor=#FFFFFF;${INK}fontSize=13;${FONT}`);
  }
  for (const [a, b] of spec.links) p.e("", `endArrow=none;html=1;${INK}strokeWidth=1.2;`, { source: ids[a], target: ids[b] });
  for (const rel of spec.rels || [])
    p.e(`«${rel.type}»`, `endArrow=open;endSize=10;dashed=1;html=1;${INK}fontSize=11;${FONT}labelBackgroundColor=#FFFFFF;`, { source: ids[rel.from], target: ids[rel.to] });
  for (const [child, parent] of spec.generalise || [])
    p.e("", `endArrow=block;endFill=0;endSize=12;html=1;${INK}`, { source: ids[child], target: ids[parent] });
  return p;
}

/* ---------------------------------------------------------------- sequence */
function sequence(spec, name) {
  const p = new Page(name);
  const parts = spec.participants;
  const margin = 90, W = spec.width + 40;
  const gap = (W - 2 * margin) / (parts.length - 1);
  const X = Object.fromEntries(parts.map((q, i) => [q.id, margin + i * gap]));
  const headH = 50, rowH = 34;
  let y = headH + 34, num = 0;
  const stack = [], frames = [], after = [];
  const touch = (...xs) => { for (const f of stack) { f.min = Math.min(f.min, ...xs); f.max = Math.max(f.max, ...xs); } };
  for (const s of spec.steps) {
    if (s.open) { stack.push({ kind: s.open, guard: s.guard, y0: y - 12, min: Infinity, max: -Infinity, elses: [], depth: stack.length }); y += 30; continue; }
    if (s.orelse) { stack[stack.length - 1].elses.push({ y: y - 10, label: s.orelse }); y += 28; continue; }
    if (s.close) { const f = stack.pop(); frames.push({ ...f, y1: y - 8 }); y += 16; continue; }
    if (s.note) {
      const a = X[s.over], b = X[s.to ?? s.over];
      const x0 = Math.min(a, b) - 80, x1 = Math.max(a, b) + 80;
      touch(x0 + 20, x1 - 20);
      after.push(() => p.v(esc(esc(s.note)), x0, y - 14, x1 - x0, 28, `shape=note;size=10;whiteSpace=wrap;html=1;fillColor=#FFF7D6;${INK}fontSize=12;${FONT}`));
      y += rowH + 4; continue;
    }
    num += 1;
    const label = esc(esc(`${num}. ${s.text}`));
    const x1 = X[s.from], x2 = X[s.to];
    const style = `html=1;${INK}fontSize=12;${FONT}verticalAlign=bottom;labelBackgroundColor=none;` + (s.reply ? "endArrow=open;endSize=8;dashed=1;" : "endArrow=block;endFill=1;endSize=8;");
    if (s.from === s.to) {
      const tw = (s.text.length + 4) * 6.6;
      const left = x1 + 50 + tw > W;
      touch(left ? x1 - tw : x1, left ? x1 + 46 : x1 + 50 + tw - 40);
      const yy = y;
      after.push(() => {
        p.e("", style.replace("verticalAlign=bottom;", ""), { sp: [x1 + 6, yy - 6], tp: [x1 + 8, yy + 14], pts: [[x1 + 44, yy - 6], [x1 + 44, yy + 14]] });
        p.v(label, left ? x1 - tw - 4 : x1 + 52, yy - 8, tw, 20, `text;strokeColor=none;fillColor=none;html=1;align=${left ? "right" : "left"};verticalAlign=middle;fontSize=12;${FONT}`);
      });
      y += rowH + 10; continue;
    }
    touch(x1, x2);
    const yy = y, dir = Math.sign(x2 - x1);
    after.push(() => p.e(label, style, { sp: [x1 + dir * 6, yy], tp: [x2 - dir * 6, yy] }));
    y += rowH;
  }
  const H = y + 14;
  // lifelines and heads
  for (const q of parts) {
    const x = X[q.id];
    p.e("", `endArrow=none;dashed=1;html=1;strokeColor=#5F6763;`, { sp: [x, headH], tp: [x, H] });
    if (q.kind === "actor") {
      p.v(esc(q.label), x - 12, 2, 24, 30, `shape=umlActor;verticalLabelPosition=bottom;verticalAlign=top;html=1;outlineConnect=0;fillColor=#FFFFFF;${INK}fontStyle=1;fontSize=12;spacingTop=-4;${FONT}`);
    } else if (q.kind === "db") {
      p.v(esc(q.label), x - 60, 2, 120, headH - 4, `shape=cylinder;whiteSpace=wrap;html=1;boundedLbl=1;backgroundOutline=1;size=8;fillColor=#F1F3F0;${INK}fontStyle=1;fontSize=12;${FONT}`);
    } else {
      p.v(esc(q.label), x - 66, 6, 132, headH - 12, `rounded=0;whiteSpace=wrap;html=1;fillColor=#F1F3F0;${INK}fontStyle=1;fontSize=12;${FONT}`);
    }
    // activation bar for the sandbox-side participants is omitted: the slide diagrams have none
  }
  // frames (outer first)
  frames.sort((a, b) => a.depth - b.depth);
  for (const f of frames) {
    const pad = 16 - f.depth * 5;
    const x0 = f.min - 40 - pad, x1 = f.max + 40 + pad;
    p.v(esc(f.kind), x0, f.y0, x1 - x0, f.y1 - f.y0, `shape=umlFrame;whiteSpace=wrap;html=1;width=56;height=22;boundedLbl=1;verticalAlign=top;align=left;spacingLeft=6;fillColor=none;${INK}fontStyle=1;fontSize=12;${FONT}`);
    p.v(esc(esc(`[${f.guard}]`)), x0 + 62, f.y0 + 1, 300, 20, `text;strokeColor=none;fillColor=none;html=1;align=left;verticalAlign=middle;fontSize=12;fontStyle=2;${FONT}`);
    for (const e of f.elses) {
      p.e("", `endArrow=none;dashed=1;html=1;${INK}`, { sp: [x0, e.y], tp: [x1, e.y] });
      p.v(esc(esc(`[${e.label}]`)), x0 + 8, e.y + 1, 300, 20, `text;strokeColor=none;fillColor=none;html=1;align=left;verticalAlign=middle;fontSize=12;fontStyle=2;${FONT}`);
    }
  }
  for (const fn of after) fn();
  return p;
}

/* ---------------------------------------------------------------- class */
function classes(spec, name) {
  const p = new Page(name);
  const K = 1.3, LINE = 18;
  const fill = { data: "#FFFFFF", logic: "#EEF4EF", iface: "#F4F5F3" };
  const ids = {};
  for (const c of spec.classes) {
    const x = c.x * K, y = c.y * K, w = c.w * K;
    const head = c.stereotype ? 44 : 28;
    const attrsH = c.attrs.length * LINE + 8;
    const opsH = c.ops && c.ops.length ? c.ops.length * LINE + 8 : 18;
    const h = head + attrsH + opsH;
    const title = c.stereotype ? `«${esc(c.stereotype)}»&lt;br&gt;&lt;b&gt;${esc(c.name)}&lt;/b&gt;` : `&lt;b&gt;${esc(c.name)}&lt;/b&gt;`;
    const pid = `c_${c.id}`;
    p.cells.push(`<mxCell id="${pid}" value="${title}" style="swimlane;shape=swimlane;fontStyle=${c.stereotype === "protocol" ? 2 : 0};align=center;verticalAlign=middle;childLayout=stackLayout;horizontal=1;startSize=${head};horizontalStack=0;resizeParent=1;resizeParentMax=0;resizeLast=0;collapsible=0;marginBottom=0;html=1;whiteSpace=wrap;fillColor=#F1F3F0;swimlaneFillColor=${fill[c.tone] || "#FFFFFF"};${INK}fontSize=13;${FONT}${c.stereotype === "assumed" ? "dashed=1;" : ""}" vertex="1" parent="1"><mxGeometry x="${r(x)}" y="${r(y)}" width="${r(w)}" height="${r(h)}" as="geometry"/></mxCell>`);
    const row = `text;strokeColor=none;fillColor=none;align=left;verticalAlign=top;spacingLeft=6;spacingRight=4;overflow=hidden;rotatable=0;points=[[0,0.5],[1,0.5]];portConstraint=eastwest;whiteSpace=wrap;html=1;fontSize=12;fontFamily=Courier New;fontColor=#222A26;`;
    p.cells.push(`<mxCell id="${pid}_a" value="${c.attrs.map(esc).map((t) => esc(t)).join("&lt;br&gt;")}" style="${row}" vertex="1" parent="${pid}"><mxGeometry y="${head}" width="${r(w)}" height="${attrsH}" as="geometry"/></mxCell>`);
    p.cells.push(`<mxCell id="${pid}_l" value="" style="line;shape=line;strokeWidth=1;fillColor=none;align=left;verticalAlign=middle;spacingTop=-1;spacingLeft=3;spacingRight=3;rotatable=0;labelPosition=right;points=[];portConstraint=eastwest;${INK}" vertex="1" parent="${pid}"><mxGeometry y="${head + attrsH}" width="${r(w)}" height="8" as="geometry"/></mxCell>`);
    if (c.ops && c.ops.length)
      p.cells.push(`<mxCell id="${pid}_o" value="${c.ops.map((t) => esc(esc(t))).join("&lt;br&gt;")}" style="${row}" vertex="1" parent="${pid}"><mxGeometry y="${head + attrsH + 8}" width="${r(w)}" height="${opsH - 8}" as="geometry"/></mxCell>`);
    ids[c.id] = pid;
  }
  const st = {
    assoc: "endArrow=none;",
    comp: "startArrow=diamondThin;startFill=1;startSize=14;endArrow=none;",
    agg: "startArrow=diamondThin;startFill=0;startSize=14;endArrow=none;",
    dep: "endArrow=open;endSize=10;dashed=1;",
    real: "endArrow=block;endFill=0;endSize=12;dashed=1;",
  };
  for (const rel of spec.rels) {
    const labels = [];
    if (rel.fromMult) labels.push([rel.fromMult, -0.8]);
    if (rel.toMult) labels.push([rel.toMult, 0.8]);
    const pts = (rel.via || []).map(([a, b]) => [a * K, b * K]);
    const id = p.e(rel.label ? esc(rel.label) : "", `html=1;rounded=0;${INK}strokeWidth=1.2;fontSize=12;fontStyle=2;${FONT}labelBackgroundColor=#FFFFFF;` + st[rel.type], { source: ids[rel.from], target: ids[rel.to], pts, labels });
  }
  return p;
}

const pages = [
  useCase(D.UC_STUDENT, "Use case 1 - Student"),
  useCase(D.UC_RESEARCHER, "Use case 2 - Researcher"),
  useCase(D.UC_ADMIN, "Use case 3 - Administrator"),
  useCase(D.UC_WORKER, "Use case 4 - Runner worker"),
  classes(D.CLASSES, "Class diagram"),
  sequence(D.SD_LOGIN, "Sequence 1 - Login"),
  sequence(D.SD_SUBMIT, "Sequence 2 - Submit a solution"),
  sequence(D.SD_EVALUATE, "Sequence 3 - Run and diagnose"),
  sequence(D.SD_ADAPT, "Sequence 4 - Recommendation"),
  sequence(D.SD_RESEARCH, "Sequence 5 - Researcher view"),
];
fs.writeFileSync(OUT, `<mxfile host="app.diagrams.net" agent="CodeAdapt" version="24.7.17">${pages.map((p) => p.xml()).join("")}</mxfile>\n`);
fs.mkdirSync(OUT + ".pages", { recursive: true });
pages.forEach((p, i) => fs.writeFileSync(`${OUT}.pages/${i}.xml`, p.xml()));
console.log("pages", pages.length);
