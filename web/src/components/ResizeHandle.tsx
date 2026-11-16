import {
  type KeyboardEvent,
  type PointerEvent,
  type RefObject,
  useCallback,
  useState,
} from "react";

const STORAGE_KEY = "codeadapt:layout:problem-width";
export const SPLIT_MIN = 0.25;
export const SPLIT_MAX = 0.65;
const SPLIT_DEFAULT = 0.4;
const KEY_STEP = 0.02;

function clamp(value: number): number {
  return Math.min(SPLIT_MAX, Math.max(SPLIT_MIN, value));
}

function readStored(): number {
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    const value = raw === null ? NaN : Number(raw);
    return Number.isFinite(value) ? clamp(value) : SPLIT_DEFAULT;
  } catch {
    return SPLIT_DEFAULT;
  }
}

function store(value: number): void {
  try {
    window.localStorage.setItem(STORAGE_KEY, value.toFixed(3));
  } catch {
    // Storage blocked (private window): the layout still works, it just is not remembered.
  }
}

/** The problem panel's share of the workspace width, remembered on this computer only. */
export function useSplit() {
  const [ratio, setRatio] = useState(readStored);
  const update = useCallback((value: number) => {
    const next = clamp(value);
    setRatio(next);
    store(next);
  }, []);
  return [ratio, update] as const;
}

/** Draggable, keyboard-operable divider between the problem and editor panels. */
export function ResizeHandle({
  container,
  ratio,
  onChange,
}: {
  container: RefObject<HTMLElement | null>;
  ratio: number;
  onChange: (ratio: number) => void;
}) {
  const [dragging, setDragging] = useState(false);

  const moveTo = (clientX: number) => {
    const box = container.current?.getBoundingClientRect();
    if (!box || box.width === 0) return;
    onChange((clientX - box.left) / box.width);
  };

  const onPointerDown = (e: PointerEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.currentTarget.setPointerCapture(e.pointerId);
    setDragging(true);
  };
  const onPointerMove = (e: PointerEvent<HTMLDivElement>) => {
    if (dragging) moveTo(e.clientX);
  };
  const stop = (e: PointerEvent<HTMLDivElement>) => {
    if (e.currentTarget.hasPointerCapture(e.pointerId)) {
      e.currentTarget.releasePointerCapture(e.pointerId);
    }
    setDragging(false);
  };
  const onKeyDown = (e: KeyboardEvent<HTMLDivElement>) => {
    const moves: Record<string, number> = {
      ArrowLeft: ratio - KEY_STEP,
      ArrowRight: ratio + KEY_STEP,
      Home: SPLIT_MIN,
      End: SPLIT_MAX,
    };
    const next = moves[e.key];
    if (next === undefined) return;
    e.preventDefault();
    onChange(next);
  };

  return (
    <div
      className={dragging ? "resize-handle dragging" : "resize-handle"}
      role="separator"
      aria-orientation="vertical"
      aria-label="Resize problem and editor panels"
      aria-valuemin={Math.round(SPLIT_MIN * 100)}
      aria-valuemax={Math.round(SPLIT_MAX * 100)}
      aria-valuenow={Math.round(ratio * 100)}
      tabIndex={0}
      onPointerDown={onPointerDown}
      onPointerMove={onPointerMove}
      onPointerUp={stop}
      onPointerCancel={stop}
      onKeyDown={onKeyDown}
      onDoubleClick={() => onChange(SPLIT_DEFAULT)}
    />
  );
}
