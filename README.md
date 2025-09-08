# Prior Authorization Hypergraph System

A Python/Neo4j system for parsing prior-authorization policies from insurers and modeling them as hypergraphs to enable intelligent querying and analysis.

## 🏗️ Architecture

This system uses a modular architecture to transform unstructured insurance documents into queryable knowledge graphs:

```
pa-hypergraph-system/
├── ingestion/       # PDF parsing and normalization
├── models/          # Pydantic data models for rules and entities
├── hypergraphs/     # Graph construction and Neo4j integration
├── api/             # FastAPI endpoints for CRUD operations
├── tests/           # Unit and integration tests
└── third_party/     # External dependencies (HyperGraphRAG)
```

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Neo4j Database
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/mykirm/elara-pa.git
   cd elara-pa
   ```

2. **Set up virtual environment**
   ```bash
   python3.11 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up Neo4j**
   - Install Neo4j Desktop or use Neo4j Aura
   - Create a new database
   - Note connection details for configuration

## 📦 Core Dependencies

- **marker-pdf** - High-fidelity PDF extraction and processing
- **neo4j** - Official Neo4j Python driver for graph database operations
- **pydantic** - Data validation and schema definition
- **fastapi** - Modern API framework for building endpoints
- **uvicorn** - ASGI server for running the API
- **pdfplumber** - Alternative PDF processing for tables and structured data

## 🧩 Components

### Ingestion Pipeline
Processes insurance PDF documents using deterministic parsing with LLM fallback:
- Text extraction and normalization
- Table detection and processing
- Rule identification and structuring

### Data Models
Pydantic schemas for representing:
- Prior authorization rules
- Medical conditions and procedures
- Coverage criteria and requirements
- Entity relationships

### Hypergraph Construction
Transforms parsed rules into Neo4j graph structures:
- Multi-dimensional relationships between entities
- Complex rule dependencies and conditions
- Hierarchical policy structures

### API Layer
RESTful endpoints for:
- Document upload and processing
- Rule querying and retrieval
- Graph visualization data
- System health and metrics

## 🔧 Development

### Running Tests
```bash
pytest tests/
```

### Starting the API Server
```bash
uvicorn api.main:app --reload
```

### Code Style
This project follows Python best practices:
- Type hints throughout
- Pydantic models for data validation
- Comprehensive error handling
- Inline documentation

## 🎯 Goals

1. **Deterministic Parsing** - Use regex and structured extraction where possible
2. **LLM Integration** - Leverage language models only for complex, ambiguous content
3. **Graph Relationships** - Model complex rule dependencies as hypergraph structures
4. **Query Interface** - Provide intuitive APIs for rule discovery and analysis
5. **Extensibility** - Support multiple insurance providers and policy formats

## 📈 Roadmap

- [ ] Core data models implementation
- [ ] PDF ingestion pipeline
- [ ] Neo4j graph construction
- [ ] HyperGraphRAG integration
- [ ] RESTful API endpoints
- [ ] Web interface for visualization
- [ ] Multi-provider support

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Submit a pull request

## 📄 License

This project is part of a research initiative for improving healthcare prior authorization processes.

---

*Built with Python 3.11, Neo4j, and modern ML/NLP tools*
