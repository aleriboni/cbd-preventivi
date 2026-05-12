"""
Entry point per l'eseguibile PyInstaller.

Questo file è il punto di ingresso dell'exe compilato.
Non viene usato in sviluppo (lì si usa ``uv run cbd-preventivi``).
"""

from cbd_preventivi.api.app import serve

if __name__ == "__main__":
    serve()
