# Design — Modifiche cliente (2026-05-15)

## Scope

Quattro modifiche richieste dal committente dopo la prima demo:

1. Rinominare "risorsa" → "costo" in tutto il codebase
2. Header voce: mostrare tutti i valori economici anche con la voce chiusa
3. Descrizione voce: cella più larga
4. PriMus colonna J: trattare come prezzo finito (con ricarica), non costo netto

Nessuna retrocompatibilità richiesta — i file JSON salvati nella cartella `data/` vengono eliminati.

---

## 1. Risorsa → Costo

### Modello Python (`models.py`)

- `RigaRisorsa` → `RigaCosto` (classe)
- `Voce.risorse: list[RigaRisorsa]` → `Voce.costi: list[RigaCosto]`
- Nessun alias di compatibilità

### Calcoli (`calcoli.py`)

Tutti i riferimenti a `voce.risorse` → `voce.costi`. Nessun cambio di logica.

### Route (`api/routes.py`)

I parametri e i body JSON cambiano il campo da `risorse` a `costi` in automatico grazie a Pydantic.

### Frontend (`frontend/index.html`)

Label visibili:
- "Risorse (analisi costi)" → "Costi"
- Intestazioni colonna tabella: invariate (Descrizione, UM, Q.tà, Costo unit., Totale)

Nomi CSS interni (`.ris-*`) e variabili JS rimangono invariati — sono dettagli implementativi non esposti all'utente.

---

## 2. Header voce: valori economici

### Layout header (voce chiusa e aperta)

```
[nr]  [Cod — Descrizione ...]  [UM]  [Costo/UM]  [Tot. costi]  [Ric.%]  [Prezzo/UM]  [Tot. ricaricato]
```

Tutti i valori sono sempre visibili nell'header, indipendentemente dallo stato aperto/chiuso della voce. Il pannello espandibile mostra misurazioni e costi analitici.

### Valori e formattazione

| Colonna | Valore | Formato |
|---|---|---|
| Costo/UM | `costo_per_um(voce)` | `€ 0.00` |
| Tot. costi | `costo_per_um × quantità` | `€ 0.00` |
| Ric.% | `ricarica_effettiva × 100` | `0%` |
| Prezzo/UM | `prezzo_per_um(voce)` | `€ 0.00` |
| Tot. ricaricato | `prezzo_per_um × quantità` | `€ 0.00` |

Quando `prezzo_override` è impostato e non ci sono costi analitici, Costo/UM e Prezzo/UM mostrano lo stesso valore. Il badge "importato" appare su Prezzo/UM.

### CSS

La colonna descrizione riceve più spazio flex (`flex: 3` o simile invece dell'attuale più stretto). Su viewport < 640px le colonne numeriche vanno a capo su una seconda riga.

---

## 3. Descrizione voce più larga

Modifica CSS/layout nell'header della voce:

- La colonna che contiene codice + descrizione passa da una larghezza fissa o `flex: 1` a `flex: 3` (o `min-width: 280px`)
- Il testo viene troncato con `text-overflow: ellipsis` per non rompere il layout su descrizioni molto lunghe, con il testo completo visibile via `title` attribute o espandendo la voce

---

## 4. PriMus colonna J = prezzo finito

### Modello (`models.py`)

- `costo_override` rimosso (era usato solo dall'import PriMus, che ora usa `prezzo_override`)
- Aggiunto: `prezzo_override: float | None = None`

### Logica di calcolo (`calcoli.py`)

Funzione `prezzo_per_um(voce, ricarica_default)`:

```
se ha costi analitici (voce.costi non vuoto):
    → costo_per_um(voce) × (1 + ricarica_effettiva)
altrimenti se prezzo_override è impostato:
    → prezzo_override          # usato direttamente, nessuna ricarica applicata
altrimenti:
    → 0.0
```

Funzione `costo_per_um(voce)`:

```
se ha costi analitici:
    → totale_costi / quantità
altrimenti se prezzo_override è impostato:
    → prezzo_override    # nessun costo separato disponibile, costo = prezzo
altrimenti:
    → 0.0
```

**Comportamento chiave**: aggiungere costi analitici alla voce fa sì che `prezzo_override` venga ignorato e il prezzo venga ricalcolato da zero con la ricarica configurata.

### Import PriMus (`primus/parser.py`)

La riga SOMMANO: il valore in colonna J viene salvato come `prezzo_override` (non `costo_override`).

```python
# prima:
voce_corrente["costo_override"] = costo
# dopo:
voce_corrente["prezzo_override"] = costo
```

### Export PriMus (`primus/export.py`)

La colonna J della riga SOMMANO riceve `prezzo_per_um(voce)` (prezzo finito con ricarica).

```python
# prima:
_cella(foglio, riga_sommano, COL_J).value = costo_unitario
# dopo:
_cella(foglio, riga_sommano, COL_J).value = prezzo_unitario
```

Il commento nel file va aggiornato: `J: Prezzo unitario (prezzo finito con ricarica)`.

### Frontend

Il badge "importato" si sposta dalla label "Costo/UM" alla label "Prezzo/UM".
Condizione: `voce.prezzo_override !== null && voce.costi.length === 0`.

---

## File coinvolti

| File | Tipo di modifica |
|---|---|
| `src/cbd_preventivi/models.py` | Rename `RigaRisorsa`→`RigaCosto`, `risorse`→`costi`; rimuove `costo_override`; aggiunge `prezzo_override` |
| `src/cbd_preventivi/calcoli.py` | Aggiorna riferimenti `costi`; nuova logica priorità `prezzo_override` |
| `src/cbd_preventivi/primus/parser.py` | J → `prezzo_override` |
| `src/cbd_preventivi/primus/export.py` | J ← `prezzo_per_um`; aggiorna commento |
| `src/cbd_preventivi/api/routes.py` | Nessuna modifica (Pydantic gestisce il rename) |
| `frontend/index.html` | Header voce, label "Costi", badge "importato", CSS descrizione |
| `tests/test_export_primus.py` | Aggiorna riferimenti `risorse`→`costi` e `RigaRisorsa`→`RigaCosto` |
