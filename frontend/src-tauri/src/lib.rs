use std::sync::{Arc, Mutex};
use tauri::Manager;
use tauri_plugin_shell::ShellExt;
use tauri_plugin_shell::process::{CommandChild, CommandEvent};

struct SidecarState(Arc<Mutex<Option<CommandChild>>>);

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
  let child_holder = Arc::new(Mutex::new(None));
  let child_holder_setup = child_holder.clone();

  tauri::Builder::default()
    .plugin(tauri_plugin_shell::init())
    .plugin(
      tauri_plugin_log::Builder::default()
        .level(log::LevelFilter::Info)
        .build(),
    )
    .setup(move |app| {
      log::info!("VisionArchive Desktop initializing...");
      app.manage(SidecarState(child_holder_setup.clone()));
      
      let home = std::env::var("HOME").unwrap_or_else(|_| "/tmp".to_string());
      let tmp_dir = std::path::PathBuf::from(home)
          .join(".config")
          .join("VisionArchive")
          .join("tmp");
      let _ = std::fs::create_dir_all(&tmp_dir);

      // Clean up any stale PyInstaller _MEI directories
      if let Ok(entries) = std::fs::read_dir(&tmp_dir) {
          for entry in entries.flatten() {
              if let Ok(file_type) = entry.file_type() {
                  if file_type.is_dir() && entry.file_name().to_string_lossy().starts_with("_MEI") {
                      let _ = std::fs::remove_dir_all(entry.path());
                  }
              }
          }
      }
      if let Ok(entries) = std::fs::read_dir("/tmp") {
          for entry in entries.flatten() {
              if let Ok(file_type) = entry.file_type() {
                  if file_type.is_dir() && entry.file_name().to_string_lossy().starts_with("_MEI") {
                      let _ = std::fs::remove_dir_all(entry.path());
                  }
              }
          }
      }

      // Terminate any previous orphan cove-backend sidecar or process occupying port 8005
      #[cfg(unix)]
      {
          let _ = std::process::Command::new("fuser")
              .args(["-k", "-9", "8005/tcp"])
              .output();
          let _ = std::process::Command::new("pkill")
              .args(["-9", "-f", "cove-backend"])
              .output();
          std::thread::sleep(std::time::Duration::from_millis(150));
      }

      // Spawn the Python backend sidecar
      match app.shell().sidecar("cove-backend") {
          Ok(sidecar_command) => {
              log::info!("Spawning cove-backend sidecar on port 8005...");
              let (mut receiver, child) = sidecar_command
                  .env("VISION_PORT", "8005")
                  .env("TMPDIR", &tmp_dir)
                  .spawn()
                  .expect("Failed to spawn sidecar");

              if let Ok(mut guard) = child_holder_setup.lock() {
                  *guard = Some(child);
              }

              tauri::async_runtime::spawn(async move {
                  while let Some(event) = receiver.recv().await {
                      match event {
                          CommandEvent::Stdout(line) => {
                              let msg = String::from_utf8_lossy(&line);
                              println!("[Sidecar STDOUT] {}", msg.trim_end());
                              log::info!("[Sidecar STDOUT] {}", msg.trim_end());
                          }
                          CommandEvent::Stderr(line) => {
                              let msg = String::from_utf8_lossy(&line);
                              eprintln!("[Sidecar STDERR] {}", msg.trim_end());
                              log::error!("[Sidecar STDERR] {}", msg.trim_end());
                          }
                          CommandEvent::Error(err) => {
                              log::error!("[Sidecar ERROR] {}", err);
                          }
                          CommandEvent::Terminated(status) => {
                              log::warn!("[Sidecar Terminated] status: {:?}", status.code);
                          }
                          _ => {}
                      }
                  }
              });
          },
          Err(e) => {
              log::error!("Failed to create sidecar command: {}", e);
              eprintln!("Failed to create sidecar command: {}", e);
          }
      }

      Ok(())
    })
    .build(tauri::generate_context!())
    .expect("error while building tauri application")
    .run(move |app_handle, event| {
        if let tauri::RunEvent::Exit = event {
            if let Some(state) = app_handle.try_state::<SidecarState>() {
                if let Ok(mut guard) = state.0.lock() {
                    if let Some(child) = guard.take() {
                        log::info!("Terminating sidecar child process on app exit...");
                        let _ = child.kill();
                    }
                }
            }
        }
    });
}
