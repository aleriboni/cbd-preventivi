"""
Entry point dell'applicazione FastAPI.

Avvio in sviluppo:
    uv run cbd-preventivi          (con reload automatico)
    uv run uvicorn cbd_preventivi.api.app:app --reload

Avvio dall'eseguibile compilato:
    cbd-preventivi.exe             (apre il browser automaticamente)

Gestione dei path:
    - In sviluppo __file__ punta a src/cbd_preventivi/api/app.py;
      il frontend è in <project_root>/frontend/
    - Nell'exe PyInstaller sys._MEIPASS contiene tutti i file bundlati
      (compresi i file del frontend copiati da --add-data)
"""

import socket
import sys
import threading
import time
import webbrowser
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from cbd_preventivi.api.routes import router


# ---------------------------------------------------------------------------
# Risoluzione path compatibile con PyInstaller
# ---------------------------------------------------------------------------

def _is_frozen() -> bool:
    """True se l'applicazione è in esecuzione come eseguibile PyInstaller."""
    return getattr(sys, "frozen", False)


def _redirect_output_to_file() -> None:
    """Reindirizza stdout/stderr su file quando l'exe gira senza console.

    Con --noconsole su Windows, sys.stdout e sys.stderr sono None.
    uvicorn.logging.DefaultFormatter chiama sys.stdout.isatty() al momento
    della configurazione e crasha con AttributeError. Aprire un file reale
    risolve il crash e produce un log utile per il debug.
    """
    log_path = Path(sys.executable).parent / "cbd-preventivi.log"
    log_file = open(log_path, "w", encoding="utf-8", buffering=1)
    sys.stdout = log_file
    sys.stderr = log_file


def _frontend_dir() -> Path:
    """Percorso della directory frontend, corretto sia in sviluppo che da exe."""
    if _is_frozen():
        # PyInstaller estrae i file bundlati in sys._MEIPASS
        return Path(sys._MEIPASS) / "frontend"
    # Sviluppo: src/cbd_preventivi/api/app.py → 3 livelli su → project root
    return Path(__file__).parents[3] / "frontend"


# ---------------------------------------------------------------------------
# Applicazione FastAPI
# ---------------------------------------------------------------------------

app = FastAPI(
    title="CBD Preventivi",
    description="Tool per la creazione e gestione di computi metrici edilizi",
    version="0.1.0",
)

app.include_router(router)

frontend = _frontend_dir()
if frontend.exists():
    app.mount("/", StaticFiles(directory=frontend, html=True), name="static")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

HOST = "127.0.0.1"
PORT = 8000


def _porta_in_uso(host: str, porta: int) -> bool:
    """True se qualcosa è già in ascolto su host:porta."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex((host, porta)) == 0


def _apri_browser(url: str, ritardo: float = 1.5) -> None:
    """Apre il browser dopo un breve ritardo (lascia il tempo al server di avviarsi)."""
    time.sleep(ritardo)
    webbrowser.open(url)


def serve(dev: bool = False) -> None:
    """Avvia il server HTTP.

    Args:
        dev: se True abilita il reload automatico (solo per sviluppo,
             incompatibile con PyInstaller).
    """
    if dev:
        # Modalità sviluppo: stringa di import + reload
        uvicorn.run(
            "cbd_preventivi.api.app:app",
            host=HOST,
            port=PORT,
            reload=True,
        )
    else:
        # Modalità produzione / exe: oggetto app diretto, nessun reload.
        url = f"http://{HOST}:{PORT}"

        # Se il server è già in ascolto (istanza precedente ancora attiva),
        # apre solo il browser senza tentare di rifare il bind sulla porta.
        if _porta_in_uso(HOST, PORT):
            webbrowser.open(url)
            return

        # Quando --noconsole è attivo stdout/stderr sono None: li redirigiamo
        # su file prima che uvicorn configuri il logging.
        if _is_frozen() and sys.stdout is None:
            _redirect_output_to_file()

        # Apre il browser in un thread separato così il server parte prima.
        threading.Thread(target=_apri_browser, args=(url,), daemon=True).start()

        config = uvicorn.Config(
            app,
            host=HOST,
            port=PORT,
            reload=False,
            log_level="warning",
        )
        uvicorn.Server(config).run()


def serve_dev() -> None:
    """Entry point per ``uv run cbd-preventivi`` in sviluppo (con reload)."""
    serve(dev=True)


if __name__ == "__main__":
    serve()
