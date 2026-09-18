# 🌍 DARUKAA.EARTH — Scientific Environmental Intelligence Engine

**DARUKAA.EARTH** is an open-source, AI-powered environmental intelligence platform designed to model complex ecological interactions, soil mechanics, and land restoration pathways. Combining a FastAPI backend, Streamlit dark-mode UI, ChromaDB RAG architecture, and local `gemma:2b` LLM inference via Ollama, it provides land managers and scientific researchers with evidence-grounded ecological assessments and real-time intervention simulators.

---

## 🌟 Key Features

* **Bi-Directional NLP Parameter Extraction**: Automatically parses soil metrics (SOC %, pH, texture), land-use types, and coordinates from natural language input.
* **Automated Geocoding**: Resolves locations using Nominatim and estimates regional climate baselines.
* **Evidence-Grounded RAG Pipeline**: Queries vector-embedded ecological literature via ChromaDB to provide cited, hallucination-free intervention strategies.
* **Interactive "What-If" Simulator**: Real-time modeling of management interventions (Biochar, Cover Crops, Tillage Reduction) and their projected 1-year and 3-year impact on soil organic carbon and infiltration.
* **Comparative Data Visualizations**: Dynamic Plotly 5-axis recovery radar charts and temporal recovery path line graphs.
* **Vector Source Citation Auditor**: Complete transparency into retrieved research documents, page numbers, chunk IDs, and vector similarity scores.
* **Containerized Architecture**: Fully dockerized stack orchestrated via Docker Compose for multi-platform local deployment.

---

## 🛠️ Tech Stack

| Layer | Component / Framework |
| :--- | :--- |
| **Frontend UI** | Streamlit (1.41+), Plotly, Custom CSS |
| **API Backend** | FastAPI, Uvicorn, Pydantic v2 |
| **LLM Engine** | Ollama (`gemma:2b`) |
| **Vector Store & RAG** | ChromaDB, Sentence-Transformers (`all-MiniLM-L6-v2`) |
| **Database & Memory** | SQLite / SQLAlchemy |
| **NLP & Geocoding** | Rule-based Regex Engine, Geopy (Nominatim) |
| **Containerization** | Docker, Docker Compose |

---

## 📁 Repository Structure

```text
darukaa-earth/
├── app/
│   ├── api/                 # FastAPI endpoints & route handlers
│   ├── clarification/       # Missing information detector
│   ├── extraction/          # Regex extractor, intent classifier & geocoder
│   ├── interventions/       # Ecological intervention evaluation engine
│   ├── llm/                 # Ollama/Local LLM provider integration
│   ├── memory/              # Conversation session & profile memory manager
│   ├── reasoning/           # Multi-metric environmental reasoning engine
│   ├── retrieval/           # ChromaDB vector store & document chunker
│   ├── schemas/             # Pydantic data models & state definitions
│   ├── config.py            # App settings & environment configurations
│   ├── frontend.py          # Streamlit chat interface & Plotly dashboard
│   └── main.py              # FastAPI app initialization & middleware
├── data/                    # ChromaDB persistent storage & raw PDFs
├── Docker/
│   ├── Dockerfile.backend   # FastAPI service container spec
│   └── Dockerfile.frontend  # Streamlit UI service container spec
├── .dockerignore            # Excluded build context rules
├── .gitignore               # Git untracked pattern rules
├── docker-compose.yml       # Stack orchestration file
├── requirements.txt         # Python dependencies
└── README.md

 Quickstart Guide (Docker Deployment)The recommended way to run DARUKAA.EARTH is via Docker Compose.PrerequisitesDocker Desktop installed and running.At least 8 GB of system RAM.1. Clone the RepositoryBashgit clone [https://github.com/gowdarahul642/darukaa-earth.git](https://github.com/gowdarahul642/darukaa-earth.git)
cd darukaa-earth
2. Build and Launch StackBashdocker compose up -d --build
3. Download Model Weights & WarmupRun these commands to pull and load the gemma:2b model inside the container:Bashdocker compose exec ollama ollama pull gemma:2b
docker compose exec ollama ollama run gemma:2b "warmup"
4. Access ServicesStreamlit Interface: http://localhost:8501FastAPI Swagger Docs: http://localhost:8000/docsOllama Endpoint: http://localhost:11434💻 Manual Local Development SetupIf running services outside Docker on your host machine:1. Environment SetupDOSpython -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
2. Start Local Ollama ServerEnsure Ollama is installed locally:DOSset OLLAMA_KEEP_ALIVE=-1
ollama serve
ollama pull gemma:2b
3. Launch ServicesBackend Terminal:DOSpython -m uvicorn app.main:app --reload --port 8000
Frontend Terminal:DOSstreamlit run app/frontend.py
📝 Example Assessment QuerySubmit this prompt in the interface to run a complete land assessment pipeline:"My farm near Pune, India has 0.4% soil organic carbon, a pH of 6.5, and grows continuous wheat under low rainfall."System Pipeline Execution:Extraction: Geocodes Pune ($18.52^\circ\text{N}, 73.85^\circ\text{E}$), extracts SOC = 0.4%, pH = 6.5, Monoculture Wheat, and Low Rainfall.RAG Vector Search: Queries ChromaDB for peer-reviewed soil restoration literature.Synthesis: Returns an evidence-grounded assessment report detailing mechanisms and interventions.Visual Analytics: Renders the "What-If" slider simulator, 5-axis ecological recovery radar, and temporal path charts.📜 LicenseDistributed under the MIT License.
