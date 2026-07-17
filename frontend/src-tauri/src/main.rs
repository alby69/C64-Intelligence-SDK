#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use tauri::api::process::{Command, CommandEvent};

#[tauri::command]
fn start_backend_services(app_handle: tauri::AppHandle) {
    println!("Inizializzazione dei servizi di backend C64...");
    // Avvia il core-service come sidecar di Tauri (se disponibile)
    match Command::new_sidecar("c64-core-service") {
        Ok(cmd) => {
            match cmd.spawn() {
                Ok((mut rx, _child)) => {
                    tauri::async_runtime::spawn(async move {
                        while let Some(event) = rx.recv().await {
                            if let CommandEvent::Stdout(line) = event {
                                println!("Backend Sidecar: {}", line);
                            }
                        }
                    });
                }
                Err(e) => {
                    eprintln!("Impossibile avviare il sidecar core-service: {}", e);
                }
            }
        }
        Err(e) => {
            eprintln!("Configurazione sidecar non trovata: {}", e);
        }
    }
}

fn main() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![start_backend_services])
        .run(tauri::generate_context!())
        .expect("errore durante l'esecuzione dell'applicazione tauri");
}
