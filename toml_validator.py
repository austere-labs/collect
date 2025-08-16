"""
TOML validation and automatic fixing utility for slashsync tool.
"""

import re
from typing import Tuple, List

try:
    import tomllib
except ImportError:
    import tomli as tomllib

try:
    import tomli_w
except ImportError:
    tomli_w = None


class TomlValidator:
    """TOML validation and automatic fixing utility"""

    def __init__(self):
        if tomli_w is None:
            print("Warning: tomli-w not available, TOML writing functionality limited")
            # Note: We mainly use tomllib for validation, so this is not critical

    def validate_toml(self, content: str) -> Tuple[bool, List[str]]:
        """
        Validate TOML content and return success status with error messages.

        Args:
            content: Raw TOML content string

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []

        if not content.strip():
            errors.append("Empty TOML content")
            return False, errors

        try:
            tomllib.loads(content)
            return True, []
        except tomllib.TOMLDecodeError as e:
            errors.append(f"TOML parsing error: {e}")
            return False, errors
        except Exception as e:
            errors.append(f"Unexpected error parsing TOML: {e}")
            return False, errors

    def clean_gemini_artifacts(self, content: str) -> str:
        """
        Remove common artifacts from Gemini AI output that break TOML parsing.

        Args:
            content: Raw content from Gemini conversion

        Returns:
            Cleaned content with artifacts removed
        """
        lines = content.split("\n")
        cleaned_lines = []
        in_toml_block = False

        for line in lines:
            line_strip = line.strip()

            # Skip common Gemini artifacts
            if line_strip in ["Loaded cached credentials.", ""]:
                continue

            # Handle markdown code fences
            if line_strip == "```toml":
                in_toml_block = True
                continue
            elif line_strip == "```" and in_toml_block:
                in_toml_block = False
                continue
            elif line_strip.startswith("```"):
                # Skip other code blocks
                continue

            # Skip status/error messages that aren't TOML
            if line_strip.startswith(
                "I need the actual file path"
            ) or line_strip.startswith("Please provide the path"):
                continue

            cleaned_lines.append(line)

        return "\n".join(cleaned_lines).strip()

    def extract_toml_from_markdown(self, content: str) -> str:
        """
        Extract TOML content from markdown blocks if present.

        Args:
            content: Content that might contain TOML in markdown blocks

        Returns:
            Extracted TOML content
        """
        # Look for ```toml blocks
        toml_block_pattern = r"```toml\s*\n(.*?)\n```"
        matches = re.findall(toml_block_pattern, content, re.DOTALL)

        if matches:
            return matches[0].strip()

        # Look for ``` blocks that might contain TOML
        code_block_pattern = r"```\s*\n(.*?)\n```"
        matches = re.findall(code_block_pattern, content, re.DOTALL)

        for match in matches:
            # Test if this block contains valid TOML
            is_valid, _ = self.validate_toml(match.strip())
            if is_valid:
                return match.strip()

        return content

    def fix_common_toml_issues(self, content: str) -> str:
        """
        Attempt to fix common TOML syntax issues.

        Args:
            content: TOML content with potential issues

        Returns:
            Fixed TOML content
        """
        # First, try to fix unclosed multiline strings and arrays
        content = self._fix_unclosed_structures(content)
        
        # Fix malformed array syntax
        content = self._fix_malformed_arrays(content)
        
        # Fix key-value pair issues
        content = self._fix_key_value_pairs(content)
        
        lines = content.split("\n")
        fixed_lines = []

        for line in lines:
            stripped = line.strip()
            if not stripped:
                fixed_lines.append("")
                continue

            # Skip comments
            if stripped.startswith("#"):
                fixed_lines.append(line)
                continue

            # Fix unquoted string values in key-value pairs
            if "=" in stripped and not stripped.startswith("["):
                key, value = stripped.split("=", 1)
                key = key.strip()
                value = value.strip()

                # If value is not quoted and not a number/boolean/array/inline table
                if value and not (
                    value.startswith('"')
                    or value.startswith("'")
                    or value.startswith("[")
                    or value.startswith("{")
                    or value.lower() in ["true", "false"]
                    or value.replace(".", "").replace("-", "").isdigit()
                ):
                    # Quote the value
                    value = f'"{value}"'

                fixed_lines.append(f"{key} = {value}")
            else:
                fixed_lines.append(line)

        return "\n".join(fixed_lines)
    
    def _fix_unclosed_structures(self, content: str) -> str:
        """
        Fix unclosed strings, arrays, and other TOML structures.
        
        Args:
            content: TOML content with potential unclosed structures
            
        Returns:
            Fixed TOML content
        """
        # Fix unclosed triple-quoted strings
        content = self._fix_unclosed_multiline_strings(content)
        
        # Fix unclosed arrays  
        content = self._fix_unclosed_arrays(content)
        
        # Fix malformed string endings
        content = self._fix_malformed_strings(content)
        
        return content
    
    def _fix_unclosed_multiline_strings(self, content: str) -> str:
        """Fix unclosed triple-quoted strings."""
        lines = content.split('\n')
        fixed_lines = []
        in_multiline_string = False
        quote_type = None  # Track whether we're in """ or '''
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            # Check if we're starting a multiline string
            if not in_multiline_string:
                # Look for the start of a multiline string
                if '"""' in line:
                    quote_count = line.count('"""')
                    if quote_count == 1:
                        in_multiline_string = True
                        quote_type = '"""'
                    elif quote_count % 2 == 0:
                        # Even number, complete pairs
                        pass
                    else:
                        # Odd number > 1, likely unclosed
                        in_multiline_string = True
                        quote_type = '"""'
                elif "'''" in line:
                    quote_count = line.count("'''")
                    if quote_count == 1:
                        in_multiline_string = True  
                        quote_type = "'''"
                    elif quote_count % 2 == 0:
                        # Even number, complete pairs
                        pass
                    else:
                        # Odd number > 1, likely unclosed
                        in_multiline_string = True
                        quote_type = "'''"
                fixed_lines.append(line)
            else:
                # We're inside a multiline string, look for closing quotes
                # Check if this line only contains the closing quotes (like isolated """)
                if stripped == quote_type:
                    # This is a standalone closing quote - use it to close and continue parsing
                    in_multiline_string = False
                    quote_type = None
                    fixed_lines.append(line)
                    continue
                elif quote_type in line:
                    # Normal closing quote
                    in_multiline_string = False
                    quote_type = None
                    fixed_lines.append(line)
                else:
                    # Check if this looks like the end of the structure
                    if (stripped.startswith('[') or 
                        stripped.startswith('#') or
                        ('=' in stripped and not stripped.startswith(' ')) or
                        stripped.startswith('name =') or
                        stripped.startswith('description =') or
                        stripped.startswith('title =')):
                        # This looks like a new TOML structure, close the string
                        fixed_lines.append(f'{quote_type}')
                        fixed_lines.append(line)
                        in_multiline_string = False
                        quote_type = None
                    else:
                        fixed_lines.append(line)
        
        # If we reach the end and still in a multiline string, close it
        if in_multiline_string and quote_type:
            fixed_lines.append(quote_type)
            
        return '\n'.join(fixed_lines)
    
    def _fix_unclosed_arrays(self, content: str) -> str:
        """Fix unclosed arrays."""
        lines = content.split('\n')
        fixed_lines = []
        open_brackets = 0
        
        for line in lines:
            stripped = line.strip()
            
            # Count opening and closing brackets (not in strings)
            in_string = False
            escape_next = False
            
            for char in stripped:
                if escape_next:
                    escape_next = False
                    continue
                    
                if char == '\\':
                    escape_next = True
                    continue
                    
                if char in ['"', "'"]:
                    in_string = not in_string
                    continue
                    
                if not in_string:
                    if char == '[':
                        open_brackets += 1
                    elif char == ']':
                        open_brackets -= 1
            
            fixed_lines.append(line)
            
            # If we have unclosed brackets and this looks like end of array context
            if (open_brackets > 0 and 
                (stripped.startswith('[') and '[[' not in stripped) or
                stripped.startswith('#') or 
                (not stripped and len(fixed_lines) > 1)):
                # Add closing brackets
                for _ in range(open_brackets):
                    fixed_lines.append(']')
                open_brackets = 0
        
        # Close any remaining open brackets at end
        for _ in range(open_brackets):
            fixed_lines.append(']')
            
        return '\n'.join(fixed_lines)
    
    def _fix_malformed_strings(self, content: str) -> str:
        """Fix strings that end with unmatched quotes."""
        lines = content.split('\n')
        fixed_lines = []
        
        for line in lines:
            # Look for lines that end with unmatched quotes
            if (line.strip().endswith('",') or 
                line.strip().endswith('"",') or
                line.strip().endswith('`","')):
                # Remove the problematic ending and close properly
                line = line.rstrip().rstrip('",').rstrip('"') + '"'
            
            # Fix lines that have unclosed quotes at the end
            if line.count('"') % 2 == 1 and not line.strip().endswith('"""'):
                # Add closing quote
                line = line + '"'
                
            fixed_lines.append(line)
            
        return '\n'.join(fixed_lines)
    
    def _fix_malformed_arrays(self, content: str) -> str:
        """Fix malformed array syntax like closing brackets followed by content."""
        lines = content.split('\n')
        fixed_lines = []
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            # Look for lines that have "]" followed by non-array content
            if stripped.startswith(']') and len(stripped) > 1:
                # Split the line - keep the ], start new content on next line
                fixed_lines.append(']')
                remaining = stripped[1:].strip()
                if remaining:
                    fixed_lines.append(remaining)
            # Handle pattern like "] - " or "] stuff"
            elif '] ' in stripped and not stripped.startswith('['):
                parts = stripped.split('] ', 1)
                if len(parts) == 2:
                    fixed_lines.append(parts[0] + ']')
                    if parts[1].strip():
                        fixed_lines.append(parts[1])
                else:
                    fixed_lines.append(line)
            else:
                fixed_lines.append(line)
                
        return '\n'.join(fixed_lines)
    
    def _fix_key_value_pairs(self, content: str) -> str:
        """Fix malformed key-value pairs that are missing equals signs."""
        lines = content.split('\n')
        fixed_lines = []
        in_multiline_string = False
        
        for line in lines:
            stripped = line.strip()
            
            # Track if we're in a multiline string context
            if '"""' in stripped:
                quote_count = stripped.count('"""')
                if quote_count % 2 == 1:
                    in_multiline_string = not in_multiline_string
            elif "'''" in stripped:
                quote_count = stripped.count("'''")
                if quote_count % 2 == 1:
                    in_multiline_string = not in_multiline_string
            
            # Skip empty lines, comments, section headers, and content inside multiline strings
            if (not stripped or 
                stripped.startswith('#') or 
                stripped.startswith('[') or
                in_multiline_string):
                fixed_lines.append(line)
                continue
                
            # Look for lines that should be key-value pairs but are missing =
            # Only for actual configuration keys, not narrative text
            if ('=' not in stripped and 
                not stripped.startswith('"') and 
                not stripped.startswith("'") and
                ' ' in stripped and
                not stripped.startswith(('You', 'Run', 'If', 'Based', 'Create', 'Execute', 'Found', 'All', 'Checking', 'Working')) and
                len(stripped.split()) == 2):
                
                # Try to split into key and value
                parts = stripped.split(None, 1)
                if len(parts) == 2:
                    key, value = parts
                    # Only add equals if it looks like a real TOML key
                    if (key.isidentifier() or 
                        key.replace('_', '').replace('-', '').isalnum()):
                        fixed_lines.append(f"{key} = {value}")
                    else:
                        fixed_lines.append(line)
                else:
                    fixed_lines.append(line)
            else:
                fixed_lines.append(line)
                
        return '\n'.join(fixed_lines)

    def fix_toml(self, content: str) -> str:
        """
        Attempt to automatically fix TOML content.

        Args:
            content: Raw content that may need fixing

        Returns:
            Fixed TOML content
        """
        # Step 1: Clean Gemini artifacts
        content = self.clean_gemini_artifacts(content)

        # Step 2: Extract from markdown if needed
        content = self.extract_toml_from_markdown(content)

        # Step 3: Fix common TOML issues
        content = self.fix_common_toml_issues(content)
        
        # Step 4: If still invalid, try aggressive fixes
        is_valid, _ = self.validate_toml(content)
        if not is_valid:
            content = self._aggressive_fix_toml(content)

        return content
        
    def _aggressive_fix_toml(self, content: str) -> str:
        """
        Apply aggressive fixes for severely malformed TOML.
        """
        # If the content looks like narrative text that was incorrectly converted, 
        # try to reconstruct it properly
        if self._looks_like_corrupted_narrative(content):
            content = self._reconstruct_narrative_content(content)
        
        # Fix unterminated multiline strings by closing them at the end
        if content.count('"""') % 2 == 1:
            content = content + '\n"""'
        if content.count("'''") % 2 == 1:
            content = content + "\n'''"
            
        # Fix unterminated arrays
        open_brackets = content.count('[') - content.count(']')
        for _ in range(open_brackets):
            content = content + '\n]'
            
        return content
    
    def _looks_like_corrupted_narrative(self, content: str) -> bool:
        """Check if content looks like narrative text that was incorrectly converted to TOML."""
        lines = content.split('\n')
        narrative_indicators = 0
        total_lines = len([l for l in lines if l.strip()])
        
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
                
            # Look for signs that this is narrative text incorrectly converted
            if (stripped.startswith(('You =', 'Run =', 'If =', 'Based =', 'Create =', 'Execute =')) or
                stripped.endswith(' = "') or 
                '] =' in stripped or
                '- =' in stripped):
                narrative_indicators += 1
                
        # If more than 30% of lines look like corrupted narrative, treat as such
        return narrative_indicators > (total_lines * 0.3)
    
    def _reconstruct_narrative_content(self, content: str) -> str:
        """Attempt to reconstruct narrative content that was incorrectly processed."""
        lines = content.split('\n')
        fixed_lines = []
        in_multiline = False
        multiline_content = []
        
        for line in lines:
            stripped = line.strip()
            
            # Handle multiline string markers
            if stripped.startswith('content = """'):
                in_multiline = True
                fixed_lines.append('content = """')
                continue
            elif stripped == '"""' and in_multiline:
                # Close the multiline string
                fixed_lines.extend(multiline_content)
                fixed_lines.append('"""')
                in_multiline = False
                multiline_content = []
                continue
            elif in_multiline:
                # Inside multiline string - clean up the content
                if ' = "' in stripped:
                    # This looks like incorrectly converted text, try to fix
                    cleaned = stripped.replace(' = "', ' ')
                    if cleaned.endswith('"'):
                        cleaned = cleaned[:-1]
                    multiline_content.append(cleaned)
                else:
                    multiline_content.append(line)
                continue
            
            # Outside multiline strings - only keep proper TOML structure
            if (not stripped or 
                stripped.startswith('#') or
                stripped.startswith('[') or
                ('=' in stripped and not ' =' in stripped and not stripped.startswith(('You', 'Run', 'If')))):
                fixed_lines.append(line)
        
        return '\n'.join(fixed_lines)

    def validate_and_fix(self, content: str) -> Tuple[str, bool, List[str]]:
        """
        Validate TOML content and attempt to fix if invalid.

        Args:
            content: Raw TOML content

        Returns:
            Tuple of (fixed_content, is_valid, error_messages)
        """
        # First, try to validate as-is
        is_valid, errors = self.validate_toml(content)
        if is_valid:
            return content, True, []

        # Attempt to fix
        fixed_content = self.fix_toml(content)

        # Validate the fixed content
        is_valid_fixed, fixed_errors = self.validate_toml(fixed_content)

        if is_valid_fixed:
            return fixed_content, True, []
        else:
            return fixed_content, False, fixed_errors
