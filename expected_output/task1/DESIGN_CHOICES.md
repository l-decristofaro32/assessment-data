# Design choices

## Goal
The schema focuses on the normalized operational domain model required by the assignment. The AI retrieval layer is generated separately in Task 3 as a vector-ready JSONL knowledge base.

## Normalization
The core entities are separated into `workspaces`, `clients`, `projects`, `methodologies`, `panelists`, `support_agents`, `interactions`, and `faq_documents`. Repeating values such as methodology names, clients and managers are modeled as entities rather than duplicated text fields. This avoids update anomalies and supports controlled vocabularies.

## Multi-tenancy
`workspace_id` is part of the key for tenant-owned entities and appears on every queryable domain table. In production I would enforce tenant isolation at multiple levels: application authorization, database row-level security, vector-store metadata filters, and tenant-scoped encryption keys where required.

## Separation between relational model and RAG layer
The relational schema models the operational entities in 3NF. The RAG-oriented layer is generated separately in Task 3 through `knowledge_base.jsonl`, where chunks, embeddings and retrieval metadata are represented in a vector-ready format.

Early in the design, `document_chunks` and `embedding_metadata` were considered as relational tables to persist chunk metadata before vector indexing. For this assessment I kept them outside the relational schema to avoid overengineering and to make the pipeline easier to run and review.

## Query optimization
Indexes target likely agent questions: active projects by workspace/status, projects by research topic, and interactions by issue type/date/project.

## Data quality assumptions
Some records contain intentionally conflicting values. The ETL keeps the most complete canonical record for duplicates and records known quality issues, instead of silently hiding them. End dates before start dates are flagged because automatically correcting them would be unsafe.

## Tradeoffs and Design Decisions

### Why normalize the schema?
The schema was normalized to reduce duplication, improve consistency and simplify downstream analytics and retrieval workflows.

### Why separate projects, methodologies and interactions?
These entities have different lifecycles and update patterns. Separating them improves extensibility and avoids denormalized duplication.

### Why use workspace_id as tenant boundary?
The platform is designed as multi-tenant. Explicit tenant boundaries simplify governance, filtering and future semantic retrieval isolation.

### Why keep relational modeling even for RAG preparation?
Structured relational data remains useful for:
- governance,
- analytics,
- filtering,
- lineage,
- retrieval metadata enrichment.

The relational layer complements the semantic retrieval layer rather than replacing it.

### Why preserve invalid records instead of deleting them?
Potentially inconsistent records were retained and flagged to preserve traceability and avoid introducing unsupported assumptions during automated cleaning.