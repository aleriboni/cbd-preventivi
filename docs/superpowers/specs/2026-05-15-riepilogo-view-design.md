# Design — Pagina Riepilogo (2026-05-15)

## Scope

Aggiunta di una schermata `screen-recap` in sola lettura che mostra il preventivo
in formato tabellare completo: una riga per voce con tutti i valori economici,
espandibile per vedere misurazioni e costi analitici.

---

## Navigazione

### Accesso

Nuovo pulsante **"Riepilogo"** nell'action bar dell'editor, accanto a "Salva" e
"Esporta Primus". Al click:

1. Se il preventivo non è ancora salvato, viene salvato automaticamente
   (riutilizza la logica del pulsante "Salva" esistente)
2. `screen-editor` si nasconde
3. `renderRiepilogo()` popola la tabella con i dati correnti
4. `screen-recap` appare

### Ritorno all'editor

Pulsante **"← Editor"** nell'header del recap. Al click:

- `screen-recap` si nasconde
- `screen-editor` riappare
- Nessun ricalcolo necessario (i dati nell'editor sono invariati)

---

## Layout schermata

```
┌─────────────────────────────────────────────────────────────────┐
│ ← Editor                                       CBD Preventivi   │
├─────────────────────────────────────────────────────────────────┤
│ Riepilogo — [nome preventivo]                                   │
│ Cliente: …  ·  Data: …  ·  N°: …  ·  Ric. default: …%         │
├─────────────────────────────────────────────────────────────────┤
│ Nr · Cod · Descrizione · UM · Q.tà · C/UM · Tot.C · Ric% · P/UM · Prezzo │
├─────────────────────────────────────────────────────────────────┤
│ ▸ 1  001  Approntamento area…  ac  1,00  —  —  0%  €11.800  €11.800 │
│ ▾ 2  003  Demolizione tramezze…  mc  28,75  €22  €635  0%  €22  €635 │
│   ├─ Misurazioni ─────────────────────────────────────────────  │
│   │  Tramezza sp 20 …  1  4,2  0,2  3,3  —  2,77               │
│   │  …                                                          │
│   └─ Costi ───────────────────────────────────────────────────  │
│      Operaio  ore  10  €31  €310                                │
│      …                                                          │
├─────────────────────────────────────────────────────────────────┤
│                              TOTALE COSTI  €…  PREZZO  €…       │
└─────────────────────────────────────────────────────────────────┘
```

---

## Colonne riga principale

| # | Header | Valore | Note |
|---|---|---|---|
| 1 | Nr. | indice 1-based | |
| 2 | Codice | `voce.codice` | |
| 3 | Descrizione | `voce.descrizione` | testo completo, no troncamento |
| 4 | UM | `voce.um` | |
| 5 | Q.tà | `quantita_x(voce)` | |
| 6 | Costo/UM | `costo_per_um` | `—` se solo `prezzo_override` |
| 7 | Tot. costi | `costo_per_um × quantita_x` | `—` se no analisi costi |
| 8 | Ric. % | `ricarica_effettiva × 100` | evidenziata in blu se ≠ default |
| 9 | Prezzo/UM | `prezzo_per_um` | badge "importato" se `prezzo_override` |
| 10 | **Prezzo** | `prezzo_per_um × quantita_x` | in blu, colonna principale |

---

## Riga espandibile

Click sulla riga principale toglie/aggiunge la classe `.expanded` e mostra un
pannello `.recap-detail` con due sotto-tabelle.

### Sotto-tabella Misurazioni

Colonne: Descrizione · Par.ug · Lung. · Larg. · H/peso · Q.tà diretta · **Quantità**

- Mostrata solo se `voce.misurazioni` non è vuota
- Le colonne fattore (Par.ug … H/peso) mostrano `—` se `null`
- Quantità calcolata come `quantitaRiga(mis)` (già disponibile nel JS)

### Sotto-tabella Costi

Colonne: Descrizione · UM · Q.tà · Costo unit. · **Totale**

- Mostrata solo se `voce.costi` non è vuota
- Se né misurazioni né costi esistono: nessun pannello espandibile (▸ non appare)

---

## Riga totale

Ultima riga della tabella, non espandibile:

- **Tot. costi**: somma di `(costo_per_um × quantita_x)` per tutte le voci con analisi
- **Prezzo**: somma di `(prezzo_per_um × quantita_x)` per tutte le voci

---

## Dati e calcoli

`renderRiepilogo()` chiama `raccogliPreventivo()` per leggere lo stato corrente
del DOM dell'editor. Per ogni voce usa le funzioni JS già esistenti:
`calcVoce(id)`, `quantitaX(id)`, `getMisurazioni(id)`, `getCosti(id)`.

**Nessuna nuova chiamata API.** Il backend non è toccato.

---

## File coinvolti

| File | Modifica |
|---|---|
| `frontend/index.html` | Aggiunge `screen-recap`, pulsante "Riepilogo", `renderRiepilogo()`, `toggleRigaRiepilogo()`, CSS recap |
