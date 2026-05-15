# Piano di implementazione — Storico Preventivi (2026-05-15)

Riferimento spec: `2026-05-15-storico-preventivi-design.md`

---

## Step 1 — Backend: `GET /api/preventivi`

**File:** `src/cbd_preventivi/api/routes.py`

Aggiungere endpoint dopo `_salva()`:

```python
@router.get("/preventivi")
def lista_preventivi():
    files = sorted(DATA_DIR.glob("*.json"), key=lambda f: f.stat().st_mtime, reverse=True)
    result = []
    for f in files:
        try:
            data = Preventivo.model_validate_json(f.read_text())
            result.append({"id": data.id, "nome": data.nome, "data": data.data})
        except Exception:
            pass
    return result
```

---

## Step 2 — Backend: `DELETE /api/preventivo/{id}`

**File:** `src/cbd_preventivi/api/routes.py`

Aggiungere dopo `aggiorna_preventivo`:

```python
@router.delete("/preventivo/{id_preventivo}", status_code=204)
def elimina_preventivo(id_preventivo: str):
    percorso = _percorso_preventivo(id_preventivo)
    if not percorso.exists():
        raise HTTPException(status_code=404, detail="Preventivo non trovato")
    percorso.unlink()
```

---

## Step 3 — Test: `tests/test_routes.py`

Nuovo file con 4 casi:
- `GET /api/preventivi` con preventivi presenti → lista con nome/data
- `GET /api/preventivi` con DATA_DIR vuota → lista vuota
- `DELETE /api/preventivo/{id}` → 204 + file eliminato
- `DELETE /api/preventivo/inesistente` → 404

Usare `tmp_path` di pytest + override di `DATA_DIR` tramite env var `CBD_DATA_DIR`.

---

## Step 4 — Frontend: CSS lista

**File:** `frontend/index.html` — sezione `<style>`

Aggiungere stili per:
- `.lista-header` — header con titolo e pulsanti azione
- `.lista-table` — tabella preventivi (stessa estetica di `.recap-table`)
- `.lista-empty` — stato vuoto

---

## Step 5 — Frontend: HTML `screen-landing`

**File:** `frontend/index.html`

Sostituire il contenuto di `#screen-landing` con:
- Header: "I miei preventivi" + pulsanti "+ Nuovo" e "Importa PriMus"
- Tabella con `<tbody id="lista-tbody">`
- Stato vuoto `<div id="lista-empty">`
- Mantenere `<input id="primus-file-input">` nascosto per l'import

---

## Step 6 — Frontend: pulsante "← Lista" nell'action bar

**File:** `frontend/index.html`

Aggiungere `<button onclick="tornaLista()">← Lista</button>` come primo pulsante
nell'action bar dell'editor (prima di "Salva").

---

## Step 7 — Frontend: funzioni JS

**File:** `frontend/index.html` — sezione `<script>`

Aggiungere 4 funzioni prima di `// Init`:

### `caricaLista()`
```
GET /api/preventivi
→ se vuota: mostra #lista-empty, nasconde tabella
→ altrimenti: popola #lista-tbody con righe (nome, data, [Apri][Elimina])
→ mostra screen-landing
```

### `apriPreventivo(id)`
```
GET /api/preventivo/{id}
→ resetEditor()
→ popola intestazione (nome, cliente, data, numero, ricarica_default)
→ per ogni voce: templateVoce() + popolaVoce()
→ currentId = id
→ mostra screen-editor
```

### `eliminaPreventivo(id, nome)`
```
confirm("Eliminare «{nome}»?")
→ DELETE /api/preventivo/{id}
→ caricaLista()
```

### `tornaLista()`
```
se currentId → salva() (silenzioso)
→ nascondi screen-editor, screen-recap
→ caricaLista()
```

---

## Step 8 — Frontend: modifica `// Init`

**File:** `frontend/index.html`

Sostituire la chiamata iniziale che mostra `screen-landing` con `caricaLista()`
invece di mostrare i soli pulsanti statici.

---

## Step 9 — Eseguire i test

```bash
uv run pytest tests/test_routes.py -v
```

Tutti e 4 i nuovi test devono passare. Poi eseguire l'intera suite:

```bash
uv run pytest -v
```

---

## Step 10 — Commit e push

```
git add src/cbd_preventivi/api/routes.py frontend/index.html tests/test_routes.py
git commit -m "Aggiunge storico preventivi: lista, apri, elimina"
git push
```
