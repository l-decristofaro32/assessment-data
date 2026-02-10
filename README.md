# AI Engineer Assessment

Benvenuto! Questo assessment è progettato per valutare le tue competenze in:
- Normalizzazione e design di database
- Pipeline ETL e data transformation
- Preparazione dati per sistemi RAG/Knowledge Base
- Integrazione con agenti AI

## Scenario

Lavori per la **Megaditta (ItalPetrolCemenTermoTessilFarmoMetalChimica)**, una piattaforma di ricerche di mercato. Hai ricevuto dati grezzi da tre fonti diverse che devono essere normalizzati e preparati per alimentare un agente AI che risponde a domande su:
- Progetti di ricerca attivi
- Interazioni con i panelisti
- Metodologie di ricerca

## Struttura Repository

```
├── data/                          # Dataset grezzi (NON MODIFICARE)
│   ├── projects_raw.csv          # 30+ progetti di ricerca
│   ├── panelist_interactions.json # 20+ interazioni customer support
│   └── research_faq.txt          # FAQ metodologie di ricerca
├── expected_output/               # Metti qui i tuoi output
│   └── README.md                 # Struttura attesa dei deliverable
├── ASSIGNMENT.md                  # Istruzioni dettagliate
└── README.md                      # Questo file
```

## Dataset

| File | Formato | Record | Contenuto |
|------|---------|--------|-----------|
| `projects_raw.csv` | CSV | ~30 righe | Progetti di ricerca con metadati (clienti, budget, metodologia, status) |
| `panelist_interactions.json` | JSON | ~20 record | Log interazioni customer support con panelisti |
| `research_faq.txt` | TXT | ~150 righe | FAQ su metodologie di ricerca, pricing, privacy, processi |

> **Nota**: I dati contengono inconsistenze intenzionali (formati misti, duplicati, valori mancanti, errori di tipo). Parte dell'assessment è identificarle e gestirle.

## Quick Start

1. **Fai un fork** di questa repo
2. Leggi attentamente [`ASSIGNMENT.md`](ASSIGNMENT.md) per i requisiti dettagliati
3. Analizza i dati in `data/` - presta attenzione alla qualità dei dati
4. Completa i 3 task richiesti
5. Salva tutti i tuoi output in `expected_output/`
6. Condividi il link al tuo fork quando hai completato

## Criteri di Valutazione

| Task | Peso | Focus |
|------|------|-------|
| Database Design & Normalizzazione | 30% | Schema 3NF, relazioni tra entità, scelte progettuali |
| Pipeline ETL | 40% | Pulizia dati, gestione inconsistenze, GDPR, data quality |
| Knowledge Base per RAG | 30% | Embeddings, chunking strategy, metadata design |

## Regole

- **Linguaggio**: Libera scelta (Python consigliato ma non obbligatorio)
- **Librerie**: Libera scelta
- **Embeddings**: Scegli il modello che preferisci (OpenAI, open-source, etc.)
- **Documentazione**: Spiega le tue scelte tecniche nei file `.md` richiesti
- **Tempo**: Non c'è un limite rigido, ma l'esercizio è pensato per ~4 ore di lavoro

## Consegna

Crea un fork di questa repo e condividi il link quando hai completato l'assessment.

## Domande?

Se qualcosa non è chiaro, fai assunzioni ragionevoli e documentale. Valutiamo anche la capacità di prendere decisioni autonome in contesti ambigui.

Buon lavoro! 🚀
