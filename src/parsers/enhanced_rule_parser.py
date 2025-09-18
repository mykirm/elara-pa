from typing import List, Tuple
try:
    from src.models import Rule, AuthRequirement, RuleType
    from src.preprocessing.intelligent_chunker import BasicIntelligentChunker, ProcessedChunk
    from src.parsers.payer_rules.uhc_rules import parse_markdown_to_rules
except ImportError:
    from models import Rule, AuthRequirement, RuleType
    from preprocessing.intelligent_chunker import BasicIntelligentChunker, ProcessedChunk
    from parsers.payer_rules.uhc_rules import parse_markdown_to_rules

class EnhancedRuleParser:
    """Rule parser that uses intelligent preprocessing"""
    
    def __init__(self):
        self.chunker = BasicIntelligentChunker()
    
    def parse_with_preprocessing(self, markdown_text: str, source_file: str) -> Tuple[List[Rule], List[ProcessedChunk]]:
        """Parse rules using intelligent preprocessing"""
        
        # 1. Intelligent preprocessing
        processed_chunks = self.chunker.preprocess_markdown(markdown_text, source_file)
        
        # 2. Extract rules from chunks
        all_rules = []
        
        # Get all chunks that can generate rules
        rule_generating_chunks = [c for c in processed_chunks if c.content_type in 
                                 ['authorization_rule', 'procedure_list']]
        
        # Geographic exceptions are handled separately (they modify existing rules)
        exception_chunks = [c for c in processed_chunks if c.content_type == 'geographic_exception']
        
        print(f"Processing {len(rule_generating_chunks)} rule-generating chunks "
              f"({len([c for c in rule_generating_chunks if c.content_type == 'authorization_rule'])} authorization, "
              f"{len([c for c in rule_generating_chunks if c.content_type == 'procedure_list'])} procedure_list) "
              f"and {len(exception_chunks)} exception chunks")
        
        # Extract rules from all rule-generating chunks
        for chunk in rule_generating_chunks:
            chunk_rules = self._extract_from_chunk(chunk, source_file)
            all_rules.extend(chunk_rules)
            
            # Log what we found
            if chunk_rules:
                cpt_codes = []
                for rule in chunk_rules:
                    if rule.cpt_codes:
                        cpt_codes.extend(rule.cpt_codes)
                print(f"  Chunk {chunk.chunk_id[:8]} ({chunk.content_type}): {len(chunk_rules)} rules, CPT codes: {cpt_codes}")
        
        # Apply geographic exceptions
        self._apply_geographic_exceptions(all_rules, exception_chunks)
        
        return all_rules, processed_chunks
    
    def _extract_from_chunk(self, chunk: ProcessedChunk, source_file: str) -> List[Rule]:
        """Extract rules from a single chunk"""
        try:
            # Try existing parser on the chunk content
            chunk_rules = parse_markdown_to_rules(chunk.primary_content, source_file)
            
            # Enhance rules with chunk hints
            for rule in chunk_rules:
                self._apply_chunk_hints(rule, chunk)
            
            return chunk_rules
            
        except Exception as e:
            print(f"Existing parser failed on chunk {chunk.chunk_id}: {e}")
            
            # Fallback: create rule from extraction hints
            return self._create_rule_from_hints(chunk, source_file)
    
    def _apply_chunk_hints(self, rule: Rule, chunk: ProcessedChunk):
        """Enhance rule with preprocessing hints"""
        hints = chunk.extraction_hints
        
        # Merge CPT codes
        if 'cpt_codes' in hints and hints['cpt_codes']:
            existing_codes = set(rule.cpt_codes) if rule.cpt_codes else set()
            hint_codes = set(hints['cpt_codes'])
            rule.cpt_codes = list(existing_codes | hint_codes)
        
        # Apply auth requirement if missing
        if 'auth_requirement' in hints and not rule.auth_requirement:
            if hints['auth_requirement'] == 'REQUIRED':
                rule.auth_requirement = AuthRequirement.REQUIRED
            elif hints['auth_requirement'] == 'NOT_REQUIRED':
                rule.auth_requirement = AuthRequirement.NOT_REQUIRED
        
        # Enhance description with section context (optional field)
        section_path = " > ".join(chunk.section_hierarchy)
        if hasattr(rule, 'description'):
            if rule.description:
                rule.description = f"[{section_path}] {rule.description}"
            else:
                rule.description = f"Rule from: {section_path}"
        
        # Add confidence score
        rule.confidence_score = chunk.confidence_score
    
    def _create_rule_from_hints(self, chunk: ProcessedChunk, source_file: str) -> List[Rule]:
        """Create rule when parser fails but hints are available"""
        hints = chunk.extraction_hints
        
        if 'cpt_codes' not in hints or not hints['cpt_codes']:
            print(f"No CPT codes in hints for chunk {chunk.chunk_id}")
            return []
        
        # Create minimal rule from hints
        rule = Rule(
            rule_id=f"hint_rule_{chunk.chunk_id[:12]}",
            rule_type=RuleType.CPT_BASED,
            auth_requirement=AuthRequirement.REQUIRED if hints.get('auth_requirement') == 'REQUIRED' else AuthRequirement.NOT_REQUIRED,
            payer="UnitedHealthcare",
            cpt_codes=hints['cpt_codes'],
            source_file=source_file
        )
        
        # Add confidence (reduced for hint-based rules)
        rule.confidence_score = chunk.confidence_score * 0.6
        
        print(f"Created hint-based rule: {rule.rule_id} with CPT codes {rule.cpt_codes}")
        return [rule]
    
    def _apply_geographic_exceptions(self, rules: List[Rule], exception_chunks: List[ProcessedChunk]):
        """Apply geographic exceptions from chunks"""
        for exception_chunk in exception_chunks:
            hints = exception_chunk.extraction_hints
            
            if 'states' in hints and hints['states']:
                states = hints['states']
                
                # Apply to all rules or specific ones
                related_cpt_codes = hints.get('cpt_codes', [])
                
                for rule in rules:
                    # Apply exception if CPT codes overlap or no specific codes mentioned
                    if (not related_cpt_codes or 
                        any(cpt in rule.cpt_codes for cpt in related_cpt_codes)):
                        
                        if not hasattr(rule, 'excluded_states'):
                            rule.excluded_states = []
                        rule.excluded_states.extend(states)
                        rule.excluded_states = list(set(rule.excluded_states))  # Remove duplicates
                
                print(f"Applied geographic exceptions {states} to {len([r for r in rules if hasattr(r, 'excluded_states') and any(s in r.excluded_states for s in states)])} rules")