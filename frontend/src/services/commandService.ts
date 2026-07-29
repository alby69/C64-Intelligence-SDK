import { execPluginCommand, PluginExecResult } from "./pluginService";
import { useIDEStore } from "../store/ideStore";

function log(lines: string[]) {
  const { addLog } = useIDEStore.getState();
  lines.filter(Boolean).forEach((l) => addLog(l));
}

function error(msg: string) {
  useIDEStore.getState().addLog(`[ERROR] ${msg}`);
}

async function run(
  plugin: string,
  cmd: string,
  args: string[],
  successMsg?: string
): Promise<PluginExecResult> {
  const result = await execPluginCommand(plugin, cmd, undefined, undefined, [cmd, ...args]);
  if (result.stdout) log(result.stdout.split("\n"));
  if (result.stderr) log(result.stderr.split("\n"));
  if (!result.success) {
    error(result.error || `${cmd} fallito`);
  } else if (successMsg) {
    log([successMsg]);
  }
  return result;
}

// ── Compiler ──
export async function runCompile(inputPath: string): Promise<void> {
  const { setCompiling } = useIDEStore.getState();
  setCompiling(true);
  log([`[BUILD] Compilazione ${inputPath}...`]);
  await run("compiler", "compile", [inputPath]);
  setCompiling(false);
}

export async function runBasicOnly(inputPath: string): Promise<void> {
  log([`[BUILD] BASIC da ${inputPath}...`]);
  await run("compiler", "basic", [inputPath]);
}

// ── Editor ──
export async function runTokenize(inputPath: string, outputPath: string): Promise<void> {
  log([`[EDITOR] Tokenizzazione ${inputPath}...`]);
  await run("editor", "tokenize", [inputPath, "-o", outputPath]);
}

export async function runDetokenize(inputPath: string, outputPath: string): Promise<void> {
  log([`[EDITOR] Detokenizzazione ${inputPath}...`]);
  await run("editor", "detokenize", [inputPath, "-o", outputPath]);
}

export async function runMinify(inputPath: string, outputPath: string): Promise<void> {
  log([`[EDITOR] Minificazione ${inputPath}...`]);
  await run("editor", "minify", [inputPath, "-o", outputPath]);
}

export async function runPrettify(inputPath: string, outputPath: string): Promise<void> {
  log([`[EDITOR] Formattazione ${inputPath}...`]);
  await run("editor", "prettify", [inputPath, "-o", outputPath]);
}

// ── Disk Tools ──
export async function runDiskList(imagePath: string): Promise<void> {
  log([`[DISK] Lettura ${imagePath}...`]);
  await run("disk-tools", "list", [imagePath]);
}

export async function runDiskExtract(
  imagePath: string, fileName: string, outputPath?: string
): Promise<void> {
  const args = [imagePath, fileName];
  if (outputPath) args.push("-o", outputPath);
  log([`[DISK] Estrazione ${fileName}...`]);
  await run("disk-tools", "extract", args);
}

export async function runDiskInject(imagePath: string, filePath: string): Promise<void> {
  log([`[DISK] Iniezione ${filePath}...`]);
  await run("disk-tools", "inject", [imagePath, filePath]);
}

export async function runDiskCreate(
  outputPath: string, format: "d64" | "d81" = "d64", label?: string
): Promise<void> {
  log([`[DISK] Creazione ${format.toUpperCase()}...`]);
  const args = ["-o", outputPath, "--format", format];
  if (label) args.push("--label", label);
  await run("disk-tools", "create", args);
}

export async function runDiskFormat(imagePath: string, label?: string): Promise<void> {
  const args = [imagePath];
  if (label) args.push("--label", label);
  log([`[DISK] Formattazione ${imagePath}...`]);
  await run("disk-tools", "format", args);
}

export async function runDiskPrgToDisk(
  outputImage: string, files: string[], label?: string
): Promise<void> {
  const args = [outputImage, "--files", files.join(",")];
  if (label) args.push("--label", label);
  log([`[DISK] Disco da ${files.length} PRG...`]);
  await run("disk-tools", "prg-to-disk", args);
}

export async function runPetSCIIConvert(
  inputPath: string, direction: "to-petscii" | "to-ascii", outputPath?: string
): Promise<void> {
  const args = [inputPath, direction];
  if (outputPath) args.push("-o", outputPath);
  log([`[DISK] PETSCII ${inputPath}...`]);
  await run("disk-tools", "petscii-convert", args);
}

// ── Emulator ──
export async function runEmulator(
  inputPath: string, options?: { sid?: boolean; resid?: boolean; timeout?: number }
): Promise<void> {
  const { setCompiling } = useIDEStore.getState();
  setCompiling(true);
  const args = [inputPath];
  if (options?.sid) args.push("--sid");
  if (options?.resid) args.push("--resid");
  if (options?.timeout) args.push("--timeout", String(options.timeout));
  log([`[EMU] Avvio ${inputPath}...`]);
  await run("emulator", "run", args);
  setCompiling(false);
}

export async function runViceRun(prgPath: string, headless?: boolean): Promise<void> {
  const args = [prgPath];
  if (headless) args.push("--headless");
  log([`[VICE] Esecuzione ${prgPath}...`]);
  await run("emulator", "vice-run", args);
}

export async function runViceAttach(): Promise<void> {
  log([`[VICE] Connessione...`]);
  await run("emulator", "vice-attach", []);
}

export async function runViceStep(): Promise<void> {
  log([`[VICE] Step...`]);
  await run("emulator", "vice-step", []);
}

export async function runViceRegisters(): Promise<void> {
  log([`[VICE] Registri...`]);
  await run("emulator", "vice-registers", []);
}

export async function runViceMemory(address: string, size?: number): Promise<void> {
  const args = [address];
  if (size) args.push("--size", String(size));
  log([`[VICE] Memoria ${address}...`]);
  await run("emulator", "vice-memory", args);
}

// ── Project Manager ──
export async function runProjectLoad(projectPath: string): Promise<void> {
  const { setActiveProject } = useIDEStore.getState();
  log([`[PROJECT] Caricamento ${projectPath}...`]);
  const result = await run("project-manager", "load", [projectPath]);
  if (result.success) {
    setActiveProject(projectPath);
    log([`[OK] Progetto caricato`]);
  }
}

export async function runProjectBuild(projectPath: string): Promise<void> {
  const { setCompiling } = useIDEStore.getState();
  setCompiling(true);
  log([`[PROJECT] Build ${projectPath}...`]);
  await run("project-manager", "build", [projectPath]);
  setCompiling(false);
}

// ── AI Agent ──
export async function runAIAgentGenerate(
  prompt: string, options?: { mode?: string; output?: string }
): Promise<void> {
  const args = [prompt];
  if (options?.mode) args.push("--mode", options.mode);
  if (options?.output) args.push("-o", options.output);
  log([`[AI] Generazione da prompt...`]);
  await run("ai-agent", "generate", args);
}

export async function runAIAgentExplain(inputPath: string): Promise<void> {
  log([`[AI] Spiegazione ${inputPath}...`]);
  await run("ai-agent", "explain", [inputPath]);
}

export async function runAIAgentDebug(inputPath: string, crashPath?: string): Promise<void> {
  const args = [inputPath];
  if (crashPath) args.push("--crash", crashPath);
  log([`[AI] Debug ${inputPath}...`]);
  await run("ai-agent", "debug", args);
}

export async function runAIAgentSearch(query: string): Promise<void> {
  log([`[AI] Ricerca: ${query}`]);
  await run("ai-agent", "search", [query]);
}

// ── Debugger ──
export async function runDebuggerRun(prgPath: string): Promise<void> {
  log([`[DEBUG] Avvio ${prgPath}...`]);
  await run("debugger", "run", [prgPath]);
}

export async function runDebuggerStep(): Promise<void> {
  log([`[DEBUG] Step...`]);
  await run("debugger", "step", []);
}

export async function runDebuggerRegisters(): Promise<void> {
  log([`[DEBUG] Registri...`]);
  await run("debugger", "registers", []);
}

export async function runDebuggerMemory(address: string, size?: number): Promise<void> {
  const args = [address];
  if (size) args.push("--size", String(size));
  log([`[DEBUG] Memoria ${address}...`]);
  await run("debugger", "memory", args);
}

export async function runDebuggerBreakpoint(address: string, remove?: boolean): Promise<void> {
  const args = [address];
  if (remove) args.push("--remove");
  log([`[DEBUG] Breakpoint ${address}...`]);
  await run("debugger", "breakpoint", args);
}

export async function runDebuggerCrashAnalyze(dumpPath: string): Promise<void> {
  log([`[DEBUG] Crash dump ${dumpPath}...`]);
  await run("debugger", "crash-analyze", [dumpPath]);
}

export async function runDebuggerReset(): Promise<void> {
  log([`[DEBUG] Reset...`]);
  await run("debugger", "reset", []);
}

// ── Knowledge ──
export async function runKnowledgeSearch(query: string): Promise<void> {
  log([`[KB] Ricerca: ${query}`]);
  await run("knowledge", "search", [query]);
}

export async function runKnowledgeDocs(topic: string): Promise<void> {
  log([`[KB] Docs: ${topic}`]);
  await run("knowledge", "docs", [topic]);
}

// ── Tutorial ──
export async function runTutorialList(part?: number): Promise<void> {
  const args: string[] = [];
  if (part) args.push("--part", String(part));
  log([`[TUTORIAL] Elenco${part ? ` parte ${part}` : ""}...`]);
  await run("tutorial", "list", args);
}

export async function runTutorialShow(chapter: string, lang?: string): Promise<void> {
  const args = [chapter];
  if (lang) args.push("--lang", lang);
  log([`[TUTORIAL] Capitolo ${chapter}...`]);
  await run("tutorial", "show", args);
}

// ── GeckOS ──
export async function runGeckosBuild(clean?: boolean): Promise<void> {
  const args: string[] = [];
  if (clean) args.push("--clean");
  log([`[GECKOS] Build${clean ? " (clean)" : ""}...`]);
  await run("geckos", "build", args);
}

export async function runGeckosDeploy(outputPath: string): Promise<void> {
  log([`[GECKOS] Deploy ${outputPath}...`]);
  await run("geckos", "deploy", [outputPath]);
}
