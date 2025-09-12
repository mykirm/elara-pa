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
│   ├── parsers/               # PDF parsing modules
│   │   ├── __init__.py
│   │   ├── uhc_parser.py      # UHC-specific PDF extraction
│   │   └── uhc_parser_rules.py # Rule parsing logic
│   ├── hypergraphs/           # Hypergraph operations
│   │   └── __init__.py
│   └── connectors/            # Database connectors (future)
├── scripts/                    # Executable scripts
│   └── process_pa_document.py # Main processing pipeline
├── tests/                      # Test suites
│   ├── integration/           # End-to-end tests
│   │   ├── test_extraction_only.py
│   │   ├── test_marker_5_pages.py
│   │   └── test_rule_parsing_*.py
│   └── unit/                  # Unit tests (future)
├── data/                       # Data directory
│   ├── raw/                   # Raw extracted content
│   └── processed/             # Processed rules and summaries
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

Process a PA document:
```bash
python scripts/process_pa_document.py data/UHC-Commercial-PA-Requirements-2025.pdf
```

Use pdfplumber instead of marker:
```bash
python scripts/process_pa_document.py data/document.pdf --use-pdfplumber
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

### 3. Rule Extraction

Deterministic parsing using regex for:
- CPT codes: `\d{5}`
- HCPCS codes: `[A-V]\d{4}`
- ICD-10 codes: `[A-Z]\d{2}(\.\d{1,4})?`
- State codes: `AL|AK|AZ|...`

Complex narratives marked for LLM processing.

## 📊 Comparison: Marker vs PDFPlumber

| Metric | Marker | PDFPlumber |
|--------|--------|------------|
| Text Extracted | 62,398 chars | 9,385 chars |
| Table Rows | 173 | 0 |
| Structure | Rich Markdown | Plain text |
| Setup | 2.1GB models | Lightweight |
| Quality | Production-ready | Basic extraction |

**Recommendation**: Use marker for production. It's essential for cross-payer scalability.

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

