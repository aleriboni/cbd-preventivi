"""
Endpoint REST per la gestione dei preventivi.

Percorsi disponibili:
  POST   /api/preventivo                       → crea un nuovo preventivo
  GET    /api/preventivo/{id}                  → carica un preventivo esistente
  PUT    /api/preventivo/{id}                  → aggiorna un preventivo esistente
  POST   /api/preventivo/import/primus         → importa un preventivo da xlsx PriMus
  GET    /api/preventivo/{id}/export/primus    → esporta il preventivo in xlsx PriMus

I preventivi sono salvati come file JSON nella directory ``DATA_DIR``.
"""

import os
import sys
import uuid
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import Response

from cbd_preventivi.models import Preventivo
from cbd_preventivi.primus.export import genera_xlsx
from cbd_preventivi.primus.parser import parse_primus_xlsx


def _default_data_dir() -> str:
    """Percorso default per i dati.

    Nell'exe PyInstaller usa la directory dell'eseguibile (persiste tra
    gli aggiornamenti); in sviluppo usa ``data/`` relativa alla CWD.
    """
    if getattr(sys, "frozen", False):
        return str(Path(sys.executable).parent / "data")
    return "data"


# Directory di persistenza: configurabile via variabile d'ambiente CBD_DATA_DIR
DATA_DIR = Path(os.environ.get("CBD_DATA_DIR", _default_data_dir()))
DATA_DIR.mkdir(exist_ok=True)

router = APIRouter(prefix="/api")


def _percorso_preventivo(id_preventivo: str) -> Path:
    """Restituisce il path del file JSON per un dato ID."""
    return DATA_DIR / f"{id_preventivo}.json"


def _carica_o_404(id_preventivo: str) -> Preventivo:
    """Carica un preventivo dal disco o solleva 404 se non esiste."""
    percorso = _percorso_preventivo(id_preventivo)
    if not percorso.exists():
        raise HTTPException(status_code=404, detail="Preventivo non trovato")
    return Preventivo.model_validate_json(percorso.read_text())


def _salva(preventivo: Preventivo) -> None:
    """Salva un preventivo su disco come file JSON."""
    _percorso_preventivo(preventivo.id).write_text(
        preventivo.model_dump_json(indent=2)
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/preventivo", response_model=Preventivo, status_code=201)
def crea_preventivo(preventivo: Preventivo):
    """Crea un nuovo preventivo e lo salva su disco."""
    preventivo.id = str(uuid.uuid4())[:8]
    _salva(preventivo)
    return preventivo


@router.get("/preventivo/{id_preventivo}", response_model=Preventivo)
def carica_preventivo(id_preventivo: str):
    """Restituisce un preventivo esistente per ID."""
    return _carica_o_404(id_preventivo)


@router.put("/preventivo/{id_preventivo}", response_model=Preventivo)
def aggiorna_preventivo(id_preventivo: str, preventivo: Preventivo):
    """Aggiorna un preventivo esistente (deve già esistere)."""
    _carica_o_404(id_preventivo)  # verifica esistenza
    preventivo.id = id_preventivo
    _salva(preventivo)
    return preventivo


@router.post("/preventivo/import/primus", status_code=201)
async def importa_da_primus(file: UploadFile = File(...)):
    """Importa un preventivo da un file xlsx esportato da PriMus."""
    contenuto = await file.read()
    try:
        preventivo = parse_primus_xlsx(contenuto)
    except Exception as errore:
        raise HTTPException(status_code=422, detail=f"Errore nel parsing del file: {errore}")
    preventivo.id = str(uuid.uuid4())[:8]
    _salva(preventivo)
    return {"id": preventivo.id}


@router.get("/preventivo/{id_preventivo}/export/primus")
def esporta_in_primus(id_preventivo: str):
    """Esporta un preventivo nel formato xlsx PriMus."""
    preventivo = _carica_o_404(id_preventivo)
    xlsx_bytes = genera_xlsx(preventivo)
    nome_file = f"computo_{id_preventivo}.xlsx"
    return Response(
        content=xlsx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{nome_file}"'},
    )
