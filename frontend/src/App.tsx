import { useEffect, useState } from "react";
import { Sidebar } from "./components/Sidebar";
import { TabBar } from "./components/TabBar";
import { EditorPanel } from "./components/EditorPanel";
import { TerminalPanel } from "./components/TerminalPanel";
import { StatusBar } from "./components/StatusBar";
import { AiCopilotPanel } from "./components/AiCopilotPanel";
import { DiskBrowser } from "./components/DiskBrowser";
import { C64ScreenPreview } from "./components/C64ScreenPreview";
import { ProjectWizard } from "./components/ProjectWizard";
import { FirstRunWizard } from "./components/FirstRunWizard";
import { useIDEStore } from "./store/ideStore";
import { writeFile } from "./services/tauriBridge";
import { runCompile, runEmulator } from "./services/commandService";
import {
  loadPreferences,
  savePreferences,
  UserPreferences,
} from "./services/preferencesService";

export default function App() {
  const { activeFile, fileContents, saveActiveFile, setActiveProject } = useIDEStore();
  const [showWizard, setShowWizard] = useState(false);
  const [prefsLoaded, setPrefsLoaded] = useState(false);

  // Load preferences on startup
  useEffect(() => {
    (async () => {
      const prefs = await loadPreferences();
      if (prefs.last_project) {
        setActiveProject(prefs.last_project);
      }
      if (prefs.theme === "light") {
        document.documentElement.classList.add("light");
      }
      setPrefsLoaded(true);

      // If no VICE/Python detected, show wizard
      if (!prefs.VICE_path) {
        setShowWizard(true);
      }
    })();
  }, []);

  // Save preferences when active project changes
  useEffect(() => {
    if (!prefsLoaded) return;
    (async () => {
      const prefs = await loadPreferences();
      prefs.last_project = activeProject;
      await savePreferences(prefs);
    })();
  }, [activeFile, prefsLoaded]);

  const { activeProject } = useIDEStore();

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

      if (mod && e.shiftKey && e.key === "A") {
        e.preventDefault();
        document.dispatchEvent(new CustomEvent("ide:toggleCopilot"));
      }

      if (e.key === "F1") {
        e.preventDefault();
        setShowWizard(true);
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
      <AiCopilotPanel />
      <DiskBrowser />
      <C64ScreenPreview />
      <ProjectWizard />
      {showWizard && (
        <FirstRunWizard onComplete={() => setShowWizard(false)} />
      )}
    </div>
  );
}
