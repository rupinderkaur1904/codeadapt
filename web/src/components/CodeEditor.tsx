import { cpp } from "@codemirror/lang-cpp";
import CodeMirror from "@uiw/react-codemirror";
import { useSyncExternalStore } from "react";

const extensions = [cpp()];

const DARK = "(prefers-color-scheme: dark)";

function subscribe(onChange: () => void) {
  const query = window.matchMedia(DARK);
  query.addEventListener("change", onChange);
  return () => query.removeEventListener("change", onChange);
}

/** Follows the system colour scheme, as the rest of the page does. */
function usePrefersDark() {
  return useSyncExternalStore(
    subscribe,
    () => window.matchMedia(DARK).matches,
    () => false,
  );
}

export function CodeEditor({
  value,
  onChange,
}: {
  value: string;
  onChange: (value: string) => void;
}) {
  const dark = usePrefersDark();
  return (
    <CodeMirror
      value={value}
      onChange={onChange}
      extensions={extensions}
      theme={dark ? "dark" : "light"}
      height="360px"
      aria-label="Solution code"
      basicSetup={{ tabSize: 4 }}
    />
  );
}
