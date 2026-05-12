"""
Modelli di dominio per il computo metrico edilizio.

Ogni classe rappresenta un concetto del dominio:
  - RigaMisurazione: una riga della lista misurazioni di una voce
  - RigaRisorsa: una risorsa (manodopera, materiale, nolo) nell'analisi costi
  - Voce: una singola lavorazione del computo
  - Preventivo: il documento completo con intestazione e lista voci
"""

from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field


class RigaMisurazione(BaseModel):
    """Una riga nella lista misurazioni di una voce.

    La quantità può essere calcolata moltiplicando i fattori (par_ug × lung × larg
    × h_peso), oppure impostata direttamente tramite ``quantita_diretta``.
    Quest'ultima modalità si usa per righe del tipo «Vedi voce n° X» importate
    da PriMus, dove la quantità è già nota e non deriva da misure.
    """

    descrizione: str = ""
    par_ug: Optional[float] = None
    lung: Optional[float] = None
    larg: Optional[float] = None
    h_peso: Optional[float] = None
    quantita_diretta: Optional[float] = None

    @property
    def quantita(self) -> float:
        """Restituisce la quantità della riga.

        Se ``quantita_diretta`` è impostata ha la precedenza; altrimenti calcola
        il prodotto dei fattori non nulli (par_ug, lung, larg, h_peso).
        Restituisce 0 se nessun fattore è valorizzato.
        """
        if self.quantita_diretta is not None:
            return round(self.quantita_diretta, 2)
        fattori = [v for v in (self.par_ug, self.lung, self.larg, self.h_peso) if v is not None]
        if not fattori:
            return 0.0
        prodotto = 1.0
        for fattore in fattori:
            prodotto *= fattore
        return round(prodotto, 2)

    @property
    def is_empty(self) -> bool:
        """True se la riga non ha né quantità né descrizione (artefatto UI)."""
        return self.quantita == 0.0 and not self.descrizione.strip()


class RigaRisorsa(BaseModel):
    """Una risorsa nell'analisi costi di una voce (operaio, materiale, nolo, ecc.)."""

    descrizione: str
    um: str = ""
    quantita: float = 0.0
    costo_unitario: float = 0.0

    @property
    def totale(self) -> float:
        """Costo totale della risorsa: quantità × costo unitario."""
        return round(self.quantita * self.costo_unitario, 2)


class Voce(BaseModel):
    """Una lavorazione del computo metrico.

    Può avere misurazioni esplicite oppure una quantità manuale.
    Il costo unitario può provenire dall'analisi risorse oppure essere
    importato direttamente da PriMus (``costo_override``).
    """

    codice: str
    descrizione: str
    um: str
    ricarica: Optional[float] = None
    quantita_manuale: Optional[float] = None
    costo_override: Optional[float] = None
    misurazioni: list[RigaMisurazione] = Field(default_factory=list)
    risorse: list[RigaRisorsa] = Field(default_factory=list)


class Preventivo(BaseModel):
    """Il documento di computo metrico completo."""

    id: Optional[str] = None
    nome: str = ""
    cliente: str = ""
    data: str = ""
    numero: str = ""
    ricarica_default: float = 0.20
    voci: list[Voce] = Field(default_factory=list)
