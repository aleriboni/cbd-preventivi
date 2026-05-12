"""
Script di build — genera l'eseguibile distribuibile.

Uso:
    uv run python build.py

Output:
    dist/cbd-preventivi/
    ├── cbd-preventivi.exe    ← avviabile con doppio click
    ├── _internal/            ← runtime Python + librerie (non toccare)
    └── (data/ creata al primo avvio dall'exe)

Per distribuire: zippare la cartella dist/cbd-preventivi/ e consegnarla.

Note tecniche:
    - --onedir invece di --onefile: avvio più rapido (nessuna estrazione al volo)
    - --noconsole: nessuna finestra terminale per l'utente finale
    - --add-data: include il frontend nella directory bundlata
    - hidden-import: uvicorn carica alcuni moduli dinamicamente; vanno dichiarati
      esplicitamente altrimenti PyInstaller li esclude
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent
ENTRY = ROOT / "scripts" / "entry.py"
FRONTEND = ROOT / "frontend"
ICON = ROOT / "scripts" / "icon.ico"  # opzionale: icona exe Windows

# Separatore path per --add-data: ';' su Windows, ':' su macOS/Linux
SEP = ";" if sys.platform == "win32" else ":"

cmd = [
    sys.executable, "-m", "PyInstaller",
    "--clean",
    "--onedir",
    "--noconsole",
    "--name", "cbd-preventivi",
    # Bundla il frontend; finisce in sys._MEIPASS/frontend nell'exe
    "--add-data", f"{FRONTEND}{SEP}frontend",
    # uvicorn usa import dinamici: vanno dichiarati esplicitamente
    "--hidden-import", "uvicorn.logging",
    "--hidden-import", "uvicorn.loops",
    "--hidden-import", "uvicorn.loops.auto",
    "--hidden-import", "uvicorn.protocols",
    "--hidden-import", "uvicorn.protocols.http",
    "--hidden-import", "uvicorn.protocols.http.auto",
    "--hidden-import", "uvicorn.protocols.websockets",
    "--hidden-import", "uvicorn.protocols.websockets.auto",
    "--hidden-import", "uvicorn.lifespan",
    "--hidden-import", "uvicorn.lifespan.on",
    str(ENTRY),
]

# Aggiunge icona se presente (solo Windows)
if ICON.exists() and sys.platform == "win32":
    cmd += ["--icon", str(ICON)]

print("Build in corso…")
result = subprocess.run(cmd)

if result.returncode == 0:
    print(f"\nBuild completata: dist/cbd-preventivi/")
    print("Per distribuire: zippare la cartella dist/cbd-preventivi/")
else:
    print("\nBuild fallita.")
    sys.exit(1)
