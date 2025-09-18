# PA Hypergraph System

A Python/Neo4j system for parsing prior-authorization (PA) policies from insurance providers and modeling them as a hypergraph for efficient querying and analysis.

## 🎯 Purpose

This system extracts structured authorization rules from insurance PDFs and models them as hypergraphs where:
- **Nodes**: CPT codes, ICD codes, states, payers, services
- **Hyperedges**: Authorization requirements connecting multiple nodes

## 📁 Project Structure

```
pa-hypergraph-system/
├── src/                        # Core source code
│   ├── __init__.py
│   ├── models.py              # Pydantic models for PA entities
│   ├── app/                   # FastAPI web application
│   │   └── main.py            # API endpoints for rule processing
│   ├── parsers/               # PDF parsing modules
│   │   ├── __init__.py
│   │   ├── pdf_extractor.py   # PDF → Markdown conversion
│   │   └── payer_rules/       # Payer-specific rule parsers
│   │       ├── __init__.py
│   │       └── uhc_rules.py   # UHC rule extraction (PRODUCTION)
│   ├── preprocessing/         # Document preprocessing
│   │   └── intelligent_chunker.py # Content classification
│   ├── hypergraphs/           # Hypergraph operations
│   │   └── __init__.py
│   └── connectors/            # Database connectors (future)
├── scripts/                    # Executable scripts
│   ├── process_pa_document.py # Main processing pipeline
│   └── run_server.py          # FastAPI server launcher
├── tests/                      # Test suites and comparisons
│   ├── integration/           # End-to-end tests
│   ├── test_*.py              # Parser comparison tests
│   └── *.md                   # Test results and documentation
├── data/                       # Data directory
│   ├── raw/                   # Raw extracted content
│   ├── processed/             # Processed rules and summaries
│   └── uploads/               # API file uploads
├── third_party/               # External dependencies
│   └── HyperGraphRAG/         # Cloned hypergraph library
├── marker_env/                # Virtual environment for marker-pdf
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Neo4j 5.0+ (for hypergraph storage)
- 2.5GB disk space (for marker models)

### Installation

1. **Clone the repository**:
```bash
git clone <repo-url>
cd pa-hypergraph-system
```

2. **Set up marker environment**:
```bash
python3.11 -m venv marker_env
source marker_env/bin/activate
pip install marker-pdf pdfplumber
```

3. **Install core dependencies**:
```bash
pip install -r requirements.txt
```

### Basic Usage

**Process a PA document (Command Line)**:
```bash
python scripts/process_pa_document.py data/UHC-Commercial-PA-Requirements-2025.pdf
```

**Start the API server**:
```bash
python scripts/run_server.py
# Server runs on http://localhost:8000
# API docs at http://localhost:8000/docs
```

**API Usage Examples**:
```bash
# Upload and process a PDF
curl -X POST "http://localhost:8000/upload-pdf" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@path/to/document.pdf"

# Evaluate authorization for CPT codes
curl -X POST "http://localhost:8000/authorization/evaluate" \
  -H "Content-Type: application/json" \
  -d '{"cpt_codes": ["23470", "29826"], "state": "CA", "patient_age": 65}'

# Get all loaded rules
curl "http://localhost:8000/rules"
```

## 🔧 Key Components

### 1. Models (`src/models.py`)

Pydantic models with validation for:
- `Rule`: Core authorization rule entity
- `CPTCode`: Validated CPT/HCPCS codes
- `ICDCode`: ICD-10 diagnosis codes
- `AuthRequirement`: REQUIRED, CONDITIONAL, NOT_REQUIRED, NOTIFICATION_ONLY

### 2. Parsers (`src/parsers/`)

**Marker Integration** (Recommended):
- High-quality PDF → Markdown conversion
- Preserves table structure (critical for PA docs)
- 6.6x more content extraction than alternatives

**PDFPlumber Fallback**:
- Simple text extraction
- Table detection
- Used when marker fails

### 3. Rule Extraction (`src/parsers/payer_rules/uhc_rules.py`)

**Production Parser**: Uses deterministic regex-based extraction proven to outperform AI preprocessing by 55x:

- **CPT codes**: `\d{5}` (5-digit procedure codes)
- **HCPCS codes**: `[A-V]\d{4}` (letter + 4 digits)
- **ICD-10 codes**: `[A-Z]\d{2}(\.\d{1,4})?` (diagnosis codes)
- **Authorization language**: "Prior authorization required" → REQUIRED
- **Geographic exceptions**: State abbreviation detection
- **Medical categories**: Preserves procedure specialties (Arthroplasty, Arthroscopy, etc.)

**Why Original Parser**: Comprehensive testing showed intelligent preprocessing lost 99%+ of content, missing critical authorization rules while the original parser successfully extracted all major medical procedures.

## 📊 Comparison: Marker vs PDFPlumber

| Metric | Marker | PDFPlumber |
|--------|--------|------------|
| Text Extracted | 62,398 chars | 9,385 chars |
| Table Rows | 173 | 0 |
| Structure | Rich Markdown | Plain text |
| Setup | 2.1GB models | Lightweight |
| Quality | Production-ready | Basic extraction |

**Recommendation**: Use marker for production. It's essential for cross-payer scalability.

## 📊 Parser Performance Comparison

Based on UHC 2025 PA Requirements testing:

| Metric | Original Parser | Enhanced Parser | Winner |
|--------|----------------|-----------------|---------|
| **Rules Extracted** | **166** | 3 | 🏆 **ORIGINAL** (55x more) |
| **Unique CPT Codes** | **1,984** | 15 | 🏆 **ORIGINAL** (132x more) |
| **REQUIRED Rules** | **22** | 0 | 🏆 **ORIGINAL** |
| **Categories Detected** | **57** | 0 | 🏆 **ORIGINAL** |
| **Major Procedures Found** | ✅ Arthroplasty, Arthroscopy | ❌ Missed all | 🏆 **ORIGINAL** |

**Key Findings**:
- Original parser correctly identifies "Prior authorization required" as REQUIRED
- Enhanced parser with AI chunking missed 99.2% of CPT codes
- Original parser preserves medical specialty context and geographic exceptions

## 🧪 Testing

Run extraction test:
```bash
python tests/integration/test_extraction_only.py
```

Compare parser outputs:
```bash
python tests/integration/test_rule_parsing_5page_comparison.py
```

## 📈 Hypergraph Model

Rules are modeled as hyperedges connecting multiple node types:

```
Hyperedge: "Arthroscopy Auth Rule"
  ├── CPT: [29826, 29843, 29871]
  ├── Payer: UnitedHealthcare
  ├── Requirement: REQUIRED
  ├── States: [excluded: TX, FL]
  └── Category: Orthopedic
```

## 🔮 Future Enhancements

- [ ] Neo4j integration for hypergraph storage
- [ ] LLM integration for complex narrative parsing
- [ ] Support for Anthem, Aetna, Cigna PDFs
- [ ] REST API for rule queries
- [ ] Automated PDF monitoring and updates

## 📝 License

[Your License Here]

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## 📧 Contact


