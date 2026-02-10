# Assignment

## Obiettivo

Creare una Knowledge Base ottimizzata per un agente AI che supporta il team della Megaditta nel rispondere a domande su progetti, panelisti e metodologie di ricerca.

## Riepilogo Deliverable

| Task | Deliverable | Formato |
|------|-------------|---------|
| 1 - DB Design | `schema.sql` o `schema_diagram.png/pdf` + `DESIGN_CHOICES.md` | SQL / immagine + Markdown |
| 2 - ETL | Script ETL + dati puliti + `data_quality_report.md` | Python/altro + CSV/JSON/Parquet/SQLite + Markdown |
| 3 - RAG KB | Script preparazione + `knowledge_base.jsonl` + `EMBEDDING_STRATEGY.md` | Python/altro + JSONL + Markdown |

Tutti i deliverable vanno salvati in `expected_output/`.

---

## Task 1: Database Design & Normalizzazione (30%)

Progetta uno schema di database normalizzato (almeno 3NF) che:

1. Elimini ridondanze e anomalie
2. Gestisca correttamente le relazioni tra entità
3. Sia ottimizzato per query frequenti dell'agente AI

**Criteri di accettazione**:
- Lo schema è almeno in terza forma normale (3NF)
- Entità chiave identificate e separate (progetti, panelisti, interazioni, agenti, ...)
- Relazioni con cardinalità corrette e chiavi esterne definite
- Tipi di dato appropriati per ogni colonna
- Le scelte progettuali sono documentate e motivate

**Deliverable**:
- File `schema.sql` o `schema_diagram.png/pdf`
- Breve documento `DESIGN_CHOICES.md` che spiega le tue decisioni

---

## Task 2: Pipeline ETL (40%)

Implementa una pipeline di estrazione, trasformazione e caricamento che:

1. Pulisca e normalizzi i dati grezzi
2. Gestisca duplicati, inconsistenze e dati mancanti
3. Anonimizzi eventuali dati sensibili (GDPR compliance)
4. Validi la qualità dei dati processati

**Hint sulle inconsistenze da cercare**:
- Formati di data non uniformi tra i record
- Tipi di dato incoerenti per lo stesso campo (stringhe vs numeri)
- Valori nulli rappresentati in modi diversi
- Duplicati non banali (stesso record con variazioni minime)
- Inconsistenze di case e formattazione
- Valori fuori range o logicamente impossibili

**Criteri di accettazione**:
- Tutti i formati di data sono normalizzati (ISO 8601 consigliato)
- I duplicati sono identificati e gestiti con strategia documentata
- I dati sensibili (email, telefono, nomi) sono anonimizzati
- Il report di qualità include statistiche su record processati, scarti, e problemi trovati
- La pipeline è riproducibile (eseguibile da zero senza intervento manuale)

**Deliverable**:
- Script (es. `etl_pipeline.py`)
- Dati puliti in formato strutturato (CSV, JSON, Parquet, o database SQLite)
- File `data_quality_report.md` con statistiche e issue trovati

---

## Task 3: Knowledge Base per RAG (30%)

Prepara i dati per retrieval semantico:

1. Genera embeddings per i contenuti testuali
2. Scegli strategia di chunking appropriata
3. Crea metadata utili per filtering/routing
4. Prepara output in formato ottimale per vector database

**Criteri di accettazione**:
- Strategia di chunking motivata e appropriata per i diversi tipi di contenuto
- Metadata strutturati che permettano filtering per source, categoria, data
- Embeddings generati con modello dichiarato e dimensioni documentate
- Output JSONL valido e ben strutturato

**Deliverable**:
- Script (es. `prepare_knowledge_base.py`)
- Output in formato JSONL con struttura:
```json
{
  "id": "unique_id",
  "content": "text chunk",
  "embedding": [0.1, 0.2, ...],
  "metadata": {
    "source": "projects|interactions|faq",
    "category": "...",
    "created_at": "ISO timestamp",
    ...
  }
}
```
- Documento `EMBEDDING_STRATEGY.md` che spiega le tue scelte

**Esempio di output atteso** (1 record):
```json
{
  "id": "faq-methodology-001",
  "content": "CAWI sta per Computer Assisted Web Interviewing. È un metodo di raccolta dati tramite questionari online auto-compilati. I panelisti ricevono un link via email e completano il sondaggio sul proprio dispositivo. Vantaggi: costi ridotti, tempi rapidi, possibilità di includere contenuti multimediali. Tempi medi di completamento: 15-20 minuti per sondaggi standard.",
  "embedding": [0.023, -0.041, 0.089, "... (384 o 1536 dimensioni a seconda del modello)"],
  "metadata": {
    "source": "faq",
    "category": "metodologie",
    "subcategory": "CAWI",
    "language": "it",
    "created_at": "2024-04-01T00:00:00Z"
  }
}
```

---

## Struttura consigliata per `expected_output/`

```
expected_output/
├── task1/
│   ├── schema.sql (o schema_diagram.png/pdf)
│   └── DESIGN_CHOICES.md
├── task2/
│   ├── etl_pipeline.py (o altro linguaggio)
│   ├── cleaned_data/
│   │   ├── projects.csv (o .json, .parquet, .sqlite)
│   │   ├── interactions.csv
│   │   └── ...
│   └── data_quality_report.md
└── task3/
    ├── prepare_knowledge_base.py
    ├── knowledge_base.jsonl
    └── EMBEDDING_STRATEGY.md
```

---

## Bonus (Opzionale)

- Implementa un semplice retrieval test (query di esempio + risultati)
- Aggiungi monitoring/logging alla pipeline
- Aggiungi unit tests
- Dockerizza la pipeline per riproducibilità

## Note Importanti

> **I dati contengono inconsistenze intenzionali** - parte dell'assessment è identificarle e gestirle correttamente. Non tutti gli errori sono ovvi: alcuni richiedono analisi cross-field o cross-record.

## Domande?

Se qualcosa non è chiaro, fai assunzioni ragionevoli e documentale nel README del tuo fork. Valutiamo anche la capacità di prendere decisioni autonome.
