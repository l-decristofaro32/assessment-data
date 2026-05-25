# Task 2 — ETL Pipeline

## Goal

Clean, normalize and validate heterogeneous raw datasets for downstream analytics and retrieval workflows.

## Main features

- ISO 8601 date normalization
- duplicate handling
- enum normalization
- null standardization
- GDPR-oriented pseudonymization
- lightweight schema validation with Pandera
- data quality reporting

## Run

```bash
uv run expected_output/task2/etl_pipeline.py
```

## Outputs

```text
cleaned_data/
├── projects.csv
├── interactions.csv
├── panelists.csv
├── agents.csv
└── methodologies.csv
```

## Validation

Run tests:

```bash
uv run pytest
```