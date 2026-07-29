function isTauri(): boolean {
  return typeof window !== "undefined" && "__TAURI__" in window;
}

export interface CommandResult {
  success: boolean;
  stdout: string;
  stderr: string;
  code: number;
}

export interface DirEntry {
  name: string;
  is_dir: boolean;
  size: number;
}

async function tauriInvoke<T>(cmd: string, args?: Record<string, unknown>): Promise<T> {
  if (!isTauri()) throw new Error("Not running in Tauri");
  const { invoke } = await import("@tauri-apps/api/tauri");
  return await invoke<T>(cmd, args);
}

function createFileInput(accept: string, multiple = false): Promise<string | null> {
  const input = document.createElement("input");
  input.type = "file";
  input.accept = accept;
  input.multiple = multiple;
  input.style.display = "none";
  document.body.appendChild(input);
  return new Promise((resolve) => {
    input.addEventListener("change", () => {
      const file = input.files?.[0];
      if (file) {
        const path = (file as any).path || file.name;
        resolve(path);
      } else {
        resolve(null);
      }
      document.body.removeChild(input);
    });
    input.addEventListener("cancel", () => {
      resolve(null);
      document.body.removeChild(input);
    });
    input.click();
  });
}

function createSaveFileDialog(defaultName?: string): Promise<string | null> {
  const name = prompt("Salva come:", defaultName || "untitled.c64");
  return Promise.resolve(name || null);
}

export async function runCommand(
  program: string,
  args: string[],
  cwd?: string
): Promise<CommandResult> {
  if (isTauri()) {
    return tauriInvoke<CommandResult>("run_command", { program, args, cwd });
  }
  console.warn("[tauriBridge] runCommand not available in browser mode:", program, args);
  return { success: false, stdout: "", stderr: "Not available in browser mode", code: -1 };
}

export async function readFile(path: string): Promise<string> {
  if (isTauri()) {
    return tauriInvoke<string>("read_file", { path });
  }
  try {
    const resp = await fetch(path);
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    return await resp.text();
  } catch {
    return new Promise((resolve, reject) => {
      const input = document.createElement("input");
      input.type = "file";
      input.accept = ".c64,.bas,.asm,.txt,.d64,.prg";
      input.style.display = "none";
      document.body.appendChild(input);
      input.addEventListener("change", () => {
        const file = input.files?.[0];
        if (!file) { reject(new Error("No file selected")); return; }
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result as string);
        reader.onerror = () => reject(reader.error);
        reader.readAsText(file);
        document.body.removeChild(input);
      });
      input.click();
    });
  }
}

export async function writeFile(path: string, content: string): Promise<void> {
  if (isTauri()) {
    return tauriInvoke<void>("write_file", { path, content });
  }
  const blob = new Blob([content], { type: "text/plain" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = path.split("/").pop() || path.split("\\").pop() || "file.c64";
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

export async function listDirectory(path: string): Promise<DirEntry[]> {
  if (isTauri()) {
    return tauriInvoke<DirEntry[]>("list_directory", { path });
  }
  console.warn("[tauriBridge] listDirectory not available in browser mode");
  return [];
}

export async function openFileDialog(): Promise<string | null> {
  if (isTauri()) {
    const { open } = await import("@tauri-apps/api/dialog");
    const result = await open({
      multiple: false,
      filters: [
        { name: "C64 Source", extensions: ["c64", "bas", "asm", "asm65"] },
        { name: "All Files", extensions: ["*"] },
      ],
    });
    return typeof result === "string" ? result : null;
  }
  return createFileInput(".c64,.bas,.asm,.asm65,.d64,.d81,.prg,.c64proj");
}

export async function saveFileDialog(defaultName?: string): Promise<string | null> {
  if (isTauri()) {
    const { save } = await import("@tauri-apps/api/dialog");
    const result = await save({
      defaultPath: defaultName,
      filters: [
        { name: "C64 Source", extensions: ["c64"] },
        { name: "BASIC", extensions: ["bas"] },
        { name: "Assembly", extensions: ["asm"] },
      ],
    });
    return typeof result === "string" ? result : null;
  }
  return createSaveFileDialog(defaultName);
}

export async function runPythonScript(
  script: string,
  args: string[] = [],
  cwd?: string
): Promise<CommandResult> {
  return runCommand(isTauri() ? "python3" : "python", [script, ...args], cwd);
}

export async function runC64Compiler(
  inputPath: string,
  cwd?: string
): Promise<CommandResult> {
  return runCommand(isTauri() ? "python3" : "python", ["run_c64.py", "compile", inputPath], cwd);
}

export async function runC64Emulator(
  inputPath: string,
  cwd?: string
): Promise<CommandResult> {
  return runCommand(isTauri() ? "python3" : "python", ["run_c64.py", "run", inputPath], cwd);
}
