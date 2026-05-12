# CBD Preventivi

Tool web per la creazione e gestione di **computi metrici edilizi**, con supporto completo per l'import e l'export nel formato PriMus (xlsx).

## Funzionalità

- Creazione di preventivi con voci, misurazioni analitiche e analisi costi
- Calcolo automatico di quantità, costo/UM e prezzo/UM con ricarica configurabile
- Import da file xlsx esportato da PriMus (con normalizzazione UM e gestione righe «Vedi voce»)
- Export in formato xlsx compatibile con PriMus ed Excel (shared strings, formule ROUND/SUM/PRODUCT)
- Persistenza su disco (file JSON per preventivo)

## Struttura del progetto

```
cbd-preventivi/
├── src/
│   └── cbd_preventivi/
│       ├── models.py           # Modelli di dominio (Pydantic)
│       ├── calcoli.py          # Logica di calcolo
│       ├── primus/
│       │   ├── export.py       # Generazione xlsx PriMus
│       │   └── parser.py       # Parsing xlsx PriMus
│       └── api/
│           ├── app.py          # Applicazione FastAPI + entry point
│           └── routes.py       # Endpoint REST
├── frontend/
│   └── index.html              # UI single-page (vanilla JS)
├── tests/
│   └── test_export_primus.py
├── data/                       # Preventivi salvati (gitignored)
└── pyproject.toml
```

## Requisiti

- Python ≥ 3.11
- [uv](https://docs.astral.sh/uv/)

## Installazione e avvio

```bash
# Clona il repository e posizionati nella directory
cd cbd-preventivi

# Installa le dipendenze con uv
uv sync

# Avvia il server di sviluppo
uv run cbd-preventivi
```

L'applicazione sarà disponibile su [http://localhost:8000](http://localhost:8000).

In alternativa con uvicorn direttamente:

```bash
uv run uvicorn cbd_preventivi.api.app:app --reload
```

## Configurazione

| Variabile d'ambiente | Default | Descrizione                        |
|----------------------|---------|------------------------------------|
| `CBD_DATA_DIR`       | `data`  | Directory di persistenza dei file JSON |

## Test

```bash
uv run pytest
```

## Build eseguibile Windows (.exe)

```bash
uv run python build.py
```

Produce `dist/cbd-preventivi/` con l'eseguibile e tutte le dipendenze bundlate.
Per distribuire: zippare la cartella e consegnarla all'utente finale.

L'utente fa doppio click su `cbd-preventivi.exe`: il server si avvia e il browser
si apre automaticamente su `http://127.0.0.1:8000`. I dati vengono salvati nella
cartella `data/` accanto all'eseguibile, e restano tra un aggiornamento e l'altro.

> Il build su macOS produce un binario macOS. Per il `.exe` Windows è necessario
> eseguire `uv run python build.py` su un PC Windows.

## API REST

| Metodo | Percorso                                  | Descrizione                         |
|--------|-------------------------------------------|-------------------------------------|
| POST   | `/api/preventivo`                         | Crea un nuovo preventivo            |
| GET    | `/api/preventivo/{id}`                    | Carica un preventivo                |
| PUT    | `/api/preventivo/{id}`                    | Aggiorna un preventivo              |
| POST   | `/api/preventivo/import/primus`           | Importa da file xlsx PriMus         |
| GET    | `/api/preventivo/{id}/export/primus`      | Esporta in xlsx PriMus              |

## Formato PriMus

Il formato xlsx PriMus ha alcune peculiarità gestite dal tool:

- **Shared strings**: PriMus richiede `xl/sharedStrings.xml`; openpyxl scrive inline strings. L'export post-processa il file per convertirle.
- **Unità di misura**: PriMus usa `a`, `m2`, `m3`, `cadauno`; il tool normalizza verso `a corpo`, `mq`, `mc`, `cad`.
- **Righe «Vedi voce»**: righe con quantità già calcolata (E-H vuoti, valore in I) vengono importate come `quantita_diretta` e riesportate preservando il round-trip.
- **Costi senza ricarica**: PriMus lavora con i costi netti; la ricarica viene gestita separatamente dal tool.
