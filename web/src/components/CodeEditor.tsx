import { cpp } from "@codemirror/lang-cpp";
import CodeMirror from "@uiw/react-codemirror";

const extensions = [cpp()];

export function CodeEditor({
  value,
  onChange,
}: {
  value: string;
  onChange: (value: string) => void;
}) {
  return (
    <CodeMirror
      value={value}
      onChange={onChange}
      extensions={extensions}
      height="360px"
      aria-label="Solution code"
      basicSetup={{ tabSize: 4 }}
    />
  );
}
