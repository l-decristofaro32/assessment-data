# Expected Output

Organizza i tuoi deliverable in questa directory seguendo la struttura suggerita:

```
expected_output/
├── task1/
│   ├── schema.sql                    # Schema DDL (o schema_diagram.png/pdf)
│   └── DESIGN_CHOICES.md             # Motivazioni delle scelte progettuali
├── task2/
│   ├── etl_pipeline.py               # Script ETL (o altro linguaggio)
│   ├── cleaned_data/                 # Dati puliti e normalizzati
│   │   ├── projects.csv              # (o .json, .parquet, .sqlite)
│   │   ├── interactions.csv
│   │   └── ...
│   └── data_quality_report.md        # Report qualità dati
└── task3/
    ├── prepare_knowledge_base.py     # Script generazione KB
    ├── knowledge_base.jsonl          # Output embeddings
    └── EMBEDDING_STRATEGY.md         # Strategia chunking/embedding
```

Sei libero di adattare la struttura se hai buone ragioni per farlo - documentalo nel tuo README.
