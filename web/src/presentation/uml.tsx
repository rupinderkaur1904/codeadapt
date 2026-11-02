// Small SVG renderers for the UML diagrams in the presentation. Each diagram is plain data
// (see diagrams.tsx) so the pictures stay in step with the code they describe and can be
// corrected in one place. No diagram library: the renderers draw only the notation we use.

import { Fragment } from "react";

const INK = "var(--deck-ink)";
const MUTED = "var(--deck-muted)";
const PAPER = "var(--deck-paper)";
const ACCENT = "var(--deck-accent)";
const SOIL = "var(--deck-soil)";

function Markers({ id }: { id: string }) {
  return (
    <defs>
      <marker
        id={`${id}-solid`}
        viewBox="0 0 10 10"
        refX="9"
        refY="5"
        markerWidth="8"
        markerHeight="8"
        orient="auto-start-reverse"
      >
        <path d="M0 0 L10 5 L0 10 Z" fill={INK} />
      </marker>
      <marker
        id={`${id}-open`}
        viewBox="0 0 10 10"
        refX="9"
        refY="5"
        markerWidth="9"
        markerHeight="9"
        orient="auto-start-reverse"
      >
        <path d="M0 0 L10 5 L0 10" fill="none" stroke={INK} strokeWidth="1.4" />
      </marker>
      <marker
        id={`${id}-hollow`}
        viewBox="0 0 12 12"
        refX="11"
        refY="6"
        markerWidth="12"
        markerHeight="12"
        orient="auto-start-reverse"
      >
        <path d="M0 0 L12 6 L0 12 Z" fill={PAPER} stroke={INK} strokeWidth="1.2" />
      </marker>
      <marker
        id={`${id}-diamond`}
        viewBox="0 0 16 10"
        refX="15"
        refY="5"
        markerWidth="15"
        markerHeight="10"
        orient="auto-start-reverse"
      >
        <path d="M0 5 L8 0 L16 5 L8 10 Z" fill={INK} />
      </marker>
      <marker
        id={`${id}-odiamond`}
        viewBox="0 0 16 10"
        refX="15"
        refY="5"
        markerWidth="15"
        markerHeight="10"
        orient="auto-start-reverse"
      >
        <path d="M0 5 L8 0 L16 5 L8 10 Z" fill={PAPER} stroke={INK} strokeWidth="1.2" />
      </marker>
    </defs>
  );
}

function Lines({
  x,
  y,
  lines,
  size,
  anchor = "middle",
  weight,
  fill = INK,
  gap,
}: {
  x: number;
  y: number;
  lines: string[];
  size: number;
  anchor?: "start" | "middle" | "end";
  weight?: number;
  fill?: string;
  gap?: number;
}) {
  const lh = gap ?? size * 1.2;
  const top = y - ((lines.length - 1) * lh) / 2;
  return (
    <text
      x={x}
      textAnchor={anchor}
      fontSize={size}
      fontWeight={weight}
      fill={fill}
      dominantBaseline="middle"
    >
      {lines.map((l, i) => (
        <tspan key={i} x={x} y={top + i * lh}>
          {l}
        </tspan>
      ))}
    </text>
  );
}

/* ------------------------------------------------------------------ use case diagrams */

export type UseCaseSpec = {
  id: string;
  width: number;
  height: number;
  system: { x: number; y: number; w: number; h: number; label: string };
  actors: { id: string; label: string; x: number; y: number; kind?: "human" | "system" }[];
  cases: { id: string; label: string; x: number; y: number; w?: number }[];
  links: [string, string][];
  rels?: { from: string; to: string; type: "include" | "extend" }[];
  generalise?: [string, string][]; // [child actor, parent actor]
};

const UC_RY = 25;

function need<T>(v: T | undefined, what: string): T {
  if (v === undefined) throw new Error(`diagram refers to unknown ${what}`);
  return v;
}

function ellipseEdge(cx: number, cy: number, rx: number, ry: number, tx: number, ty: number) {
  const dx = tx - cx;
  const dy = ty - cy;
  const t = 1 / Math.sqrt((dx / rx) ** 2 + (dy / ry) ** 2);
  return { x: cx + dx * t, y: cy + dy * t };
}

export function UseCaseDiagram({ spec }: { spec: UseCaseSpec }) {
  const cases = new Map(spec.cases.map((c) => [c.id, c]));
  const actors = new Map(spec.actors.map((a) => [a.id, a]));
  const rx = (id: string) => (cases.get(id)?.w ?? 190) / 2;
  const anchor = (id: string) => {
    const a = actors.get(id);
    if (a) return { x: a.x, y: a.kind === "system" ? a.y : a.y - 8 };
    const c = need(cases.get(id), "id");
    return { x: c.x, y: c.y };
  };
  const edge = (id: string, toward: { x: number; y: number }) => {
    const c = cases.get(id);
    if (!c) {
      const a = need(actors.get(id), "id");
      if (a.kind === "system") {
        const dx = toward.x - a.x;
        return { x: a.x + Math.sign(dx) * 62, y: a.y };
      }
      return { x: a.x + Math.sign(toward.x - a.x) * 22, y: a.y - 8 };
    }
    return ellipseEdge(c.x, c.y, rx(id), UC_RY, toward.x, toward.y);
  };
  return (
    <svg
      viewBox={`0 0 ${spec.width} ${spec.height}`}
      className="uml"
      role="img"
      aria-label={`Use case diagram: ${spec.system.label}`}
    >
      <Markers id={spec.id} />
      <rect
        x={spec.system.x}
        y={spec.system.y}
        width={spec.system.w}
        height={spec.system.h}
        rx="6"
        fill="var(--deck-panel)"
        stroke={INK}
        strokeWidth="1.3"
      />
      <text x={spec.system.x + 14} y={spec.system.y + 22} fontSize="13" fontWeight="700" fill={INK}>
        {spec.system.label}
      </text>
      {spec.links.map(([a, c]) => {
        const p = anchor(a);
        const cs = cases.get(c);
        // Actor lines meet the ellipse at its nearest end, as on a radial layout.
        const q = cs ? { x: cs.x + Math.sign(p.x - cs.x) * rx(c), y: cs.y } : edge(c, p);
        const s = edge(a, q);
        return (
          <line
            key={`${a}-${c}`}
            x1={s.x}
            y1={s.y}
            x2={q.x}
            y2={q.y}
            stroke={INK}
            strokeWidth="1.1"
          />
        );
      })}
      {(spec.rels ?? []).map((r) => {
        const p = anchor(r.from);
        const q = anchor(r.to);
        const s = edge(r.from, q);
        const e = edge(r.to, p);
        const mx = (s.x + e.x) / 2;
        const my = (s.y + e.y) / 2;
        return (
          <g key={`${r.from}-${r.to}`}>
            <line
              x1={s.x}
              y1={s.y}
              x2={e.x}
              y2={e.y}
              stroke={INK}
              strokeWidth="1.1"
              strokeDasharray="5 4"
              markerEnd={`url(#${spec.id}-open)`}
            />
            <rect x={mx - 30} y={my - 8} width="60" height="15" fill="var(--deck-panel)" />
            <text
              x={mx}
              y={my + 3}
              fontSize="10.5"
              textAnchor="middle"
              fill={MUTED}
              fontStyle="italic"
            >
              «{r.type}»
            </text>
          </g>
        );
      })}
      {(spec.generalise ?? []).map(([child, parent]) => {
        const c = need(actors.get(child), "id");
        const p = need(actors.get(parent), "id");
        return (
          <line
            key={`${child}-${parent}`}
            x1={c.x}
            y1={c.y - 62}
            x2={p.x}
            y2={p.y + 28}
            stroke={INK}
            strokeWidth="1.1"
            markerEnd={`url(#${spec.id}-hollow)`}
          />
        );
      })}
      {spec.cases.map((c) => (
        <g key={c.id}>
          <ellipse
            cx={c.x}
            cy={c.y}
            rx={rx(c.id)}
            ry={UC_RY}
            fill={PAPER}
            stroke={INK}
            strokeWidth="1.2"
          />
          <Lines x={c.x} y={c.y} lines={c.label.split("\n")} size={12} />
        </g>
      ))}
      {spec.actors.map((a) =>
        a.kind === "system" ? (
          <g key={a.id}>
            <rect
              x={a.x - 62}
              y={a.y - 26}
              width="124"
              height="52"
              rx="3"
              fill={PAPER}
              stroke={INK}
              strokeWidth="1.2"
            />
            <text x={a.x} y={a.y - 8} fontSize="10" textAnchor="middle" fill={MUTED}>
              «system»
            </text>
            <Lines
              x={a.x}
              y={a.y + 9}
              lines={a.label.split("\n")}
              size={12}
              weight={700}
              gap={13}
            />
          </g>
        ) : (
          <g key={a.id} stroke={INK} strokeWidth="1.5" fill="none">
            <circle cx={a.x} cy={a.y - 42} r="9" fill={PAPER} />
            <line x1={a.x} y1={a.y - 33} x2={a.x} y2={a.y - 6} />
            <line x1={a.x - 15} y1={a.y - 24} x2={a.x + 15} y2={a.y - 24} />
            <line x1={a.x} y1={a.y - 6} x2={a.x - 12} y2={a.y + 12} />
            <line x1={a.x} y1={a.y - 6} x2={a.x + 12} y2={a.y + 12} />
            <g stroke="none" fill={INK}>
              <Lines
                x={a.x}
                y={a.y + 30}
                lines={a.label.split("\n")}
                size={12.5}
                weight={700}
                gap={14}
              />
            </g>
          </g>
        ),
      )}
    </svg>
  );
}

/* ------------------------------------------------------------------ sequence diagrams */

export type Participant = { id: string; label: string; kind?: "actor" | "db" | "box" };
export type SeqStep =
  | { from: string; to: string; text: string; reply?: boolean }
  | { note: string; over: string; to?: string }
  | { open: "alt" | "loop" | "opt"; guard: string }
  | { orelse: string }
  | { close: true };

export type SequenceSpec = {
  id: string;
  width: number;
  participants: Participant[];
  steps: SeqStep[];
};

export function SequenceDiagram({ spec }: { spec: SequenceSpec }) {
  const n = spec.participants.length;
  const margin = 80;
  const gapX = (spec.width - 2 * margin) / (n - 1);
  const xOf = new Map(spec.participants.map((p, i) => [p.id, margin + i * gapX]));
  const headH = 46;
  const rowH = 29;
  let y = headH + 26;
  let num = 0;

  type Frame = {
    kind: string;
    guard: string;
    y0: number;
    minX: number;
    maxX: number;
    elses: { y: number; label: string }[];
    depth: number;
  };
  const stack: Frame[] = [];
  const frames: (Frame & { y1: number })[] = [];
  const items: React.ReactNode[] = [];

  const touch = (...xs: number[]) => {
    for (const f of stack) {
      f.minX = Math.min(f.minX, ...xs);
      f.maxX = Math.max(f.maxX, ...xs);
    }
  };

  spec.steps.forEach((s, i) => {
    if ("open" in s) {
      stack.push({
        kind: s.open,
        guard: s.guard,
        y0: y - 8,
        minX: Infinity,
        maxX: -Infinity,
        elses: [],
        depth: stack.length,
      });
      y += 26;
      return;
    }
    if ("orelse" in s) {
      need(stack[stack.length - 1], "frame").elses.push({ y: y - 6, label: s.orelse });
      y += 24;
      return;
    }
    if ("close" in s) {
      const f = need(stack.pop(), "frame");
      frames.push({ ...f, y1: y - 6 });
      y += 14;
      return;
    }
    if ("note" in s) {
      const a = need(xOf.get(s.over), "id");
      const b = need(xOf.get(s.to ?? s.over), "id");
      const x0 = Math.min(a, b) - 70;
      const x1 = Math.max(a, b) + 70;
      touch(x0 + 20, x1 - 20);
      items.push(
        <g key={i}>
          <path
            d={`M${x0} ${y - 13} H${x1 - 9} L${x1} ${y - 4} V${y + 13} H${x0} Z`}
            fill="var(--deck-flag)"
            stroke={INK}
            strokeWidth="0.9"
          />
          <text x={(x0 + x1) / 2} y={y + 4} fontSize="11.5" textAnchor="middle" fill={INK}>
            {s.note}
          </text>
        </g>,
      );
      y += rowH + 4;
      return;
    }
    num += 1;
    const x1 = need(xOf.get(s.from), "id");
    const x2 = need(xOf.get(s.to), "id");
    if (s.from === s.to) {
      // Labels run right of the loop unless that would leave the diagram.
      const textW = (s.text.length + 4) * 6.2;
      const left = x1 + 48 + textW > spec.width;
      touch(left ? x1 - textW + 40 : x1, left ? x1 + 40 : x1 + 48 + textW - 60);
      items.push(
        <g key={i}>
          <path
            d={`M${x1 + 5} ${y - 4} H${x1 + 40} V${y + 12} H${x1 + 7}`}
            fill="none"
            stroke={INK}
            strokeWidth="1.1"
            markerEnd={`url(#${spec.id}-solid)`}
          />
          <text
            x={left ? x1 - 6 : x1 + 48}
            y={y + 2}
            fontSize="11.5"
            fill={INK}
            textAnchor={left ? "end" : "start"}
          >
            <tspan fontWeight="700" fill={ACCENT}>
              {num}.{" "}
            </tspan>
            {s.text}
          </text>
        </g>,
      );
      y += rowH + 10;
      return;
    }
    touch(x1, x2);
    const dir = Math.sign(x2 - x1);
    items.push(
      <g key={i}>
        <line
          x1={x1 + dir * 5}
          y1={y}
          x2={x2 - dir * 5}
          y2={y}
          stroke={INK}
          strokeWidth="1.1"
          strokeDasharray={s.reply ? "5 4" : undefined}
          markerEnd={`url(#${spec.id}-${s.reply ? "open" : "solid"})`}
        />
        <text x={(x1 + x2) / 2} y={y - 6} fontSize="11.5" textAnchor="middle" fill={INK}>
          <tspan fontWeight="700" fill={ACCENT}>
            {num}.{" "}
          </tspan>
          {s.text}
        </text>
      </g>,
    );
    y += rowH;
  });

  const height = y + 10;
  return (
    <svg
      viewBox={`0 0 ${spec.width} ${height}`}
      className="uml"
      role="img"
      aria-label="Sequence diagram"
    >
      <Markers id={spec.id} />
      {spec.participants.map((p) => {
        const x = need(xOf.get(p.id), "id");
        return (
          <g key={p.id}>
            <line
              x1={x}
              y1={headH}
              x2={x}
              y2={height - 4}
              stroke={MUTED}
              strokeWidth="1"
              strokeDasharray="3 4"
            />
            {p.kind === "actor" ? (
              <g stroke={INK} strokeWidth="1.4" fill="none">
                <circle cx={x - 46} cy={headH / 2 - 7} r="5" fill={PAPER} />
                <line x1={x - 46} y1={headH / 2 - 2} x2={x - 46} y2={headH / 2 + 9} />
                <line x1={x - 53} y1={headH / 2 + 2} x2={x - 39} y2={headH / 2 + 2} />
                <line x1={x - 46} y1={headH / 2 + 9} x2={x - 51} y2={headH / 2 + 16} />
                <line x1={x - 46} y1={headH / 2 + 9} x2={x - 41} y2={headH / 2 + 16} />
              </g>
            ) : null}
            {p.kind === "db" ? (
              <g>
                <path
                  d={`M${x - 56} 8 V${headH - 8} A56 7 0 0 0 ${x + 56} ${headH - 8} V8`}
                  fill={PAPER}
                  stroke={INK}
                  strokeWidth="1.2"
                />
                <ellipse cx={x} cy={8} rx="56" ry="7" fill={PAPER} stroke={INK} strokeWidth="1.2" />
              </g>
            ) : (
              <rect
                x={x - 66}
                y={4}
                width="132"
                height={headH - 8}
                rx="4"
                fill={p.kind === "actor" ? "var(--deck-flag)" : PAPER}
                stroke={INK}
                strokeWidth="1.2"
              />
            )}
            <text
              x={p.kind === "actor" ? x + 8 : x}
              y={headH / 2 + 6}
              fontSize="12"
              fontWeight="700"
              textAnchor="middle"
              fill={INK}
            >
              {p.label}
            </text>
          </g>
        );
      })}
      {frames.map((f, i) => {
        const inset = f.depth * 10;
        const fx = Math.max(6 + inset, f.minX - 70 + inset);
        const fw = Math.min(spec.width - 6 - inset, f.maxX + 70 - inset) - fx;
        const tab = `${f.kind} [${f.guard}]`;
        const tw = tab.length * 6.4 + 18;
        return (
          <g key={`f${i}`}>
            <rect
              x={fx}
              y={f.y0}
              width={fw}
              height={f.y1 - f.y0}
              fill="none"
              stroke={SOIL}
              strokeWidth="1.1"
            />
            <path
              d={`M${fx} ${f.y0} H${fx + tw} V${f.y0 + 12} L${fx + tw - 8} ${f.y0 + 19} H${fx} Z`}
              fill="var(--deck-panel)"
              stroke={SOIL}
              strokeWidth="1.1"
            />
            <text x={fx + 7} y={f.y0 + 13.5} fontSize="10.5" fontWeight="700" fill={SOIL}>
              {tab}
            </text>
            {f.elses.map((e) => (
              <Fragment key={e.label}>
                <line
                  x1={fx}
                  y1={e.y}
                  x2={fx + fw}
                  y2={e.y}
                  stroke={SOIL}
                  strokeWidth="1"
                  strokeDasharray="6 4"
                />
                <text x={fx + 8} y={e.y + 14} fontSize="10.5" fontWeight="700" fill={SOIL}>
                  [{e.label}]
                </text>
              </Fragment>
            ))}
          </g>
        );
      })}
      {items}
    </svg>
  );
}

/* ------------------------------------------------------------------ class diagram */

export type ClassBox = {
  id: string;
  name: string;
  stereotype?: string;
  x: number;
  y: number;
  w: number;
  attrs: string[];
  ops?: string[];
  tone?: "data" | "logic" | "iface";
};
export type ClassRel = {
  from: string;
  to: string;
  type: "assoc" | "comp" | "agg" | "dep" | "real";
  fromMult?: string;
  toMult?: string;
  label?: string;
  via?: [number, number][]; // optional bend points
  labelAt?: [number, number];
};
export type ClassSpec = {
  id: string;
  width: number;
  height: number;
  classes: ClassBox[];
  rels: ClassRel[];
};

const LINE = 14;
function boxHeight(c: ClassBox) {
  const head = c.stereotype ? 36 : 24;
  const ops = c.ops?.length ? c.ops.length * LINE + 8 : 6;
  return head + c.attrs.length * LINE + 8 + ops;
}

function clip(c: ClassBox, tx: number, ty: number) {
  const h = boxHeight(c);
  const cx = c.x + c.w / 2;
  const cy = c.y + h / 2;
  const dx = tx - cx;
  const dy = ty - cy;
  const sx = dx === 0 ? Infinity : c.w / 2 / Math.abs(dx);
  const sy = dy === 0 ? Infinity : h / 2 / Math.abs(dy);
  const s = Math.min(sx, sy);
  return { x: cx + dx * s, y: cy + dy * s };
}

export function ClassDiagram({ spec }: { spec: ClassSpec }) {
  const byId = new Map(spec.classes.map((c) => [c.id, c]));
  const centre = (c: ClassBox) => ({ x: c.x + c.w / 2, y: c.y + boxHeight(c) / 2 });
  return (
    <svg
      viewBox={`0 0 ${spec.width} ${spec.height}`}
      className="uml"
      role="img"
      aria-label="Class diagram"
    >
      <Markers id={spec.id} />
      {spec.rels.map((r, i) => {
        const a = need(byId.get(r.from), "id");
        const b = need(byId.get(r.to), "id");
        const pts = r.via ?? [];
        const p0 = pts[0];
        const pn = pts[pts.length - 1];
        const first = p0 ? { x: p0[0], y: p0[1] } : centre(b);
        const last = pn ? { x: pn[0], y: pn[1] } : centre(a);
        const s = clip(a, first.x, first.y);
        const e = clip(b, last.x, last.y);
        const d = [`M${s.x} ${s.y}`, ...pts.map(([x, y]) => `L${x} ${y}`), `L${e.x} ${e.y}`].join(
          " ",
        );
        const dashed = r.type === "dep" || r.type === "real";
        const start =
          r.type === "comp"
            ? `url(#${spec.id}-diamond)`
            : r.type === "agg"
              ? `url(#${spec.id}-odiamond)`
              : undefined;
        const end =
          r.type === "real"
            ? `url(#${spec.id}-hollow)`
            : r.type === "dep"
              ? `url(#${spec.id}-open)`
              : undefined;
        const mult = (p: { x: number; y: number }, q: { x: number; y: number }, label?: string) => {
          if (!label) return null;
          const len = Math.hypot(q.x - p.x, q.y - p.y) || 1;
          const ux = (q.x - p.x) / len;
          const uy = (q.y - p.y) / len;
          const x = p.x + ux * 20 - uy * 10;
          const y = p.y + uy * 20 + ux * 10;
          return (
            <text x={x} y={y + 4} fontSize="10.5" textAnchor="middle" fill={MUTED}>
              {label}
            </text>
          );
        };
        const mid = p0 ? { x: p0[0], y: p0[1] } : { x: (s.x + e.x) / 2, y: (s.y + e.y) / 2 };
        return (
          <g key={i}>
            <path
              d={d}
              fill="none"
              stroke={INK}
              strokeWidth="1.1"
              strokeDasharray={dashed ? "5 4" : undefined}
              markerStart={start}
              markerEnd={end}
            />
            {mult(s, first, r.fromMult)}
            {mult(e, last, r.toMult)}
            {r.label && (
              <text
                x={r.labelAt ? r.labelAt[0] : mid.x + 4}
                y={r.labelAt ? r.labelAt[1] : mid.y - 5}
                fontSize="10.5"
                fill={MUTED}
                fontStyle="italic"
              >
                {r.label}
              </text>
            )}
          </g>
        );
      })}
      {spec.classes.map((c) => {
        const h = boxHeight(c);
        const head = c.stereotype ? 36 : 24;
        const attrTop = c.y + head;
        const opsTop = attrTop + c.attrs.length * LINE + 8;
        const headFill =
          c.tone === "logic"
            ? "var(--deck-sprout-soft)"
            : c.tone === "iface"
              ? "var(--deck-flag)"
              : "var(--deck-panel)";
        return (
          <g key={c.id}>
            <rect
              x={c.x}
              y={c.y}
              width={c.w}
              height={h}
              fill={PAPER}
              stroke={INK}
              strokeWidth="1.2"
            />
            <rect
              x={c.x}
              y={c.y}
              width={c.w}
              height={head}
              fill={headFill}
              stroke={INK}
              strokeWidth="1.2"
            />
            {c.stereotype && (
              <text x={c.x + c.w / 2} y={c.y + 13} fontSize="9.5" textAnchor="middle" fill={MUTED}>
                «{c.stereotype}»
              </text>
            )}
            <text
              x={c.x + c.w / 2}
              y={c.y + head - 8}
              fontSize="12"
              fontWeight="700"
              textAnchor="middle"
              fill={INK}
              fontStyle={c.tone === "iface" ? "italic" : undefined}
            >
              {c.name}
            </text>
            {c.attrs.map((a, i) => (
              <text
                key={a}
                x={c.x + 7}
                y={attrTop + 13 + i * LINE}
                fontSize="10.5"
                fill={INK}
                className="mono"
              >
                {a}
              </text>
            ))}
            <line x1={c.x} y1={opsTop} x2={c.x + c.w} y2={opsTop} stroke={INK} strokeWidth="1" />
            {(c.ops ?? []).map((o, i) => (
              <text
                key={o}
                x={c.x + 7}
                y={opsTop + 15 + i * LINE}
                fontSize="10.5"
                fill={INK}
                className="mono"
              >
                {o}
              </text>
            ))}
          </g>
        );
      })}
    </svg>
  );
}
