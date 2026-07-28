import React from "react";
import ReactDOM from "react-dom/client";
import { useMonaco } from "@monaco-editor/react";
import App from "./App";
import { registerC64Languages } from "./services/monacoLanguages";
import "./index.css";

function MonacoInit({ children }: { children: React.ReactNode }) {
  const monaco = useMonaco();
  React.useEffect(() => {
    if (monaco) {
      registerC64Languages(monaco);
    }
  }, [monaco]);
  return <>{children}</>;
}

ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>
    <MonacoInit>
      <App />
    </MonacoInit>
  </React.StrictMode>
);
