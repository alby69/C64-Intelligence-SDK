import { useEffect } from "react";
import { Sidebar } from "./components/Sidebar";
import { TabBar } from "./components/TabBar";
import { EditorPanel } from "./components/EditorPanel";
import { TerminalPanel } from "./components/TerminalPanel";
import { StatusBar } from "./components/StatusBar";
import { useIDEStore } from "./store/ideStore";
import { writeFile } from "./services/tauriBridge";
import { runCompile, runEmulator } from "./services/commandService";

export default function App() {
  const { activeFile, fileContents, saveActiveFile } = useIDEStore();

  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      const mod = e.ctrlKey || e.metaKey;

      if (mod && e.key === "s") {
        e.preventDefault();
        if (activeFile) {
          const content = fileContents[activeFile] || "";
          saveActiveFile((path, cont) => writeFile(path, cont));
        }
      }

      if (mod && e.key === "b") {
        e.preventDefault();
        if (activeFile) {
          runCompile(activeFile);
        }
      }

      if (e.key === "F5") {
        e.preventDefault();
        if (activeFile) {
          runEmulator(activeFile);
        }
      }

      if (mod && e.key === "o") {
        e.preventDefault();
        document.dispatchEvent(new CustomEvent("ide:openFile"));
      }

      if (mod && e.key === "n") {
        e.preventDefault();
        document.dispatchEvent(new CustomEvent("ide:newFile"));
      }
    }

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [activeFile, fileContents, saveActiveFile]);

  return (
    <div className="flex flex-col h-screen w-screen bg-editor-bg text-editor-text">
      <div className="flex flex-1 overflow-hidden">
        <Sidebar />
        <div className="flex flex-col flex-1 overflow-hidden">
          <TabBar />
          <div className="flex flex-1 overflow-hidden">
            <EditorPanel />
          </div>
          <TerminalPanel />
        </div>
      </div>
      <StatusBar />
    </div>
  );
}
