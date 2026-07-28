import { create } from 'zustand';

interface IDEState {
  activeProject: string | null;
  openFiles: string[];
  activeFile: string | null;
  fileContents: Record<string, string>;
  savedContents: Record<string, string>;
  isCompiling: boolean;
  terminalLogs: string[];
  commandHistory: string[];
  historyIndex: number;

  setActiveProject: (path: string | null) => void;
  openFile: (path: string, initialContent?: string) => void;
  closeFile: (path: string) => void;
  setActiveFile: (path: string | null) => void;
  updateFileContent: (path: string, content: string) => void;
  saveActiveFile: (saveFn: (path: string, content: string) => Promise<void>) => Promise<void>;
  setCompiling: (status: boolean) => void;
  addLog: (log: string) => void;
  clearLogs: () => void;
  addCommandHistory: (cmd: string) => void;
  isFileDirty: (path: string) => boolean;
}

export const useIDEStore = create<IDEState>((set, get) => ({
  activeProject: null,
  openFiles: [],
  activeFile: null,
  fileContents: {},
  savedContents: {},
  isCompiling: false,
  terminalLogs: [],
  commandHistory: [],
  historyIndex: -1,

  setActiveProject: (path) => set({ activeProject: path }),

  openFile: (path, initialContent = "") => set((state) => {
    const nextFiles = state.openFiles.includes(path) ? state.openFiles : [...state.openFiles, path];
    const newContents = { ...state.fileContents };
    const newSaved = { ...state.savedContents };

    if (newContents[path] === undefined) {
      newContents[path] = initialContent;
      newSaved[path] = initialContent;
    }

    return {
      openFiles: nextFiles,
      activeFile: path,
      fileContents: newContents,
      savedContents: newSaved
    };
  }),

  closeFile: (path) => set((state) => {
    const nextFiles = state.openFiles.filter(f => f !== path);
    const newContents = { ...state.fileContents };
    const newSaved = { ...state.savedContents };
    delete newContents[path];
    delete newSaved[path];

    return {
      openFiles: nextFiles,
      activeFile: state.activeFile === path ? (nextFiles[0] || null) : state.activeFile,
      fileContents: newContents,
      savedContents: newSaved
    };
  }),

  setActiveFile: (path) => set({ activeFile: path }),

  updateFileContent: (path, content) => set((state) => ({
    fileContents: {
      ...state.fileContents,
      [path]: content
    }
  })),

  saveActiveFile: async (saveFn) => {
    const { activeFile, fileContents } = get();
    if (!activeFile) return;
    const content = fileContents[activeFile] || "";
    try {
      await saveFn(activeFile, content);
      set((state) => ({
        savedContents: {
          ...state.savedContents,
          [activeFile]: content
        }
      }));
    } catch (e) {
      console.error("Failed to save file:", e);
    }
  },

  setCompiling: (status) => set({ isCompiling: status }),

  addLog: (log) => set((state) => ({ terminalLogs: [...state.terminalLogs, log] })),

  clearLogs: () => set({ terminalLogs: [] }),

  addCommandHistory: (cmd) => set((state) => ({
    commandHistory: [...state.commandHistory, cmd].slice(-50),
    historyIndex: -1,
  })),

  isFileDirty: (path) => {
    const { fileContents, savedContents } = get();
    const current = fileContents[path];
    const saved = savedContents[path];
    if (current === undefined || saved === undefined) return false;
    return current !== saved;
  }
}));
