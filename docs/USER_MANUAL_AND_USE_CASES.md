# ETL-HALE-BOPP: User Manual & Use Cases

Questo manuale è progettato per Operatori Data, DevOps e Agenti Kortex che devono interagire con l'orchestratore **ETL-HALE-BOPP**. L'obiettivo è fornire una guida chiara su come avviare il motore e quali sono i casi d'uso (Use Cases) previsti dalla sua architettura config-driven.

---

## 🚀 1. Requisiti Hardware e Installazione (Sotto il cofano)

L'infrastruttura ETL-HALE-BOPP è progettata per essere leggera, ma orchestrare container richiede specifiche minime per garantire la stabilità di Airflow e Postgres.

### Requisiti di Sistema (Risorse Minime)
Per far girare l'intera architettura in un singolo nodo (Single-Node Deploy):
*   **CPU**: Minimo 2 vCPU (Consigliate 4 vCPU per processare parallelamente trasformazioni DB e chiamate API).
*   **RAM**: Minimo 4 GB (Consigliati 8 GB, in quanto scheduler, webserver e database Postgres girano simultaneamente in RAM dedicata).
*   **Disco**: 20 GB di spazio libero (Immagini Docker, logs di esecuzione storicizzati nel DB Postgres e dati temporanei in `/opt/airflow/data`).
*   **Motore Container**: Docker Engine con plugin Docker Compose V2 (o Podman).
*   **Shell**: PowerShell 7+ (necessario per gli script `.ps1` di orchestrazione).

### Cosa succede durante l'Installazione?
L'approccio "1-Click" si basa su script PowerShell che mascherano la complessità operativa per l'utente, ma ecco cosa fanno sotto il cofano:

1. **Il comando `pwsh ./scripts/install.ps1`**:
   *   Verifica che la macchina ospiti Docker e Docker Compose V2. Se mancano, blocca l'installazione spiegando l'errore (Fail-Fast pattern).
   *   Crea il file `.env` copiandolo da `.env.example`. Questo file conterrà le variabili isolate dal repository (es. `AIRFLOW_ADMIN_PASSWORD`). **Nessun certificato o password viene storato su Git.**
2. **Il comando `pwsh ./scripts/bootstrap.ps1 -Mode init`**:
   *   Crea un container effimero (`airflow-init`) che effettua le "Migrazioni del Database" su Postgres per creare le tabelle di Airflow.
   *   Crea programmaticamente l'utente Amministratore nativo in base alle variabili lette dal `.env`.
3. **Il comando `pwsh ./scripts/bootstrap.ps1 -Mode up`**:
   *   Avvia i demoni persistenti: `Webserver` (la UI visibile su localhost:8080), lo `Scheduler` (il cuore battente che valuta il cron del file YAML ogni pochi secondi) e il `Triggerer` (per operazioni asincrone).

### Sequenza di Avvio Rapido (Bootstrap)
1. **Configurazione Iniziale**: Navigare nella cartella `C:\old\ETL-HALE-BOPP` ed eseguire l'installer per preparare l'ambiente virtuale e i file `.env`:
   ```powershell
   pwsh ./scripts/install.ps1
   ```
2. **Inizializzazione Database (Una Tantum)**: Inizializza il DB Postgres interno di Airflow e l'utente amministratore (credenziali di default: `admin`/`admin`, modificabili nel `.env`):
   ```powershell
   pwsh ./scripts/bootstrap.ps1 -Mode init
   ```
3. **Accensione del Motore**: Tirare su l'intera stack in background:
   ```powershell
   pwsh ./scripts/bootstrap.ps1 -Mode up
   ```
4. **Accesso alla Console**: Aprire il browser all'indirizzo `http://127.0.0.1:8080` (vincolato a localhost per sicurezza Zero Trust).

---

## 🎯 2. Use Cases (Casi d'Uso) in ottica Hale-Bopp

ETL-HALE-BOPP non è un semplice Airflow; è un **Orchestratore Dichiarativo**. I DAG non vengono scritti in codice Python dai Data Engineer, ma dichiarati in un file `pipelines.yaml`.

Ecco i principali *Use Cases* previsti dal sistema:

### Use Case 1: L'Elaborazione Notturna (Daily ETL)
*   **Scenario**: Ogni notte alle 04:00 del mattino (cron: `0 4 * * *`), i dati dal Data Portal devono essere consolidati nel Data Warehouse.
*   **Come si usa**: Nel file `config/orchestration/pipelines.yaml` è definito il workflow `etlb_daily_pipeline`. Questo richiama un workflow pre-costruito (`daily_etl_n8n`) che innesca Airflow per contattare i webhook esterni (es. su n8n) che materialmente muovono i dati.
*   **Vantaggio Antifragile**: Nessun codice scritto Custom. Se il target webhook cambia, basta aggiornare lo YAML: `endpoint: /webhook/etlb-daily`.

### Use Case 2: Il Trigger Event-Driven (Streaming/Rest API)
*   **Scenario**: Il Data Portal riceve un file massivo caricato da un utente e deve processarlo *immediatamente*, senza aspettare il batch notturno.
*   **Come si usa**: La pipeline `etlb_event_pipeline` (configurata senza cron, `schedule: null`) aspetta di essere invocata via REST API. 
*   **Esecuzione via API**: Gli agenti o le web-app possono chiamare l'API di Airflow per lanciare la pipeline passandogli un payload dinamico:
    ```json
    POST http://127.0.0.1:8080/api/v1/dags/etlb_event_pipeline/dagRuns
    { "conf": { "source_file": "upload_123.csv" } }
    ```

### Use Case 3: Il Quality Gate (Data Governance)
*   **Scenario**: Prima di inviare i dati ai cruscotti BI, è necessario eseguire uno script di Quality Assurance per scovare anomalie o dati corrotti.
*   **Come si usa**: La `etlb_quality_gate_pipeline` viene schedulata subito dopo il Daily (es. `30 4 * * *`). Essa lancia comandi Bash o script Python sanitizzati per interrogare il DB. Se il Quality Gate fallisce, l'orchestratore blocca la chain e notifica gli operatori.

### Use Case 4: L'"Inoculazione" di nuove Pipeline tramite Kortex (Agentic Workflow)
*   **Scenario (Futuro Hale-Bopp)**: PM Agent deduce un nuovo requisito di business. Non serve un programmatore per scrivere il DAG.
*   **Come si usa**: Kortex o il Discovery Agent operano una Pull Request modificando esclusivamente `config/orchestration/pipelines.yaml` inserendo un nuovo blocco Yaml. Al commit, un hook riavvia Airflow (`pwsh ./scripts/bootstrap.ps1 -Mode restart`). Il `dag_factory.py` si accorgerà del nuovo nodo Yaml, validerà lo schema, e automaticamente materializzerà la pipeline nell'interfaccia UI.

### Use Case 5: Trasformazioni Dati Native (Unzip, Load DB)
*   **Scenario**: Devi scaricare un file ZIP da un SFTP/HTTP, scompattarlo ed eseguire una bulk insert su un Database Relazionale, ma non vuoi scrivere codice Python.
*   **Come si usa**: Sfrutta la libreria di workflow nativi dentro `common_utilities`. Nel file YAML dichiari semplicemente:
    ```yaml
    workflow_ref:
      id: extract_and_unzip
      context:
        source_url: "https://dati.gov.it/dataset.zip"
        dest_folder: "/opt/airflow/data/inbound"
    ```
    E un DAG dipendente o la task successiva può agganciarlo al caricamento:
    ```yaml
    workflow_ref:
      id: load_to_db
      context:
        file_path: "/opt/airflow/data/inbound/data.csv"
        table_name: "public.anagrafica_clienti"
    ```
*   **Chi fa la trasformazione?**: La trasformazione è eseguita dai Worker di Airflow avvalendosi dei prebuilt Python Operators in `common_utilities/workflows/prebuilt.py`. Nessuno sviluppatore scrive la logica di unzip, la si riusa come un mattoncino Lego.

### Use Case 6: Routing Dinamico (Il "Bilanciatore" Intelligente)
*   **Scenario**: Vuoi aggiornare una tabella usando un file CSV. Se il file pesa meno di 100 MB, va bene elaborarlo localmente in RAM (veloce ed economico). Se il file pesa 5 GB, elaborarlo localmente bloccherebbe il nodo, quindi devi demandare il lavoro asincrono ad Apache Spark.
*   **Come si usa**: Grazie al pattern del *Dynamic Routing* (basato sul `BranchPythonOperator` di Airflow), nel file YAML si implementa il "Bilanciatore":
    ```yaml
    workflow_ref:
      id: dynamic_file_router
      context:
        file_path: "/opt/airflow/data/inbound/update.csv"
        threshold_mb: 100
    ```
*   **Cosa succede dietro le quinte**: Airflow esamina dinamicamente le dimensioni del file a runtime.
    *   **Se < 100 MB**: Esegue il set di istruzioni Python in locale (Pandas/SQLAlchemy). L'elaborazione è sincrona.
    *   **Se > 100 MB**: Salta l'esecuzione locale e innesca una chiamata API verso il cluster Spark/Databricks, mettendosi in attesa della fine del job (Sensors).
*   **Il vantaggio**: Ottimizzi i costi del cluster (usando Spark solo quando realmente serve) ed eviti colli di bottiglia su Airflow.

---

## 🤖 4. L'Assistente AI per l'Orchestrazione (Hale-Bopp AI Agent)

Per chiudere il cerchio della Governance e garantire che l'utente finale rispetti le regole **senza alcuno sforzo**, l'architettura ETL-HALE-BOPP prevede l'integrazione di un **AI Assistant dedicato** (es. _Agent_ETL_Builder_).

### Retrival-Augmented Generation (RAG) come Memoria Operativa
Come fa l'Agente a sapere quali tabelle di destinazione usare, o con quali file YAML preesistenti confrontare la nuova pipeline? L'AI non "tira a indovinare", ma consulta un vero e proprio **RAG (Retrieval-Augmented Generation)** agganciato a:

1.  **Vettorializzazione del Postgres di Airflow**: I metadati dei DAG (quali pipeline esistono, quanti task hanno fallito) sono estratti, vettorizzati e indicizzati in un Vector Database (es. Qdrant o ChromaDB).
2.  **Libreria dei LEGO Blocks**: Tutti i template disponibili in `common_utilities/workflows` (es. `extract_and_unzip`) e i relativi esempi yaml vengono indicizzati nel RAG.
3.  **Data Dictionary**: I tracciati record delle tabelle finali.

### Il Flusso Operativo dell'Assistente AI:
Invece di chiedere all'utente business di scrivere la sintassi YAML (col rischio di errori di indentazione o chiamate non valide), l'utente interagirà in linguaggio naturale (ChatOps) con l'Agente.

*   **L'Utente chiede**: *"Ho bisogno di scaricare ogni mattina alle 6:00 il file `clienti.csv` da questo link e caricarlo nella tabella `prod_clienti`."*
*   **L'Agente Esegue**:
    1. L'AI comprende la richiesta.
    2. Interroga in parallelo il **Vector DB (RAG)**: *"Ho già una pipeline che scrive in `prod_clienti`?"* Se sì, evita duplicati. *"Qual è lo YAML snippet per scaricare e caricare un CSV?"* (Il RAG gli restituisce l'esempio di `extract_and_unzip`).
    3. Usa il Vector DB per garantirsi di rispettare le regole semantiche.
    4. Scrive programmaticamente il blocco in `pipelines.yaml` usando lo schema rigoroso e validato dal RAG.
    5. Esegue una Pull Request (o committa direttamente) scatenando l'aggiornamento automatico di Airflow.

Questo approccio ibrido (Agentic Workflow + RAG = **Agentic RAG**) annulla il rischio di malconfigurazioni umane (**Paved Road** totale): l'utente ottiene esattamente ciò che vuole parlando, mentre il reparto Security/Engineering dorme sonni tranquilli perché l'Agente agirà su basi certe, contestualizzando su dati aziendali reali.

---

## 🏗️ 5. Il "Control Plane" (Astrazione Assoluta)

L'ultimo step evolutivo previsto dall'architettura Hale-Bopp per non far toccare **né Python né YAML** agli utenti finali è la creazione di un **Control Plane**.

Poiché il motore (`dag_factory.py`) legge un semplice file di testo (`pipelines.yaml`), il processo di generazione dello YAML può essere completamente disaccoppiato dall'Orchestratore vero e proprio:

1.  **L'Approccio "Excel-to-YAML" (Citizen Developer Base)**
    *   Si fornisce all'utente aziendale un file `.xlsx` formattato come un modulo (Es. Nome Pipeline, URL Sorgente, Tabella Destinazione, Orario).
    *   L'utente carica il file Excel in una cartella condivisa (o SharePoint).
    *   Una macro, una Cloud Function o un webhook su n8n "mangia" l'Excel e converte le righe in sintassi YAML validata, sovrascrivendo il `pipelines.yaml`.

2.  **L'Approccio Web UI (Enterprise Control Plane)**
    *   Avremo un Front-End interno (es. un portale scritto in Next.js/React o generato da un Agente).
    *   Tramite l'interfaccia visiva, gli utenti compilano box e menu a tendina.
    *   I dati vengono salvati su un Database Operazionale (es. MySQL o lo stesso Postgres).
    *   Un generatore (`yaml_generator.py`) esegue una query sul DB, unisce le configurazioni "Globali" (le policy auree aziendali immutabili) con quelle "Locali" (inserite dall'utente), ed esporta il file `pipelines.yaml`.

**Risultato**: `dag_factory.py` di Airflow si limita a leggere il risultato finale di questa catena di montaggio. Che lo generi un Umano (scrivendo YAML), un Agente AI (tramite Chat) o un Control Plane (tramite Web UI/Excel), Airflow non se ne accorgerà nemmeno, limitandosi a eseguire il lavoro sporco con la massima sicurezza e stabilità.

---

## 🔒 6. Gestione Connettori e Segreti (Nessuna Password in Chiaro)

Nel mondo legacy, i Data Engineer piazzano password in chiaro negli script Python o nei file `.env` sparsi per i server. In ETL-HALE-BOPP, la gestione delle credenziali verso i sistemi esterni (Data Lake AWS S3, Oracle, Snowflake, REST API) è centralizzata e criptata by-design.

### 1. Airflow Connections (Il Vault Sicuro)
*   Le credenziali non si scrivono nello YAML. Nello YAML si passa solo un "Puntatore" (es. `conn_id: "oracle_legacy_db"`).
*   L'Amministratore o l'Agente configura la connessione `oracle_legacy_db` una sola volta nell'interfaccia di Airflow (o via CLI/Terraform).
*   Airflow salva la password nel suo database Postgres, ma **non in chiaro**: viene criptata usando la master key simmetrica `FERNET_KEY`.

### 2. Gli "Airflow Providers" (Connettori Ufficiali)
Come ci connettiamo a un sistema esotico o a un Data Lake? Non si reinventa la ruota. 
Apache Airflow vanta centinaia di librerie ufficiali chiamate **Providers**. 
*   Basta aggiungere `apache-airflow-providers-snowflake` (o AWS, Azure, Google) nel nostro `requirements.txt`.
*   Airflow eredita istantaneamente la capacità di parlare con quel sistema usando le sue API native, in modo sicuro ed efficientemente ottimizzato per i Big Data.
*   I nostri LEGO blocks in `prebuilt.py` importeranno questi operatori ufficiali e faranno il lavoro pesante.

### 3. Secret Backends (Per Ambienti Zero-Trust)
Se le policy aziendali vietano di salvare le password persino nel Postgres criptato di Airflow, il sistema supporta nativamente i **Secret Backends**.
*   Airflow viene configurato per non salvare nulla localmente. Quando un DAG ha bisogno della password di Oracle, invia una chiamata API al volo a **HashiCorp Vault**, ad **Azure Key Vault** o ad **AWS Secrets Manager**, recupera il segreto, lo usa in RAM per la durata del task e poi lo getta via. Questo è il gold standard della Security.

---

## 📝 7. Osservabilità e Logging (Zero-Hardcoding)

Il sistema dei log in ETL-HALE-BOPP è progettato per garantire il massimo livello di configurabilità senza mai scendere a compromessi alterando i container o hardcodando percorsi su file.

### 1. Architettura Parametrica nel `.env`
L'intero strato di log è iniettato nei container (`docker-compose.yml`) tramite variabili d'ambiente. Tutte le configurazioni si comandano da un unico file `.env` senza mai toccare l'architettura:
```ini
ETLBELVISO_LOG_PATH=/opt/airflow/logs
ETLBELVISO_REMOTE_LOGGING=False
ETLBELVISO_REMOTE_LOG_PATH=
ETLBELVISO_REMOTE_CONN_ID=
```

### 2. Local Logging vs Remote Logging
*   **Local Logging (Default)**: Di default, i log vengono salvati nel volume montato (specificato da `ETLBELVISO_LOG_PATH`). Da qui finiscono nel database Postgres (tabelle `task_instance` e `dag_run`), offrendo all'interfaccia web di Airflow una vista in streaming completa sugli errori.
*   **Remote Logging (Enterprise/Multi-Node)**: Nelle configurazioni massive, accumulare log su disco porta al collasso del server (Disk Full). Modificando la variabile `ETLBELVISO_REMOTE_LOGGING=True` e specificando una connessione Cloud (es. `aws_s3`, `azure_blob`, `elastic`), Airflow smetterà di scrivere log persistenti sul server. Al termine di ogni esecuzione, invierà l'output su Cloud Storage. Grazie all'ingegnoso design di Airflow, anche con i file remoti, **l'interfaccia UI continuerà a mostrarli a schermo in tempo reale** interrogando il Cloud Provider in background in totale trasparenza.

### 3. Prevenzione Data Leakage (Log Masking Nativo)
Il rischio aziendale più grande è che un errore in uno script Python stampi a video una password o i dati personali (PII) dei clienti, rendendoli visibili nei log. ETL-HALE-BOPP risolve questo rischio alla radice grazie al **Log Masking**:

1.  **Masking Automatico dei Segreti**: Qualsiasi valore salvato all'interno delle "Airflow Connections" o delle "Airflow Variables" il cui nome contenga parole sensibili (es. `password`, `secret`, `api_key`, `token`) viene intercettato *prima* della scrittura del file di log. Se uno sviluppatore scrive maldestramente `print(my_db_password)`, nei log e nella UI apparirà unicamente la stringa oscurata `***`.
2.  **Masking Esteso (PII Regex)**: È possibile estendere questo livello di sicurezza configurando Airflow per oscurare pattern specifici. Ad esempio, definendo tramite Variabili o filtri di Python Logging delle espressioni regolari ("Regex") che riconoscono i Codici Fiscali, IBAN o indirizzi email. In questo modo, se un file CSV malformato genera un'eccezione che "sputa" la riga di errore, il log registrerà automaticamente `Cliente: *** errore di parsing` invece del dato sensibile in chiaro.
