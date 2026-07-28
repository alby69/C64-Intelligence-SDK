import { invoke } from "@tauri-apps/api/tauri";
import { open, save } from "@tauri-apps/api/dialog";

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

export async function runCommand(
  program: string,
  args: string[],
  cwd?: string
): Promise<CommandResult> {
  return invoke<CommandResult>("run_command", { program, args, cwd });
}

export async function readFile(path: string): Promise<string> {
  return invoke<string>("read_file", { path });
}

export async function writeFile(path: string, content: string): Promise<void> {
  return invoke<void>("write_file", { path, content });
}

export async function listDirectory(path: string): Promise<DirEntry[]> {
  return invoke<DirEntry[]>("list_directory", { path });
}

export async function openFileDialog(): Promise<string | null> {
  const result = await open({
    multiple: false,
    filters: [
      { name: "C64 Source", extensions: ["c64", "bas", "asm", "asm65"] },
      { name: "All Files", extensions: ["*"] },
    ],
  });
  return typeof result === "string" ? result : null;
}

export async function saveFileDialog(defaultName?: string): Promise<string | null> {
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

export async function runPythonScript(
  script: string,
  args: string[] = [],
  cwd?: string
): Promise<CommandResult> {
  return runCommand("python3", [script, ...args], cwd);
}

export async function runC64Compiler(
  inputPath: string,
  cwd?: string
): Promise<CommandResult> {
  return runCommand("python3", ["run_c64.py", "compile", inputPath], cwd);
}

export async function runC64Emulator(
  inputPath: string,
  cwd?: string
): Promise<CommandResult> {
  return runCommand("python3", ["run_c64.py", "run", inputPath], cwd);
}
