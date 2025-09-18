"""Basic Intelligent Chunker for testing classification and extraction"""

from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from pathlib import Path
import re
import uuid


@dataclass
class ProcessedChunk:
    """Intelligent chunk with enhanced metadata for rule extraction"""
    chunk_id: str
    content_type: str  # 'authorization_rule', 'geographic_exception', 'procedure_list', 'context_info'
    section_hierarchy: List[str]  # ['Orthopedic', 'Arthroscopic Procedures']
    primary_content: str  # Cleaned, structured content
    supporting_context: str  # Related context from nearby sections
    extraction_hints: Dict  # Hints for the rule parser
    raw_content: str  # Original content
    confidence_score: float  # How confident we are in the classification
    
    def to_dict(self) -> Dict:
        return {
            'chunk_id': self.chunk_id,
            'content_type': self.content_type,
            'section_hierarchy': self.section_hierarchy,
            'primary_content': self.primary_content,
            'supporting_context': self.supporting_context,
            'extraction_hints': self.extraction_hints,
            'confidence_score': self.confidence_score,
            'content_length': len(self.primary_content)
        }


class BasicIntelligentChunker:
    """Basic version for testing preprocessing concepts"""
    
    def __init__(self):
        # Pattern matchers for different content types
        self.auth_patterns = [
            r'prior authorization.*required',
            r'requires.*prior auth',
            r'auth.*required',
            r'must obtain.*authorization',
            r'authorization.*necessary',
            r'PA required',
            r'prior auth.*needed'
        ]
        
        self.exception_patterns = [
            r'exception',
            r'excluded.*from',
            r'does not apply',
            r'not required.*for',
            r'exempt.*from',
            r'excluding',
            r'except for'
        ]
        
        self.cpt_patterns = [
            r'cpt.*code',
            r'procedure.*code', 
            r'hcpcs',
            r'\b\d{5}\b',  # Individual CPT codes
            r'\b\d{5}[-]\d{5}\b',  # CPT code ranges
            r'\b\d{5}(?:,\s*\d{5})+\b'  # CPT code lists
        ]
        
        self.geographic_patterns = [
            r'state',
            r'geographic',
            r'region',
            r'location',
            r'\b(AL|AK|AZ|AR|CA|CO|CT|DE|FL|GA|HI|ID|IL|IN|IA|KS|KY|LA|ME|MD|MA|MI|MN|MS|MO|MT|NE|NV|NH|NJ|NM|NY|NC|ND|OH|OK|OR|PA|RI|SC|SD|TN|TX|UT|VT|VA|WA|WV|WI|WY|DC|PR|VI|GU|AS|MP)\b'
        ]
        
        self.not_required_patterns = [
            r'not required',
            r'no.*authorization',
            r'exempt',
            r'excluded',
            r'does not apply'
        ]
    
    def preprocess_markdown(self, markdown_text: str, source_file: str) -> List[ProcessedChunk]:
        """Convert raw markdown into intelligent chunks for better rule extraction"""
        
        # 1. Parse document into sections
        sections = self._parse_into_sections(markdown_text)
        
        # 2. Process each section into chunks
        processed_chunks = []
        for section in sections:
            chunks = self._process_section(section, source_file)
            processed_chunks.extend(chunks)
        
        # 3. Add cross-references and context
        self._add_contextual_relationships(processed_chunks)
        
        return processed_chunks
    
    def _parse_into_sections(self, markdown_text: str) -> List[Dict]:
        """Parse markdown into sections based on headers and content breaks"""
        lines = markdown_text.split('\n')
        sections = []
        current_section = None
        section_stack = []
        
        for line_num, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
                
            # Detect headers (markdown ## or bold text)
            header_match = re.match(r'^(#{1,6})\s*(.+)', line)
            if header_match:
                level = len(header_match.group(1))
                title = header_match.group(2).strip()
                
                # Save previous section
                if current_section and current_section['content'].strip():
                    sections.append(current_section)
                
                # Update hierarchy
                section_stack = section_stack[:level-1]
                section_stack.append(title)
                
                # Start new section
                current_section = {
                    'title': title,
                    'level': level,
                    'hierarchy': section_stack.copy(),
                    'content': '',
                    'start_line': line_num
                }
                
            elif current_section:
                current_section['content'] += line + '\n'
            else:
                # Content without header - create default section
                current_section = {
                    'title': 'Document Content',
                    'level': 1,
                    'hierarchy': ['Document Content'],
                    'content': line + '\n',
                    'start_line': line_num
                }
        
        # Add final section
        if current_section and current_section['content'].strip():
            sections.append(current_section)
        
        return sections
    
    def _process_section(self, section: Dict, source_file: str) -> List[ProcessedChunk]:
        """Process a section into classified chunks"""
        content = section['content']
        hierarchy = section['hierarchy']
        
        # Classify content type
        content_type, confidence = self._classify_content(content)
        
        # Extract hints based on classification
        extraction_hints = self._extract_hints(content, content_type)
        
        # Create chunk
        chunk_id = f"{Path(source_file).stem}_{hash(''.join(hierarchy))}_{uuid.uuid4().hex[:8]}"
        
        chunk = ProcessedChunk(
            chunk_id=chunk_id,
            content_type=content_type,
            section_hierarchy=hierarchy,
            primary_content=self._clean_content(content),
            supporting_context="",  # Will be added later
            extraction_hints=extraction_hints,
            raw_content=content,
            confidence_score=confidence
        )
        
        return [chunk]
    
    def _classify_content(self, content: str) -> Tuple[str, float]:
        """Classify content type with confidence score"""
        content_lower = content.lower()
        
        # Count pattern matches
        auth_matches = sum(1 for pattern in self.auth_patterns if re.search(pattern, content_lower, re.IGNORECASE))
        exception_matches = sum(1 for pattern in self.exception_patterns if re.search(pattern, content_lower, re.IGNORECASE))
        cpt_matches = sum(1 for pattern in self.cpt_patterns if re.search(pattern, content_lower, re.IGNORECASE))
        geo_matches = sum(1 for pattern in self.geographic_patterns if re.search(pattern, content_lower, re.IGNORECASE))
        
        # Calculate scores
        scores = {
            'authorization_rule': auth_matches * 2 + cpt_matches,  # Auth language + CPT codes
            'geographic_exception': exception_matches * 2 + geo_matches,  # Exceptions + geography
            'procedure_list': cpt_matches * 2,  # Heavy CPT code presence
            'context_info': 1  # Default fallback
        }
        
        # Find highest scoring type
        best_type = max(scores.keys(), key=lambda k: scores[k])
        max_score = scores[best_type]
        
        # Calculate confidence
        total_matches = sum(scores.values())
        if total_matches > 1:
            confidence = min(max_score / total_matches, 0.95)
        else:
            confidence = 0.5  # Default confidence
        
        # Boost confidence for clear indicators
        if max_score >= 3:
            confidence = min(confidence + 0.2, 0.95)
        
        return best_type, confidence
    
    def _extract_hints(self, content: str, content_type: str) -> Dict:
        """Extract parsing hints based on content type"""
        hints = {'content_type': content_type}
        
        # Extract CPT codes and HCPCS codes
        cpt_codes = re.findall(r'\b\d{5}\b', content)  # 5-digit CPT codes
        hcpcs_codes = re.findall(r'\b[A-V]\d{4}\b', content)  # HCPCS codes (letter + 4 digits)
        all_codes = cpt_codes + hcpcs_codes
        if all_codes:
            hints['cpt_codes'] = list(set(all_codes))
        
        # Extract state codes
        states = re.findall(r'\b(AL|AK|AZ|AR|CA|CO|CT|DE|FL|GA|HI|ID|IL|IN|IA|KS|KY|LA|ME|MD|MA|MI|MN|MS|MO|MT|NE|NV|NH|NJ|NM|NY|NC|ND|OH|OK|OR|PA|RI|SC|SD|TN|TX|UT|VT|VA|WA|WV|WI|WY|DC|PR|VI|GU|AS|MP)\b', content)
        if states:
            hints['states'] = list(set(states))
        
        # Determine auth requirement
        content_lower = content.lower()
        
        # Check for "not required" patterns first (more specific)
        not_required_found = any(re.search(pattern, content_lower) for pattern in self.not_required_patterns)
        if not_required_found:
            hints['auth_requirement'] = 'NOT_REQUIRED'
        # Then check for "required" patterns
        elif any(re.search(pattern, content_lower) for pattern in self.auth_patterns):
            hints['auth_requirement'] = 'REQUIRED'
        
        # Special handling based on content type
        if content_type == 'geographic_exception':
            # Assume exceptions mean NOT_REQUIRED unless explicitly stated
            if 'auth_requirement' not in hints:
                hints['auth_requirement'] = 'NOT_REQUIRED'
            hints['exception_type'] = 'EXCLUSION'
        
        return hints
    
    def _clean_content(self, content: str) -> str:
        """Clean and structure content for better parsing"""
        # Remove excessive whitespace
        cleaned = re.sub(r'\n\s*\n\s*\n+', '\n\n', content)
        
        # Normalize bullet points
        cleaned = re.sub(r'^\s*[-*+"]\s*', '" ', cleaned, flags=re.MULTILINE)
        
        # Clean up table separators
        cleaned = re.sub(r'^\s*\|[-:]+\|[-:]+\|\s*$', '', cleaned, flags=re.MULTILINE)
        
        return cleaned.strip()
    
    def _add_contextual_relationships(self, chunks: List[ProcessedChunk]):
        """Add supporting context to chunks from related sections"""
        for chunk in chunks:
            context_parts = []
            
            # Find related chunks (same hierarchy level or parent)
            for other_chunk in chunks:
                if other_chunk.chunk_id != chunk.chunk_id:
                    # Check hierarchy overlap
                    overlap = len(set(chunk.section_hierarchy) & set(other_chunk.section_hierarchy))
                    if overlap > 0:
                        if other_chunk.content_type == 'geographic_exception' and chunk.content_type == 'authorization_rule':
                            context_parts.append(f"Geographic context: {other_chunk.primary_content[:100]}...")
                        elif other_chunk.content_type == 'context_info':
                            context_parts.append(other_chunk.primary_content[:150])
            
            # Set context (limit length)
            chunk.supporting_context = " | ".join(context_parts[:2])
    
    def get_classification_stats(self, chunks: List[ProcessedChunk]) -> Dict:
        """Get statistics about classification results"""
        content_types = {}
        confidence_scores = []
        extraction_hints_stats = {}
        
        for chunk in chunks:
            # Count content types
            content_types[chunk.content_type] = content_types.get(chunk.content_type, 0) + 1
            
            # Track confidence
            confidence_scores.append(chunk.confidence_score)
            
            # Count extraction hints
            for hint_key in chunk.extraction_hints.keys():
                extraction_hints_stats[hint_key] = extraction_hints_stats.get(hint_key, 0) + 1
        
        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
        
        return {
            'total_chunks': len(chunks),
            'content_types': content_types,
            'average_confidence': avg_confidence,
            'extraction_hints_found': extraction_hints_stats,
            'high_confidence_chunks': len([c for c in chunks if c.confidence_score > 0.8])
        }