# Analisi funzionale — CBD Preventivi

## 1. Scopo

CBD Preventivi è un tool web per la **creazione, gestione ed esportazione di computi metrici edilizi**. Permette a professionisti del settore (geometri, ingegneri, imprese edili) di costruire un preventivo voce per voce, inserire le misurazioni analitiche, calcolare i costi con analisi delle risorse e produrre un file xlsx compatibile con il software PriMus.

---

## 2. Requisiti

### 2.1 Requisiti funzionali

| ID   | Requisito |
|------|-----------|
| RF01 | L'utente può creare un nuovo preventivo vuoto |
| RF02 | L'utente può importare un preventivo da un file xlsx esportato da PriMus |
| RF03 | Il preventivo ha un'intestazione: nome, cliente, data, numero, ricarica default |
| RF04 | Il preventivo è composto da una lista ordinata di voci |
| RF05 | Ogni voce ha: codice, descrizione, unità di misura, ricarica (opzionale), misurazioni, risorse |
| RF06 | Le misurazioni sono righe con descrizione e fattori (par_ug, lung, larg, h/peso); la quantità è il prodotto dei fattori non nulli |
| RF07 | In alternativa ai fattori, ogni riga di misurazione può avere una **quantità diretta** (bypassa il prodotto) |
| RF08 | Se una voce non ha misurazioni, l'utente può inserire una **quantità manuale** |
| RF09 | Ogni voce ha un'analisi costi: lista di risorse (descrizione, UM, quantità, costo unitario) |
| RF10 | Il costo/UM è calcolato come totale costi ÷ quantità; se assente l'analisi costi usa il costo importato da PriMus |
| RF11 | Il prezzo/UM è costo/UM × (1 + ricarica); la ricarica è quella specifica della voce o quella default del preventivo |
| RF12 | L'importo di ogni voce è prezzo/UM × quantità totale |
| RF13 | Il preventivo mostra il totale costi (senza ricarica) e il totale con ricarica |
| RF14 | L'utente può salvare il preventivo (persistenza su disco) e ricaricarlo tramite URL |
| RF15 | L'utente può esportare il preventivo in formato xlsx compatibile con PriMus |
| RF16 | L'utente può tornare alla schermata iniziale senza perdere i dati salvati |

### 2.2 Requisiti non funzionali

| ID    | Requisito |
|-------|-----------|
| RNF01 | Il file xlsx esportato deve poter essere importato da PriMus senza errori |
| RNF02 | Il file xlsx esportato deve poter essere aperto da Excel senza dialog di riparazione |
| RNF03 | Il round-trip import → modifica → export → re-import deve preservare le quantità |
| RNF04 | Il backend è stateless: ogni richiesta è indipendente; lo stato persiste su file JSON |
| RNF05 | Il tool funziona in locale senza dipendenze da servizi esterni |

---

## 3. Attori e casi d'uso

**Attore principale:** utente (professionista edile)

| Caso d'uso | Descrizione |
|------------|-------------|
| Crea preventivo | Parte dalla landing, clicca «Nuovo preventivo», compila intestazione e voci |
| Importa da PriMus | Carica un xlsx PriMus; il backend lo analizza e crea un preventivo pre-popolato |
| Modifica preventivo | Aggiunge/rimuove voci, misurazioni, risorse; i calcoli si aggiornano in tempo reale |
| Salva preventivo | Il preventivo viene serializzato in JSON e salvato su disco; viene assegnato un ID |
| Ricarica preventivo | Accedendo a `/?id=xxx` il preventivo salvato viene ricaricato nell'editor |
| Esporta in PriMus | Scarica il file xlsx nel formato PriMus, pronto per essere importato nel software |

---

## 4. Modello dati

```
Preventivo
├── id: str (8 chars, UUID troncato)
├── nome, cliente, data, numero: str
├── ricarica_default: float (es. 0.20 = 20%)
└── voci: list[Voce]
        ├── codice, descrizione, um: str
        ├── ricarica: float | None   (None → eredita ricarica_default)
        ├── quantita_manuale: float | None
        ├── costo_override: float | None   (importato da PriMus J)
        ├── misurazioni: list[RigaMisurazione]
        │       ├── descrizione: str
        │       ├── par_ug, lung, larg, h_peso: float | None
        │       └── quantita_diretta: float | None
        └── risorse: list[RigaRisorsa]
                ├── descrizione, um: str
                ├── quantita: float
                └── costo_unitario: float
```

---

## 5. Logica di calcolo

```
quantita_riga    = quantita_diretta  oppure  PRODOTTO(fattori non nulli)
quantita_voce    = SOMMA(quantita_riga per tutte le righe valide)
                   oppure quantita_manuale (se nessuna misurazione)

totale_costi     = SOMMA(risorsa.quantita × risorsa.costo_unitario)
costo_per_um     = costo_override (se risorse assenti)
                   oppure totale_costi / quantita_voce
prezzo_per_um    = costo_per_um × (1 + ricarica_effettiva)
importo_voce     = prezzo_per_um × quantita_voce

totale_costi_preventivo   = SOMMA(costo_per_um × quantita_voce per ogni voce)
totale_preventivo         = SOMMA(importo_voce per ogni voce)
```

La stessa logica è implementata in modo speculare nel frontend (JavaScript) per il calcolo in tempo reale e nel backend Python (`calcoli.py`) per la generazione dell'xlsx.

---

## 6. Flusso import da PriMus

1. L'utente seleziona un file xlsx dalla landing page
2. Il file viene inviato a `POST /api/preventivo/import/primus`
3. Il parser (`primus/parser.py`) legge il foglio con una **macchina a stati**:

```
seek_voce → in_header → in_mis → after_marker → after_sommano → seek_voce
```

4. Per ogni voce estrae: codice (C), descrizione (D), misurazioni (E-H, I), costo/UM (J), UM dalla riga SOMMANO
5. Il preventivo risultante viene salvato e l'utente viene reindirizzato all'editor con `?id=xxx`

---

## 7. Flusso export in PriMus

1. L'utente clicca «Esporta Primus»; se non è ancora salvato, il frontend salva prima
2. Il backend chiama `GET /api/preventivo/{id}/export/primus`
3. `primus/export.py` costruisce il file xlsx con `openpyxl` seguendo il formato PriMus:
   - Righe intestazione (2-3), poi per ogni voce le righe strutturate (header, label, misurazioni, marker, SOMMANO, separatore)
   - Il costo in J è il `costo_per_um` **senza ricarica** (PriMus non gestisce la ricarica)
   - Formule reali: `=ROUND(PRODUCT(E:H),2)` per le misurazioni, `=ROUND(SUM(...),2)` per i SOMMANO, `=ROUND(SUM(K4:Kn),2)` per il TOTALE
4. Il file viene post-processato da `_converti_in_shared_strings()` (vedi §8.1)
5. Il browser scarica il file come allegato

---

## 8. Operazioni custom e non ovvie

### 8.1 Conversione inline strings → shared strings

**Problema:** openpyxl scrive le stringhe come *inline strings* (`t="inlineStr"` con `<is><t>...</t></is>`). PriMus richiede *shared strings* (`xl/sharedStrings.xml` con celle `t="s"` e indice intero).

**Soluzione:** dopo aver generato l'xlsx con openpyxl, la funzione `_converti_in_shared_strings()` post-processa il file zip:
- Scansiona tutti i worksheet XML e raccoglie le stringhe uniche
- Sostituisce ogni cella `t="inlineStr"` con `t="s"` + indice nello shared strings table
- Aggiunge `xl/sharedStrings.xml` con tutte le stringhe
- Aggiorna `[Content_Types].xml` e `xl/_rels/workbook.xml.rels` per dichiarare il nuovo file

Senza questa conversione PriMus restituisce «Cannot open sharedStrings.xml».

### 8.2 Celle placeholder vuote (non formula)

**Problema:** PriMus usa `<f>=</f>` come placeholder nelle celle I e K delle righe strutturali (intestazione voce, label misurazioni, separatore). Tuttavia `<f>=</f>` ha `=` come contenuto della formula, che Excel interpreta come formula `==` — invalida — e rimuove con il dialog «Record rimossi: Formula».

**Soluzione:** le celle placeholder vengono lasciate **vuote**. Il parser PriMus identifica le righe strutturali dal testo in colonna D (es. `M I S U R A Z I O N I:`, `SOMMANO`, `TOTALE euro`) e dal marker `N="3'"`, non dal valore di I o K. Il post-processing rimuove anche eventuali `<c ...><f/><v/></c>` residui convertendoli in celle vuote.

### 8.3 Righe «Vedi voce n° X» (quantità diretta)

**Problema:** in PriMus alcune voci referenziano la quantità di un'altra voce con una riga del tipo «Vedi voce n° 17 [mq 38.00]». In questo caso le colonne E-H sono vuote e la quantità (38.00) è nella colonna I come valore cache (il file viene letto con `data_only=True`).

**Import:** se E-H sono tutti `None` e I ha un valore numerico non nullo, la riga viene importata come `quantita_diretta` (non come fattori di prodotto).

**Export:** le righe con `quantita_diretta` vengono scritte con il valore direttamente in colonna I (non come formula `ROUND(PRODUCT(E:H))`) e con E-H vuoti. Questo preserva il round-trip: re-importando il file esportato, la stessa riga viene riconosciuta come `quantita_diretta`.

> Se invece si scrivesse `quantita_diretta` in colonna E (par_ug), al re-import verrebbe letto come fattore di prodotto anziché come quantità diretta — bug riscontrato e corretto.

### 8.4 Segnaposto quantità manuale

**Problema:** in PriMus le voci «a corpo» senza misurazioni esplicite vengono rappresentate con una singola riga di misurazione con solo `par_ug` valorizzato e nessuna descrizione. Il valore di `par_ug` è la quantità (tipicamente 1).

**Import:** il parser rileva questa condizione (1 sola riga, nessuna descrizione, solo `par_ug` non nullo) e converte in `quantita_manuale` invece di `misurazioni`.

**Export:** se non ci sono misurazioni valide e `quantita_manuale` è definita, viene scritta una riga placeholder con `par_ug = quantita_manuale` così `PRODUCT(E:H)` in PriMus restituisce il valore corretto.

### 8.5 Normalizzazione unità di misura

PriMus usa abbreviazioni diverse da quelle del tool:

| PriMus   | Tool     |
|----------|----------|
| `a`      | `a corpo` |
| `m2`     | `mq`     |
| `m3`     | `mc`     |
| `cadauno`| `cad`    |

La normalizzazione avviene in `_MAPPA_UM` nel parser. All'export non è necessario il mapping inverso perché il campo `um` viene scritto verbatim nella riga SOMMANO (`SOMMANO mq`, `SOMMANO a corpo`, ecc.) — PriMus accetta entrambe le forme.

### 8.6 Costo senza ricarica nell'export

PriMus gestisce i costi netti; la ricarica commerciale è responsabilità dello strumento di preventivazione (questo tool). Per questo motivo:

- La colonna J del SOMMANO viene popolata con `costo_per_um(voce)` (costo netto), **non** con `prezzo_per_um` (che includerebbe la ricarica)
- Il campo `costo_override` importato da PriMus rappresenta un costo netto; viene usato da `costo_per_um()` solo in assenza di risorse analitiche, così l'utente può aggiungere risorse per sovrascrivere il costo importato
- Nel frontend la voce mostra sia «Costo/UM» (con badge «importato» se da PriMus) sia «Prezzo/UM» (con ricarica applicata)
