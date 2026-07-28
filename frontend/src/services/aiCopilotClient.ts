export class AICopilotClient {
  private socket: WebSocket | null = null;
  private onToken?: (token: string) => void;
  private onDone?: () => void;
  private onError?: (error: string) => void;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;

  constructor(callbacks: {
    onToken: (token: string) => void;
    onDone: () => void;
    onError: (error: string) => void;
  }) {
    this.onToken = callbacks.onToken;
    this.onDone = callbacks.onDone;
    this.onError = callbacks.onError;
  }

  private connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      if (this.socket && this.socket.readyState === WebSocket.OPEN) {
        resolve();
        return;
      }

      try {
        this.socket = new WebSocket("ws://localhost:8000/ws/ai-copilot");

        this.socket.onopen = () => resolve();

        this.socket.onmessage = (event) => {
          try {
            const msg = JSON.parse(event.data);
            if (msg.done) {
              this.onDone?.();
            } else if (msg.error) {
              this.onError?.(msg.error);
            } else if (msg.token !== undefined) {
              this.onToken?.(msg.token);
            }
          } catch (e) {
            console.error("AI Copilot parse error:", e);
          }
        };

        this.socket.onclose = () => {
          this.scheduleReconnect();
        };

        this.socket.onerror = () => {
          reject(new Error("WebSocket connection failed"));
        };
      } catch (err) {
        reject(err);
      }
    });
  }

  private scheduleReconnect() {
    if (this.reconnectTimer) return;
    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null;
      this.connect().catch(() => {});
    }, 5000);
  }

  async complete(prompt: string, context?: string): Promise<void> {
    try {
      await this.connect();
    } catch {
      this.onError?.("Impossibile connettersi al server AI Copilot");
      return;
    }

    if (!this.socket || this.socket.readyState !== WebSocket.OPEN) {
      this.onError?.("WebSocket non connesso");
      return;
    }

    const payload = {
      action: "complete",
      prompt,
      context: context || "",
    };

    this.socket.send(JSON.stringify(payload));
  }

  disconnect() {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    if (this.socket) {
      this.socket.onclose = null;
      this.socket.close();
      this.socket = null;
    }
  }
}
