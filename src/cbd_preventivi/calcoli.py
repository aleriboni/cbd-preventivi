"""
Logica di calcolo per voci e preventivo.

Tutte le funzioni sono pure (nessun effetto collaterale) e operano
sui modelli di dominio definiti in ``models``.

Gerarchia dei calcoli:
  quantita_x      → somma delle quantità delle misurazioni (o quantita_manuale)
  totale_costi    → somma dei costi di tutte le voci di costo
  costo_per_um    → totale_costi / quantita_x, oppure prezzo_override se nessun costo
  prezzo_per_um   → costo_per_um × (1 + ricarica), oppure prezzo_override diretto
  importo_voce    → prezzo_per_um × quantita_x
  totale_preventivo → somma degli importi di tutte le voci
"""

from cbd_preventivi.models import Preventivo, Voce


def ricarica_effettiva(voce: Voce, preventivo: Preventivo) -> float:
    """Ricarica da applicare alla voce: quella specifica se definita, altrimenti quella di default."""
    return voce.ricarica if voce.ricarica is not None else preventivo.ricarica_default


def quantita_x(voce: Voce) -> float:
    """Quantità totale della voce.

    Somma le quantità delle misurazioni valide; se non ce ne sono usa
    ``quantita_manuale``.
    """
    misurazioni_valide = [m for m in voce.misurazioni if not m.is_empty]
    if misurazioni_valide:
        return round(sum(m.quantita for m in misurazioni_valide), 2)
    return voce.quantita_manuale or 0.0


def totale_costi(voce: Voce) -> float:
    """Somma dei costi di tutte le voci di costo della lavorazione."""
    return round(sum(costo.totale for costo in voce.costi), 2)


def costo_per_um(voce: Voce) -> float:
    """Costo netto per unità di misura.

    Se ci sono voci di costo analitiche, divide il totale costi per la quantità.
    Se invece è impostato ``prezzo_override`` (importato da PriMus) e non ci sono
    costi analitici, lo usa come riferimento di costo (costo = prezzo importato).
    """
    if voce.costi:
        quantita = quantita_x(voce)
        if quantita == 0:
            return 0.0
        return round(totale_costi(voce) / quantita, 6)
    if voce.prezzo_override is not None:
        return voce.prezzo_override
    return 0.0


def prezzo_per_um(voce: Voce, preventivo: Preventivo) -> float:
    """Prezzo di vendita per unità di misura.

    Se ci sono voci di costo, applica la ricarica al costo calcolato.
    Se è impostato solo ``prezzo_override``, lo usa direttamente senza
    applicare la ricarica (il prezzo è già quello finale importato da PriMus).
    """
    if voce.costi:
        costo = costo_per_um(voce)
        ricarica = ricarica_effettiva(voce, preventivo)
        return round(costo * (1 + ricarica), 2)
    if voce.prezzo_override is not None:
        return voce.prezzo_override
    return 0.0


def importo_voce(voce: Voce, preventivo: Preventivo) -> float:
    """Importo totale della voce: prezzo/UM × quantità."""
    return round(prezzo_per_um(voce, preventivo) * quantita_x(voce), 2)


def totale_preventivo(preventivo: Preventivo) -> float:
    """Importo complessivo del preventivo (somma degli importi di tutte le voci)."""
    return round(sum(importo_voce(voce, preventivo) for voce in preventivo.voci), 2)
