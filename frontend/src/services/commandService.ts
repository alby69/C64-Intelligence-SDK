import { execPluginCommand } from "./pluginService";
import { useIDEStore } from "../store/ideStore";

export async function runCompile(inputPath: string): Promise<void> {
  const { addLog, setCompiling } = useIDEStore.getState();
  setCompiling(true);
  addLog(`[BUILD] Compilazione ${inputPath}...`);

  const result = await execPluginCommand("compiler", "compile", [inputPath]);
  setCompiling(false);

  if (result.success) {
    if (result.stdout) {
      result.stdout.split("\n").filter(Boolean).forEach((line) => addLog(line));
    }
    addLog("[OK] Compilazione completata");
  } else {
    addLog(`[ERROR] ${result.error || result.stderr}`);
  }
}

export async function runTokenize(inputPath: string, outputPath: string): Promise<void> {
  const { addLog } = useIDEStore.getState();
  addLog(`[EDITOR] Tokenizzazione ${inputPath}...`);

  const result = await execPluginCommand("editor", "tokenize", [inputPath], { output: outputPath });
  if (result.success) {
    if (result.stdout) {
      result.stdout.split("\n").filter(Boolean).forEach((line) => addLog(line));
    }
  } else {
    addLog(`[ERROR] ${result.error || result.stderr}`);
  }
}

export async function runMinify(inputPath: string, outputPath: string): Promise<void> {
  const { addLog } = useIDEStore.getState();
  const result = await execPluginCommand("editor", "minify", [inputPath], { output: outputPath });
  if (result.success) {
    if (result.stdout) {
      result.stdout.split("\n").filter(Boolean).forEach((line) => addLog(line));
    }
  } else {
    addLog(`[ERROR] ${result.error || result.stderr}`);
  }
}

export async function runDiskList(imagePath: string): Promise<void> {
  const { addLog } = useIDEStore.getState();
  const result = await execPluginCommand("disk-tools", "list", [imagePath]);
  if (result.success) {
    if (result.stdout) {
      result.stdout.split("\n").filter(Boolean).forEach((line) => addLog(line));
    }
  } else {
    addLog(`[ERROR] ${result.error || result.stderr}`);
  }
}

export async function runEmulator(inputPath: string): Promise<void> {
  const { addLog, setCompiling } = useIDEStore.getState();
  setCompiling(true);
  addLog(`[EMU] Avvio ${inputPath}...`);

  const result = await execPluginCommand("emulator", "run", [inputPath]);
  setCompiling(false);

  if (result.stdout) {
    result.stdout.split("\n").filter(Boolean).forEach((line) => addLog(line));
  }
  if (result.stderr && !result.success) {
    addLog(`[ERROR] ${result.stderr}`);
  }
}
