export class LSPClient {
  private socket: WebSocket | null = null;
  private editor: any;
  private uri: string;
  private onDiagnosticsCallback?: (diagnostics: any[]) => void;

  constructor(editor: any, uri: string, onDiagnostics?: (diagnostics: any[]) => void) {
    this.editor = editor;
    this.uri = uri;
    this.onDiagnosticsCallback = onDiagnostics;
    this.connect();
  }

  private connect() {
    try {
      this.socket = new WebSocket("ws://localhost:8000/ws/lsp");

      this.socket.onopen = () => {
        console.log("Connessione LSP WebSocket stabilita.");
      };

      this.socket.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);
          if (msg.method === "textDocument/publishDiagnostics") {
            const diagnostics = msg.params?.diagnostics || [];
            this.applyDiagnostics(diagnostics);
            if (this.onDiagnosticsCallback) {
              this.onDiagnosticsCallback(diagnostics);
            }
          }
        } catch (e) {
          console.error("Errore durante il parsing del messaggio LSP:", e);
        }
      };

      this.socket.onclose = () => {
        console.warn("LSP WebSocket chiuso. Tentativo di riconnessione tra 5 secondi...");
        setTimeout(() => this.connect(), 5000);
      };

      this.socket.onerror = (err) => {
        console.error("Errore LSP WebSocket:", err);
      };
    } catch (err) {
      console.error("Errore di connessione LSP WebSocket:", err);
    }
  }

  public notifyChange(content: string) {
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      const payload = {
        jsonrpc: "2.0",
        method: "textDocument/didChange",
        params: {
          textDocument: { uri: this.uri, version: 1 },
          contentChanges: [{ text: content }]
        }
      };
      this.socket.send(JSON.stringify(payload));
    }
  }

  private applyDiagnostics(diagnostics: any[]) {
    const win = window as any;
    if (!win.monaco || !this.editor) return;

    const model = this.editor.getModel();
    if (!model) return;

    const markers = diagnostics.map((d: any) => ({
      startLineNumber: (d.range?.start?.line ?? 0) + 1,
      startColumn: (d.range?.start?.character ?? 0) + 1,
      endLineNumber: (d.range?.end?.line ?? d.range?.start?.line ?? 0) + 1,
      endColumn: (d.range?.end?.character ?? d.range?.start?.character ?? 0) + 1,
      message: d.message || "Errore sconosciuto",
      severity: win.monaco.MarkerSeverity.Error
    }));

    win.monaco.editor.setModelMarkers(model, "lsp-owner", markers);
  }

  public disconnect() {
    if (this.socket) {
      this.socket.onclose = null; // Prevent reconnect on explicit disconnect
      this.socket.close();
    }
  }
}
