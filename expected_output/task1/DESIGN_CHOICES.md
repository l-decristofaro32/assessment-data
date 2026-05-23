# Design choices

## Obiettivo
Lo schema separa il modello di dominio operativo dal livello di recupero basato sull'intelligenza artificiale. Il compito richiede almeno la terza forma normale (3NF), ma l'obiettivo è quello di costruire una base di conoscenza interrogabile tramite modelli di linguaggio di grandi dimensioni (LLM), pertanto il modello include anche tabelle relative all'acquisizione dei dati e ai metadati dei blocchi.

## Normalizzazione
Le entità principali sono suddivise in `workspaces`, `clients`, `projects`, `methodologies`, `panelists`, `support_agents`, `interactions` e `faq_documents`. I valori ricorrenti, come i nomi delle metodologie, i clienti e i responsabili, sono modellati come entità anziché come campi di testo duplicati. Ciò consente di evitare anomalie negli aggiornamenti e supporta l'uso di vocabolari controllati.

## Multi-tenancy
`workspace_id` fa parte della chiave delle entità di proprietà del tenant e compare in ogni tabella di dominio interrogabile. In produzione, garantirei l'isolamento dei tenant su più livelli: autorizzazione dell'applicazione, sicurezza a livello di riga del database, filtri dei metadati del vector store e, dove necessario, chiavi di crittografia specifiche per tenant.

## Layer RAG
`document_chunks` and `embedding_metadata` sono stati volutamente esclusi dal modello operativo 3NF. Sono ottimizzati per il recupero dei dati, non per l'elaborazione delle transazioni. Ogni blocco memorizza il tipo di fonte, l'ID della fonte, l'ID dell'area di lavoro, l'hash del contenuto e i metadati, il che consente il re-embedding incrementale e la tracciabilità.

## Query optimization
Gli indici sono pensati per rispondere alle domande più frequenti degli agenti: progetti attivi per area di lavoro/stato, interazioni per tipo di ticket/data/progetto e segmenti per area di lavoro/fonte. L'indice GIN su `metadata` supporta il recupero filtrabile se i segmenti vengono salvati in PostgreSQL prima di essere trasferiti in un database vettoriale.

## Riflessioni sulla data quality
Alcuni record contengono valori intenzionalmente contraddittori. L'ETL conserva il record canonico più completo in caso di duplicati e registra i problemi di qualità noti, invece di nasconderli senza avvisare. Le date di fine precedenti alle date di inizio vengono segnalate perché correggerle automaticamente non sarebbe sicuro.