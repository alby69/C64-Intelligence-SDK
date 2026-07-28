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

// ── AI Agent Plugin ──

export async function runAIAgentGenerate(
  prompt: string,
  options?: { mode?: string; output?: string }
): Promise<void> {
  const { addLog } = useIDEStore.getState();
  addLog(`[AI] Generazione codice da prompt...`);

  const cliArgs = ["generate", prompt];
  if (options?.mode) cliArgs.push("--mode", options.mode);
  if (options?.output) cliArgs.push("-o", options.output);

  const result = await execPluginCommand("ai-agent", "generate", undefined, undefined, cliArgs);
  if (result.stdout) addLines(result.stdout.split("\n"));
  if (result.stderr) addLines(result.stderr.split("\n"));
  if (!result.success) addError(result.error || "Generazione fallita");
}

export async function runAIAgentExplain(inputPath: string): Promise<void> {
  const { addLog } = useIDEStore.getState();
  addLog(`[AI] Spiegazione ${inputPath.split("/").pop()}...`);

  const result = await execPluginCommand("ai-agent", "explain", undefined, undefined, [
    "explain", inputPath,
  ]);
  if (result.stdout) addLines(result.stdout.split("\n"));
  if (result.stderr) addLines(result.stderr.split("\n"));
  if (!result.success) addError(result.error || "Spiegazione fallita");
}

export async function runAIAgentDebug(inputPath: string, crashPath?: string): Promise<void> {
  const { addLog } = useIDEStore.getState();
  addLog(`[AI] Debug ${inputPath.split("/").pop()}...`);

  const cliArgs = ["debug", inputPath];
  if (crashPath) cliArgs.push("--crash", crashPath);

  const result = await execPluginCommand("ai-agent", "debug", undefined, undefined, cliArgs);
  if (result.stdout) addLines(result.stdout.split("\n"));
  if (result.stderr) addLines(result.stderr.split("\n"));
  if (!result.success) addError(result.error || "Debug AI fallito");
}

export async function runAIAgentSearch(query: string): Promise<void> {
  const { addLog } = useIDEStore.getState();
  addLog(`[AI] Ricerca KB: ${query}`);

  const result = await execPluginCommand("ai-agent", "search", undefined, undefined, [
    "search", query,
  ]);
  if (result.stdout) addLines(result.stdout.split("\n"));
  if (result.stderr) addLines(result.stderr.split("\n"));
}

// ── Debugger Plugin ──

export async function runDebuggerRun(prgPath: string): Promise<void> {
  const { addLog } = useIDEStore.getState();
  addLog(`[DEBUG] Avvio ${prgPath.split("/").pop()} in VICE...`);

  const result = await execPluginCommand("debugger", "run", undefined, undefined, [
    "run", prgPath,
  ]);
  if (result.stdout) addLines(result.stdout.split("\n"));
  if (result.stderr) addLines(result.stderr.split("\n"));
  if (!result.success) addError(result.error || "Avvio debugger fallito");
}

export async function runDebuggerStep(): Promise<void> {
  const { addLog } = useIDEStore.getState();
  addLog(`[DEBUG] Step...`);

  const result = await execPluginCommand("debugger", "step");
  if (result.stdout) addLines(result.stdout.split("\n"));
  if (result.stderr) addLines(result.stderr.split("\n"));
}

export async function runDebuggerRegisters(): Promise<void> {
  const { addLog } = useIDEStore.getState();
  addLog(`[DEBUG] Lettura registri...`);

  const result = await execPluginCommand("debugger", "registers");
  if (result.stdout) addLines(result.stdout.split("\n"));
  if (result.stderr) addLines(result.stderr.split("\n"));
}

export async function runDebuggerMemory(address: string, size?: number): Promise<void> {
  const { addLog } = useIDEStore.getState();
  addLog(`[DEBUG] Lettura memoria ${address}...`);

  const cliArgs = ["memory", address];
  if (size) cliArgs.push("--size", String(size));

  const result = await execPluginCommand("debugger", "memory", undefined, undefined, cliArgs);
  if (result.stdout) addLines(result.stdout.split("\n"));
  if (result.stderr) addLines(result.stderr.split("\n"));
}

export async function runDebuggerBreakpoint(address: string, remove?: boolean): Promise<void> {
  const { addLog } = useIDEStore.getState();
  addLog(`[DEBUG] Breakpoint ${remove ? "rimuovi" : "imposta"} ${address}...`);

  const cliArgs = ["breakpoint", address];
  if (remove) cliArgs.push("--remove");

  const result = await execPluginCommand("debugger", "breakpoint", undefined, undefined, cliArgs);
  if (result.stdout) addLines(result.stdout.split("\n"));
  if (result.stderr) addLines(result.stderr.split("\n"));
}

export async function runDebuggerCrashAnalyze(dumpPath: string): Promise<void> {
  const { addLog } = useIDEStore.getState();
  addLog(`[DEBUG] Analisi crash dump...`);

  const result = await execPluginCommand("debugger", "crash-analyze", undefined, undefined, [
    "crash-analyze", dumpPath,
  ]);
  if (result.stdout) addLines(result.stdout.split("\n"));
  if (result.stderr) addLines(result.stderr.split("\n"));
}

export async function runDebuggerReset(): Promise<void> {
  const { addLog } = useIDEStore.getState();
  addLog(`[DEBUG] Reset VICE...`);

  const result = await execPluginCommand("debugger", "reset");
  if (result.stdout) addLines(result.stdout.split("\n"));
  if (result.stderr) addLines(result.stderr.split("\n"));
}

// ── Knowledge Plugin ──

export async function runKnowledgeSearch(query: string): Promise<void> {
  const { addLog } = useIDEStore.getState();
  addLog(`[KB] Ricerca: ${query}`);

  const result = await execPluginCommand("knowledge", "search", undefined, undefined, [
    "search", query,
  ]);
  if (result.stdout) addLines(result.stdout.split("\n"));
  if (result.stderr) addLines(result.stderr.split("\n"));
}

export async function runKnowledgeDocs(topic: string): Promise<void> {
  const { addLog } = useIDEStore.getState();
  addLog(`[KB] Documentazione: ${topic}`);

  const result = await execPluginCommand("knowledge", "docs", undefined, undefined, [
    "docs", topic,
  ]);
  if (result.stdout) addLines(result.stdout.split("\n"));
  if (result.stderr) addLines(result.stderr.split("\n"));
}

// ── Tutorial Plugin ──

export async function runTutorialList(part?: number): Promise<void> {
  const { addLog } = useIDEStore.getState();
  addLog(`[TUTORIAL] Elenco capitoli${part ? ` (parte ${part})` : ""}...`);

  const cliArgs: string[] = ["list"];
  if (part) cliArgs.push("--part", String(part));

  const result = await execPluginCommand("tutorial", "list", undefined, undefined, cliArgs);
  if (result.stdout) addLines(result.stdout.split("\n"));
  if (result.stderr) addLines(result.stderr.split("\n"));
}

export async function runTutorialShow(chapter: string, lang?: string): Promise<void> {
  const { addLog } = useIDEStore.getState();
  addLog(`[TUTORIAL] Capitolo ${chapter}...`);

  const cliArgs = ["show", chapter];
  if (lang) cliArgs.push("--lang", lang);

  const result = await execPluginCommand("tutorial", "show", undefined, undefined, cliArgs);
  if (result.stdout) addLines(result.stdout.split("\n"));
  if (result.stderr) addLines(result.stderr.split("\n"));
}

// ── GeckOS Plugin ──

export async function runGeckosBuild(clean?: boolean): Promise<void> {
  const { addLog } = useIDEStore.getState();
  addLog(`[GECKOS] Build GeckOS-NG${clean ? " (clean)" : ""}...`);

  const cliArgs: string[] = ["build"];
  if (clean) cliArgs.push("--clean");

  const result = await execPluginCommand("geckos", "build", undefined, undefined, cliArgs);
  if (result.stdout) addLines(result.stdout.split("\n"));
  if (result.stderr) addLines(result.stderr.split("\n"));
  if (!result.success) addError(result.error || "Build GeckOS fallita");
}

export async function runGeckosDeploy(outputPath: string): Promise<void> {
  const { addLog } = useIDEStore.getState();
  addLog(`[GECKOS] Deploy su ${outputPath}...`);

  const result = await execPluginCommand("geckos", "deploy", undefined, undefined, [
    "deploy", outputPath,
  ]);
  if (result.stdout) addLines(result.stdout.split("\n"));
  if (result.stderr) addLines(result.stderr.split("\n"));
}

// ── VICE Emulator (extended) ──

export async function runViceRun(prgPath: string, headless?: boolean): Promise<void> {
  const { addLog } = useIDEStore.getState();
  addLog(`[VICE] Esecuzione ${prgPath.split("/").pop()}...`);

  const cliArgs = ["vice-run", prgPath];
  if (headless) cliArgs.push("--headless");

  const result = await execPluginCommand("emulator", "vice-run", undefined, undefined, cliArgs);
  if (result.stdout) addLines(result.stdout.split("\n"));
  if (result.stderr) addLines(result.stderr.split("\n"));
}

export async function runViceAttach(): Promise<void> {
  const { addLog } = useIDEStore.getState();
  addLog(`[VICE] Connessione al monitor...`);

  const result = await execPluginCommand("emulator", "vice-attach");
  if (result.stdout) addLines(result.stdout.split("\n"));
  if (result.stderr) addLines(result.stderr.split("\n"));
}

export async function runViceStep(): Promise<void> {
  const { addLog } = useIDEStore.getState();
  addLog(`[VICE] Step...`);

  const result = await execPluginCommand("emulator", "vice-step");
  if (result.stdout) addLines(result.stdout.split("\n"));
  if (result.stderr) addLines(result.stderr.split("\n"));
}

export async function runViceRegisters(): Promise<void> {
  const { addLog } = useIDEStore.getState();
  addLog(`[VICE] Lettura registri...`);

  const result = await execPluginCommand("emulator", "vice-registers");
  if (result.stdout) addLines(result.stdout.split("\n"));
  if (result.stderr) addLines(result.stderr.split("\n"));
}

export async function runViceMemory(address: string, size?: number): Promise<void> {
  const { addLog } = useIDEStore.getState();
  addLog(`[VICE] Lettura memoria ${address}...`);

  const cliArgs = ["vice-memory", address];
  if (size) cliArgs.push("--size", String(size));

  const result = await execPluginCommand("emulator", "vice-memory", undefined, undefined, cliArgs);
  if (result.stdout) addLines(result.stdout.split("\n"));
  if (result.stderr) addLines(result.stderr.split("\n"));
}

// ── Disk Tools (extended) ──

export async function runDiskFormat(imagePath: string, label?: string): Promise<void> {
  const { addLog } = useIDEStore.getState();
  addLog(`[DISK] Formattazione ${imagePath.split("/").pop()}...`);

  const cliArgs = ["format", imagePath];
  if (label) cliArgs.push("--label", label);

  const result = await execPluginCommand("disk-tools", "format", undefined, undefined, cliArgs);
  if (result.stdout) addLines(result.stdout.split("\n"));
  if (result.stderr) addLines(result.stderr.split("\n"));
}

export async function runDiskPrgToDisk(
  outputImage: string,
  files: string[],
  label?: string
): Promise<void> {
  const { addLog } = useIDEStore.getState();
  addLog(`[DISK] Creazione disco da ${files.length} PRG...`);

  const cliArgs = ["prg-to-disk", outputImage, "--files", files.join(",")];
  if (label) cliArgs.push("--label", label);

  const result = await execPluginCommand("disk-tools", "prg-to-disk", undefined, undefined, cliArgs);
  if (result.stdout) addLines(result.stdout.split("\n"));
  if (result.stderr) addLines(result.stderr.split("\n"));
}

export async function runPetSCIIConvert(
  inputPath: string,
  direction: "to-petscii" | "to-ascii",
  outputPath?: string
): Promise<void> {
  const { addLog } = useIDEStore.getState();
  addLog(`[DISK] Conversione PETSCII ${inputPath.split("/").pop()}...`);

  const cliArgs = ["petscii-convert", inputPath, direction];
  if (outputPath) cliArgs.push("-o", outputPath);

  const result = await execPluginCommand("disk-tools", "petscii-convert", undefined, undefined, cliArgs);
  if (result.stdout) addLines(result.stdout.split("\n"));
  if (result.stderr) addLines(result.stderr.split("\n"));
}
