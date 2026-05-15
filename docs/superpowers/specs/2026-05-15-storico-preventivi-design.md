# Design — Storico Preventivi (2026-05-15)

## Scope

Aggiunta di uno storico dei preventivi: la `screen-landing` diventa una lista
navigabile di tutti i preventivi salvati. L'utente può aprire un preventivo
esistente, eliminarlo, o crearne uno nuovo. Il backend espone due nuovi endpoint.

---

## Backend

### `GET /api/preventivi`

Legge tutti i file `*.json` in `DATA_DIR`, estrae `id`, `nome`, `data` da
ciascuno e restituisce una lista ordinata per data di modifica del file
(più recente prima).

Risposta:
```json
[
  {"id": "abc123", "nome": "Ristrutturazione Via Roma", "data": "15/05/2026"},
  {"id": "def456", "nome": "Bagno Rossi", "data": "10/05/2026"}
]
```

File con JSON non valido vengono saltati silenziosamente.

### `DELETE /api/preventivo/{id}`

Cancella il file `{id}.json` da `DATA_DIR`.

- `204 No Content` se eliminato con successo
- `404 Not Found` se il file non esiste

---

## Frontend

### `screen-landing` — Lista preventivi

**Header:**
```
I miei preventivi          [+ Nuovo]  [Importa PriMus]
```

**Tabella compatta** (colonne: Nome · Data · Azioni):

| Nome | Data | |
|---|---|---|
| Ristrutturazione Via Roma | 15/05/2026 | [Apri] [Elimina] |
| Bagno Rossi | 10/05/2026 | [Apri] [Elimina] |

**Stato vuoto** (nessun preventivo): messaggio "Nessun preventivo. Crea il primo!"
con i due pulsanti di azione.

### Flusso navigazione

| Azione | Comportamento |
|---|---|
| **Apri** | `GET /api/preventivo/{id}` → `templateVoce` per ogni voce → mostra `screen-editor` |
| **Elimina** | `confirm()` → `DELETE /api/preventivo/{id}` → ricarica lista |
| **+ Nuovo** | `resetEditor()` → mostra `screen-editor` (comportamento invariato) |
| **Importa PriMus** | upload xlsx → `POST /api/preventivo/import/primus` → apre editor (comportamento invariato) |
| **← Lista** (nell'editor) | salva automaticamente se il preventivo ha un id → nasconde `screen-editor` → `caricaLista()` → mostra `screen-landing` |

### Bottone "← Lista" nell'editor

Aggiunto nell'action bar accanto a Salva / Esporta / Riepilogo.
Al click:
1. Se `currentId` è valorizzato → chiama `salva()` silenziosamente
2. Nasconde `screen-editor`
3. Chiama `caricaLista()` per aggiornare la lista
4. Mostra `screen-landing`

### Nuove funzioni JS

| Funzione | Responsabilità |
|---|---|
| `caricaLista()` | `GET /api/preventivi` → popola `#lista-tbody` → mostra `screen-landing` |
| `apriPreventivo(id)` | `GET /api/preventivo/{id}` → carica voci nell'editor → imposta `currentId = id` → mostra `screen-editor` |
| `eliminaPreventivo(id, nome)` | `confirm()` → `DELETE` → `caricaLista()` |
| `tornaLista()` | salva se ha id → `caricaLista()` → torna a `screen-landing` |

---

## Compatibilità

I preventivi già presenti in `data/` sono compatibili senza migrazioni. Vengono
elencati automaticamente dalla nuova `GET /api/preventivi`.

---

## Testing

Nuovo file `tests/test_routes.py` con i seguenti casi:

- `GET /api/preventivi` restituisce lista con `id`, `nome`, `data` corretti
- `GET /api/preventivi` restituisce lista vuota se `DATA_DIR` è vuota
- `DELETE /api/preventivo/{id}` elimina il file e restituisce 204
- `DELETE /api/preventivo/inesistente` restituisce 404

---

## File coinvolti

| File | Modifica |
|---|---|
| `src/cbd_preventivi/api/routes.py` | Aggiunge `GET /api/preventivi` e `DELETE /api/preventivo/{id}` |
| `frontend/index.html` | Trasforma `screen-landing` in lista; aggiunge `caricaLista()`, `apriPreventivo()`, `eliminaPreventivo()`, `tornaLista()`; aggiunge bottone `← Lista` nell'action bar |
| `tests/test_routes.py` | Nuovo file con test per i due nuovi endpoint |
