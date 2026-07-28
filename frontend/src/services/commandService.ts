import { execPluginCommand } from "./pluginService";
import { useIDEStore } from "../store/ideStore";

function addLines(logs: string[]) {
  const { addLog } = useIDEStore.getState();
  logs.filter(Boolean).forEach((l) => addLog(l));
}

function addError(msg: string) {
  useIDEStore.getState().addLog(`[ERROR] ${msg}`);
}

// ── Compiler Plugin ──

export async function runCompile(inputPath: string): Promise<void> {
  const { addLog, setCompiling } = useIDEStore.getState();
  setCompiling(true);
  addLog(`[BUILD] Compilazione ${inputPath.split("/").pop()}...`);

  const result = await execPluginCommand("compiler", "compile", undefined, undefined, [
    "compile", inputPath,
  ]);

  setCompiling(false);

  if (result.stdout) addLines(result.stdout.split("\n"));
  if (result.stderr && !result.success) addLines(result.stderr.split("\n"));
  if (!result.success) addError(result.error || "Compilazione fallita");
}

export async function runBasicOnly(inputPath: string): Promise<void> {
  const { addLog } = useIDEStore.getState();
  addLog(`[BUILD] Generazione BASIC da ${inputPath.split("/").pop()}...`);

  const result = await execPluginCommand("compiler", "basic", undefined, undefined, [
    "basic", inputPath,
  ]);

  if (result.stdout) addLines(result.stdout.split("\n"));
  if (result.stderr && !result.success) addLines(result.stderr.split("\n"));
  if (!result.success) addError(result.error || "Generazione BASIC fallita");
}

// ── Editor Plugin ──

export async function runTokenize(inputPath: string, outputPath: string): Promise<void> {
  const { addLog } = useIDEStore.getState();
  addLog(`[EDITOR] Tokenizzazione ${inputPath.split("/").pop()}...`);

  const result = await execPluginCommand("editor", "tokenize", undefined, undefined, [
    "tokenize", inputPath, "-o", outputPath,
  ]);

  if (result.stdout) addLines(result.stdout.split("\n"));
  if (result.stderr) addLines(result.stderr.split("\n"));
  if (!result.success) addError(result.error || "Tokenizzazione fallita");
}

export async function runDetokenize(inputPath: string, outputPath: string): Promise<void> {
  const { addLog } = useIDEStore.getState();
  addLog(`[EDITOR] Detokenizzazione ${inputPath.split("/").pop()}...`);

  const result = await execPluginCommand("editor", "detokenize", undefined, undefined, [
    "detokenize", inputPath, "-o", outputPath,
  ]);

  if (result.stdout) addLines(result.stdout.split("\n"));
  if (result.stderr) addLines(result.stderr.split("\n"));
  if (!result.success) addError(result.error || "Detokenizzazione fallita");
}

export async function runMinify(inputPath: string, outputPath: string): Promise<void> {
  const { addLog } = useIDEStore.getState();
  addLog(`[EDITOR] Minificazione ${inputPath.split("/").pop()}...`);

  const result = await execPluginCommand("editor", "minify", undefined, undefined, [
    "minify", inputPath, "-o", outputPath,
  ]);

  if (result.stdout) addLines(result.stdout.split("\n"));
  if (result.stderr) addLines(result.stderr.split("\n"));
  if (!result.success) addError(result.error || "Minificazione fallita");
}

export async function runPrettify(inputPath: string, outputPath: string): Promise<void> {
  const { addLog } = useIDEStore.getState();
  addLog(`[EDITOR] Formattazione ${inputPath.split("/").pop()}...`);

  const result = await execPluginCommand("editor", "prettify", undefined, undefined, [
    "prettify", inputPath, "-o", outputPath,
  ]);

  if (result.stdout) addLines(result.stdout.split("\n"));
  if (result.stderr) addLines(result.stderr.split("\n"));
  if (!result.success) addError(result.error || "Formattazione fallita");
}

// ── Disk Plugin ──

export async function runDiskList(imagePath: string): Promise<void> {
  const { addLog } = useIDEStore.getState();
  addLog(`[DISK] Lettura ${imagePath.split("/").pop()}...`);

  const result = await execPluginCommand("disk-tools", "list", undefined, undefined, [
    "disk", "list", imagePath,
  ]);

  if (result.stdout) addLines(result.stdout.split("\n"));
  if (result.stderr) addLines(result.stderr.split("\n"));
  if (!result.success) addError(result.error || "Lettura disco fallita");
}

export async function runDiskExtract(
  imagePath: string,
  fileName: string,
  outputPath?: string
): Promise<void> {
  const { addLog } = useIDEStore.getState();
  addLog(`[DISK] Estrazione ${fileName} da ${imagePath.split("/").pop()}...`);

  const cliArgs = ["disk", "extract", imagePath, fileName];
  if (outputPath) cliArgs.push("-o", outputPath);

  const result = await execPluginCommand("disk-tools", "extract", undefined, undefined, cliArgs);

  if (result.stdout) addLines(result.stdout.split("\n"));
  if (result.stderr) addLines(result.stderr.split("\n"));
  if (!result.success) addError(result.error || "Estrazione fallita");
}

export async function runDiskInject(imagePath: string, filePath: string): Promise<void> {
  const { addLog } = useIDEStore.getState();
  addLog(`[DISK] Inserimento ${filePath.split("/").pop()} in ${imagePath.split("/").pop()}...`);

  const result = await execPluginCommand("disk-tools", "inject", undefined, undefined, [
    "disk", "inject", imagePath, filePath,
  ]);

  if (result.stdout) addLines(result.stdout.split("\n"));
  if (result.stderr) addLines(result.stderr.split("\n"));
  if (!result.success) addError(result.error || "Inserimento fallito");
}

export async function runDiskCreate(
  outputPath: string,
  format: "d64" | "d81" = "d64",
  label?: string
): Promise<void> {
  const { addLog } = useIDEStore.getState();
  addLog(`[DISK] Creazione disco ${format.toUpperCase()}...`);

  const cliArgs = ["disk", "create", label || "UNTITLED"];
  cliArgs.push("-o", outputPath);
  cliArgs.push("--format", format);

  const result = await execPluginCommand("disk-tools", "create", undefined, undefined, cliArgs);

  if (result.stdout) addLines(result.stdout.split("\n"));
  if (result.stderr) addLines(result.stderr.split("\n"));
  if (!result.success) addError(result.error || "Creazione disco fallita");
}

// ── Emulator Plugin ──

export async function runEmulator(
  inputPath: string,
  options?: { sid?: boolean; resid?: boolean; timeout?: number }
): Promise<void> {
  const { addLog, setCompiling } = useIDEStore.getState();
  setCompiling(true);
  addLog(`[EMU] Avvio ${inputPath.split("/").pop()}...`);

  const cliArgs = ["run", inputPath];
  if (options?.sid) cliArgs.push("--sid");
  if (options?.resid) cliArgs.push("--resid");
  if (options?.timeout) cliArgs.push("--timeout", String(options.timeout));

  const result = await execPluginCommand("emulator", "run", undefined, undefined, cliArgs);

  setCompiling(false);

  if (result.stdout) addLines(result.stdout.split("\n"));
  if (result.stderr) addLines(result.stderr.split("\n"));
}

// ── Project Manager Plugin ──

export async function runProjectLoad(projectPath: string): Promise<void> {
  const { addLog, setActiveProject } = useIDEStore.getState();
  addLog(`[PROJECT] Caricamento ${projectPath.split("/").pop()}...`);

  const result = await execPluginCommand("project-manager", "load", undefined, undefined, [
    "load", projectPath,
  ]);

  if (result.stdout) addLines(result.stdout.split("\n"));
  if (result.stderr) addLines(result.stderr.split("\n"));

  if (result.success) {
    setActiveProject(projectPath);
    addLog(`[OK] Progetto caricato`);
  } else {
    addError(result.error || "Caricamento progetto fallito");
  }
}

export async function runProjectBuild(projectPath: string): Promise<void> {
  const { addLog, setCompiling } = useIDEStore.getState();
  setCompiling(true);
  addLog(`[PROJECT] Build ${projectPath.split("/").pop()}...`);

  const result = await execPluginCommand("project-manager", "build", undefined, undefined, [
    "build", projectPath,
  ]);

  setCompiling(false);

  if (result.stdout) addLines(result.stdout.split("\n"));
  if (result.stderr) addLines(result.stderr.split("\n"));

  if (result.success) {
    addLog(`[OK] Build completato`);
  } else {
    addError(result.error || "Build progetto fallito");
  }
}
