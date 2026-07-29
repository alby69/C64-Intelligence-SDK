import { useState, useEffect } from "react";
import type { UserPreferences } from "../services/preferencesTypes";
import {
  savePreferences,
  detectVice,
  detectPython,
} from "../services/preferencesService";

interface FirstRunWizardProps {
  onComplete: (prefs: UserPreferences) => void;
}

type Step = "welcome" | "python" | "vice" | "done";

export function FirstRunWizard({ onComplete }: FirstRunWizardProps) {
  const [step, setStep] = useState<Step>("welcome");
  const [pythonPath, setPythonPath] = useState<string | null>(null);
  const [vicePath, setVicePath] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    checkDetections();
  }, []);

  const checkDetections = async () => {
    setLoading(true);
    const [py, vice] = await Promise.all([detectPython(), detectVice()]);
    setPythonPath(py);
    setVicePath(vice);
    setLoading(false);
  };

  const handleNext = async () => {
    switch (step) {
      case "welcome":
        setStep("python");
        break;
      case "python":
        setStep("vice");
        break;
      case "vice":
        const prefs: UserPreferences = {
          last_project: null,
          last_directory: null,
          theme: "dark",
          font_size: 13,
          window_width: 1280,
          window_height: 800,
          VICE_path: vicePath,
          auto_save: true,
        };
        await savePreferences(prefs);
        setStep("done");
        setTimeout(() => onComplete(prefs), 1500);
        break;
    }
  };

  return (
    <div className="fixed inset-0 z-[100] bg-editor-bg flex items-center justify-center">
      <div className="w-[480px] bg-editor-sidebar border border-editor-border rounded-xl shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="bg-editor-accent px-6 py-4">
          <h1 className="text-white font-bold text-lg">C64 Intelligence Studio</h1>
          <p className="text-blue-100 text-xs mt-0.5">Setup iniziale</p>
        </div>

        {/* Progress */}
        <div className="flex gap-1 px-6 pt-4">
          {["welcome", "python", "vice", "done"].map((s, i) => (
            <div
              key={s}
              className={`h-1 flex-1 rounded transition-colors ${
                ["welcome", "python", "vice", "done"].indexOf(step) >= i
                  ? "bg-editor-accent"
                  : "bg-editor-border"
              }`}
            />
          ))}
        </div>

        {/* Content */}
        <div className="px-6 py-6 min-h-[240px]">
          {step === "welcome" && (
            <div className="space-y-4">
              <div className="text-center">
                <div className="text-5xl mb-3">🖥️</div>
                <h2 className="text-xl font-bold text-editor-text">
                  Benvenuto in C64 Intelligence Studio
                </h2>
                <p className="text-sm text-gray-500 mt-2">
                  IDE moderno per lo sviluppo C64PY targeting il Commodore 64.
                </p>
              </div>
              <div className="bg-editor-bg rounded-lg p-3 space-y-2 text-xs text-gray-400">
                <div className="flex items-center gap-2">
                  <span>🔨</span> <span>Compilatore C64PY integrato</span>
                </div>
                <div className="flex items-center gap-2">
                  <span>🤖</span> <span>AI Copilot per suggerimenti</span>
                </div>
                <div className="flex items-center gap-2">
                  <span>💾</span> <span>Gestione dischi D64/D81</span>
                </div>
                <div className="flex items-center gap-2">
                  <span>🎮</span> <span>Emulatore integrato</span>
                </div>
              </div>
            </div>
          )}

          {step === "python" && (
            <div className="space-y-4">
              <h2 className="text-lg font-bold text-editor-text">🐍 Python</h2>
              <p className="text-sm text-gray-500">
                Il sistema plugin richiede Python 3 per eseguire i tool CLI.
              </p>
              {loading ? (
                <div className="text-xs text-gray-500 italic">Rilevamento in corso...</div>
              ) : pythonPath ? (
                <div className="bg-green-900/30 border border-green-700/50 rounded-lg p-3">
                  <div className="flex items-center gap-2 text-green-400 text-sm">
                    <span>✅</span>
                    <span className="font-medium">Python trovato: {pythonPath}</span>
                  </div>
                </div>
              ) : (
                <div className="bg-red-900/30 border border-red-700/50 rounded-lg p-3">
                  <div className="flex items-center gap-2 text-red-400 text-sm">
                    <span>❌</span>
                    <span className="font-medium">Python non trovato</span>
                  </div>
                  <p className="text-xs text-gray-500 mt-1">
                    Installa Python 3: <code className="text-yellow-400">sudo apt install python3</code>
                  </p>
                </div>
              )}
              <p className="text-xs text-gray-600">
                Puoi configurare il percorso manualmente dopo il setup.
              </p>
            </div>
          )}

          {step === "vice" && (
            <div className="space-y-4">
              <h2 className="text-lg font-bold text-editor-text">🎮 VICE Emulator</h2>
              <p className="text-sm text-gray-500">
                VICE è opzionale. Serve per eseguire i programmi C64 direttamente.
              </p>
              {loading ? (
                <div className="text-xs text-gray-500 italic">Rilevamento in corso...</div>
              ) : vicePath ? (
                <div className="bg-green-900/30 border border-green-700/50 rounded-lg p-3">
                  <div className="flex items-center gap-2 text-green-400 text-sm">
                    <span>✅</span>
                    <span className="font-medium">VICE trovato: {vicePath}</span>
                  </div>
                </div>
              ) : (
                <div className="bg-yellow-900/30 border border-yellow-700/50 rounded-lg p-3">
                  <div className="flex items-center gap-2 text-yellow-400 text-sm">
                    <span>⚠️</span>
                    <span className="font-medium">VICE non trovato</span>
                  </div>
                  <p className="text-xs text-gray-500 mt-1">
                    Puoi installarlo con: <code className="text-yellow-400">sudo apt install vice</code>
                  </p>
                </div>
              )}
              <p className="text-xs text-gray-600">
                Puoi configurare il percorso VICE nelle preferenze dopo il setup.
              </p>
            </div>
          )}

          {step === "done" && (
            <div className="text-center space-y-4">
              <div className="text-5xl">✨</div>
              <h2 className="text-lg font-bold text-editor-text">Tutto pronto!</h2>
              <p className="text-sm text-gray-500">
                C64 Intelligence Studio è configurato. Buona programmazione!
              </p>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-editor-border flex justify-between">
          <button
            onClick={() => {
              savePreferences({
                last_project: null, last_directory: null, theme: "dark",
                font_size: 13, window_width: 1280, window_height: 800,
                VICE_path: null, auto_save: true,
              });
              onComplete({
                last_project: null, last_directory: null, theme: "dark",
                font_size: 13, window_width: 1280, window_height: 800,
                VICE_path: null, auto_save: true,
              });
            }}
            className="px-4 py-2 text-gray-500 text-sm hover:text-gray-300 transition-colors"
          >
            Salta setup →
          </button>
          <button
            onClick={handleNext}
            className="px-6 py-2 bg-editor-accent text-white text-sm font-medium rounded-lg hover:bg-editor-accent/80 transition-colors"
          >
            {step === "done" ? "Inizia" : step === "vice" ? "Fine" : "Avanti →"}
          </button>
        </div>
      </div>
    </div>
  );
}
