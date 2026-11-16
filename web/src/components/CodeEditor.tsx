import { cpp } from "@codemirror/lang-cpp";
import CodeMirror, { EditorView } from "@uiw/react-codemirror";
import { useSyncExternalStore } from "react";

/** Brand typography and spacing on top of CodeMirror's own light and dark themes. */
const workspaceTheme = EditorView.theme({
  "&": { height: "100%", fontSize: "14px" },
  ".cm-scroller": {
    fontFamily: "var(--font-mono)",
    lineHeight: "1.65",
  },
  ".cm-content": { padding: "12px 0" },
  ".cm-line": { padding: "0 16px 0 8px" },
  ".cm-gutters": { borderRight: "1px solid var(--editor-gutter-border)", paddingLeft: "6px" },
  ".cm-lineNumbers .cm-gutterElement": { minWidth: "2.5ch", padding: "0 8px 0 4px" },
});

const extensions = [cpp(), workspaceTheme];

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
      className="code-editor"
      value={value}
      onChange={onChange}
      extensions={extensions}
      theme={dark ? "dark" : "light"}
      height="100%"
      aria-label="Solution code"
      basicSetup={{ tabSize: 4 }}
    />
  );
}
