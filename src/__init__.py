"""PA Hypergraph System - Core Module."""

from .models import (
    Rule, RuleType, AuthRequirement,
    CPTCode, ICDCode, State,
    Payer, Category, Service
)

from .parsers import (
    convert_pdf_to_markdown,
    extract_tables_with_pdfplumber,
    parse_markdown_to_rules
)

__version__ = "0.1.0"

__all__ = [
    # Models
    'Rule', 'RuleType', 'AuthRequirement',
    'CPTCode', 'ICDCode', 'State',
    'Payer', 'Category', 'Service',
    # Parser functions
    'convert_pdf_to_markdown',
    'extract_tables_with_pdfplumber',
    'parse_markdown_to_rules'
]