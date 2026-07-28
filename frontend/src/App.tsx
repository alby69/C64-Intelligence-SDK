import { Sidebar } from "./components/Sidebar";
import { TabBar } from "./components/TabBar";
import { EditorPanel } from "./components/EditorPanel";
import { TerminalPanel } from "./components/TerminalPanel";
import { StatusBar } from "./components/StatusBar";

export default function App() {
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
