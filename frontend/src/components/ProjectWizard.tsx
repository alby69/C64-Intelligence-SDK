import { useState, useRef, useEffect } from "react";
import { useIDEStore } from "../store/ideStore";
import { saveFileDialog, writeFile, openFileDialog } from "../services/tauriBridge";

interface ProjectTemplate {
  name: string;
  description: string;
  entryContent: string;
  projContent: (name: string) => string;
}

const TEMPLATES: ProjectTemplate[] = [
  {
    name: "Hello World",
    description: "Programma base con PRINT",
    entryContent: `# Hello World for C64
def main() -> byte:
    poke(53280, 0)
    poke(53281, 0)
    print("HELLO WORLD!")
    return 0
`,
    projContent: (name) => JSON.stringify({
      project_name: name,
      version: "1.0.0",
      author: "",
      target: "C64",
      entry_point: "main.c64",
      output_name: `${name.toLowerCase().replace(/\s+/g, "_")}.prg`,
      build_config: { optimize: true, assembler: "acme", load_address: "0x0801" },
      assets: [],
    }, null, 2),
  },
  {
    name: "Blinking Screen",
    description: "Cambia colori dello schermo in loop",
    entryContent: `# Blinking Screen
def main() -> byte:
    for i = 0 to 15
        poke(53280, i)
        poke(53281, 15 - i)
        for j = 0 to 200
            pass
        next j
    next i
    poke(53280, 14)
    poke(53281, 6)
    return 0
`,
    projContent: (name) => JSON.stringify({
      project_name: name,
      version: "1.0.0",
      author: "",
      target: "C64",
      entry_point: "main.c64",
      output_name: `${name.toLowerCase().replace(/\s+/g, "_")}.prg`,
      build_config: { optimize: true, assembler: "acme", load_address: "0x0801" },
      assets: [],
    }, null, 2),
  },
  {
    name: "Sprite Demo",
    description: "Mostra uno sprite in movimento",
    entryContent: `# Sprite Demo
byte sprite_data[64] = [
    $00,$7E,$FF,$FF,$FF,$FF,$7E,$00,
    $00,$7E,$FF,$FF,$FF,$FF,$7E,$00,
    $3C,$7E,$FF,$DB,$FF,$DB,$7E,$3C,
    $7E,$FF,$FF,$FF,$FF,$FF,$FF,$7E,
    $7E,$FF,$FF,$FF,$FF,$FF,$FF,$7E,
    $3C,$7E,$FF,$DB,$FF,$DB,$7E,$3C,
    $00,$7E,$FF,$FF,$FF,$FF,$7E,$00,
    $00,$3C,$7E,$7E,$7E,$7E,$3C,$00
]

def main() -> byte:
    poke(53269, 1)
    poke(2040, 13)
    for i = 0 to 63
        poke(832 + i, sprite_data[i])
    next i
    poke(53248, 100)
    poke(53249, 100)
    return 0
`,
    projContent: (name) => JSON.stringify({
      project_name: name,
      version: "1.0.0",
      author: "",
      target: "C64",
      entry_point: "main.c64",
      output_name: `${name.toLowerCase().replace(/\s+/g, "_")}.prg`,
      build_config: { optimize: true, assembler: "acme", load_address: "0x0801" },
      assets: [],
    }, null, 2),
  },
  {
    name: "Progetto Vuoto",
    description: "File di partenza minimale",
    entryContent: `# Nuovo progetto C64
def main() -> byte:
    return 0
`,
    projContent: (name) => JSON.stringify({
      project_name: name,
      version: "1.0.0",
      author: "",
      target: "C64",
      entry_point: "main.c64",
      output_name: `${name.toLowerCase().replace(/\s+/g, "_")}.prg`,
      build_config: { optimize: true, assembler: "acme", load_address: "0x0801" },
      assets: [],
    }, null, 2),
  },
];

export function ProjectWizard() {
  const [collapsed, setCollapsed] = useState(true);
  const [step, setStep] = useState<"list" | "configure">("list");
  const [selectedTemplate, setSelectedTemplate] = useState<ProjectTemplate | null>(null);
  const [projectName, setProjectName] = useState("My C64 Project");
  const [pos, setPos] = useState({ x: window.innerWidth - 340, y: window.innerHeight - 460 });
  const dragging = useRef(false);
  const dragStart = useRef({ x: 0, y: 0, left: 0, top: 0 });

  const handleSelect = (template: ProjectTemplate) => {
    setSelectedTemplate(template);
    setStep("configure");
  };

  const handleCreate = async () => {
    if (!selectedTemplate) return;

    try {
      const projPath = await saveFileDialog(
        `${projectName.toLowerCase().replace(/\s+/g, "_")}.c64proj`
      );
      if (!projPath) return;

      const dir = projPath.substring(0, projPath.lastIndexOf("/"));
      const entryPath = `${dir}/main.c64`;

      await writeFile(projPath, selectedTemplate.projContent(projectName));
      await writeFile(entryPath, selectedTemplate.entryContent);

      useIDEStore.getState().openFile(entryPath, selectedTemplate.entryContent);
      useIDEStore.getState().setActiveProject(projPath);
      useIDEStore.getState().addLog(`[PROJECT] Nuovo progetto "${projectName}" creato`);
      setCollapsed(true);
      setStep("list");
    } catch (e) {
      useIDEStore.getState().addLog(`[ERROR] Creazione progetto fallita: ${e}`);
    }
  };

  const handleOpenProject = async () => {
    const path = await openFileDialog();
    if (path) {
      try {
        const content = await import("../services/tauriBridge").then(m => m.readFile(path));
        const name = path.split("/").pop() || path.split("\\").pop() || "project";
        useIDEStore.getState().openFile(path, content);
        useIDEStore.getState().setActiveProject(path);
        useIDEStore.getState().addLog(`[PROJECT] Progetto caricato: ${name}`);
        setCollapsed(true);
      } catch (e) {
        useIDEStore.getState().addLog(`[ERROR] Caricamento progetto fallito: ${e}`);
      }
    }
  };

  const handleMouseDown = (e: React.MouseEvent) => {
    dragging.current = true;
    dragStart.current = { x: e.clientX, y: e.clientY, left: pos.x, top: pos.y };
    document.body.style.cursor = "grabbing";
    document.body.style.userSelect = "none";
  };

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!dragging.current) return;
      setPos({
        x: Math.max(0, dragStart.current.left + (e.clientX - dragStart.current.x)),
        y: Math.max(0, dragStart.current.top + (e.clientY - dragStart.current.y)),
      });
    };
    const handleMouseUp = () => {
      if (dragging.current) {
        dragging.current = false;
        document.body.style.cursor = "";
        document.body.style.userSelect = "";
      }
    };
    window.addEventListener("mousemove", handleMouseMove);
    window.addEventListener("mouseup", handleMouseUp);
    return () => {
      window.removeEventListener("mousemove", handleMouseMove);
      window.removeEventListener("mouseup", handleMouseUp);
    };
  }, [pos]);

  if (collapsed) {
    return (
      <button
        onClick={() => setCollapsed(false)}
        className="fixed bottom-16 right-72 z-50 bg-editor-sidebar border border-editor-border text-editor-text px-3 py-1.5 rounded-full text-xs font-medium shadow-lg hover:border-editor-accent transition-colors"
        title="Nuovo Progetto"
      >
        📁 New
      </button>
    );
  }

  return (
    <div
      className="fixed z-50 w-80 bg-editor-sidebar border border-editor-border rounded-lg shadow-2xl overflow-hidden"
      style={{ left: pos.x, top: pos.y }}
    >
      <div
        className="flex items-center justify-between px-3 py-2 border-b border-editor-border bg-editor-bg cursor-grab"
        onMouseDown={handleMouseDown}
      >
        <span className="text-xs font-semibold text-editor-text uppercase tracking-wider">
          📁 Nuovo Progetto
        </span>
        <div className="flex items-center gap-2">
          <button
            onClick={handleOpenProject}
            className="text-[10px] text-gray-500 hover:text-editor-accent px-1"
            title="Apri progetto esistente"
          >
            Apri
          </button>
          <button
            onClick={() => { setCollapsed(true); setStep("list"); }}
            className="text-gray-500 hover:text-editor-text text-xs px-1"
          >
            ✕
          </button>
        </div>
      </div>

      <div className="p-3 space-y-3">
        {step === "list" ? (
          <>
            <p className="text-[11px] text-gray-500">Scegli un template:</p>
            <div className="space-y-2">
              {TEMPLATES.map((t) => (
                <button
                  key={t.name}
                  onClick={() => handleSelect(t)}
                  className="w-full text-left p-2 bg-editor-bg border border-editor-border rounded hover:border-editor-accent/50 transition-colors"
                >
                  <div className="text-xs font-medium text-editor-text">{t.name}</div>
                  <div className="text-[10px] text-gray-500 mt-0.5">{t.description}</div>
                </button>
              ))}
            </div>
          </>
        ) : (
          <>
            <div>
              <label className="text-[10px] text-gray-500 uppercase">Nome progetto</label>
              <input
                type="text"
                value={projectName}
                onChange={(e) => setProjectName(e.target.value)}
                className="w-full mt-1 bg-editor-bg border border-editor-border rounded px-2 py-1.5 text-xs text-editor-text outline-none focus:border-editor-accent"
              />
            </div>
            <div>
              <label className="text-[10px] text-gray-500 uppercase">Template</label>
              <div className="mt-1 text-xs text-editor-text">{selectedTemplate?.name}</div>
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => setStep("list")}
                className="flex-1 px-2 py-1.5 bg-editor-border text-gray-400 text-xs rounded hover:bg-editor-border/50 transition-colors"
              >
                ← Indietro
              </button>
              <button
                onClick={handleCreate}
                className="flex-1 px-2 py-1.5 bg-editor-accent text-white text-xs rounded hover:bg-editor-accent/80 transition-colors"
              >
                Crea
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
