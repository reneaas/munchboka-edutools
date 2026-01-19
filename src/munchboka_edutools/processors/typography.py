"""Typography processor for print-quality text formatting."""

from typing import Dict, Any
from bs4 import BeautifulSoup, NavigableString
import re

from .base import Processor


class TypographyProcessor(Processor):
    """Enhance typography for print output.
    
    Features:
    - Norwegian hyphenation hints
    - Widow and orphan control via CSS
    - Smart quotes and dashes
    - Non-breaking spaces in appropriate contexts
    - Proper formatting of numbers and units
    """
    
    @property
    def name(self) -> str:
        return "typography"
    
    @property
    def priority(self) -> int:
        return 20
    
    def process(self, html_content: str, soup: BeautifulSoup, context: Dict[str, Any]) -> str:
        """Apply typography enhancements."""
        
        # Add hyphenation and widow/orphan control via CSS
        self._add_typography_css(soup)
        
        # Apply text transformations
        if self.config.get("smart_quotes", True):
            self._apply_smart_quotes(soup)
        
        if self.config.get("non_breaking_spaces", True):
            self._apply_non_breaking_spaces(soup)
        
        if self.config.get("number_formatting", True):
            self._format_numbers(soup)
        
        return str(soup)
    
    def _add_typography_css(self, soup: BeautifulSoup) -> None:
        """Add CSS for hyphenation and widow/orphan control."""
        style_tag = soup.new_tag("style")
        style_tag.string = """
        /* Typography enhancements */
        body {
            hyphens: auto;
            -webkit-hyphens: auto;
            -ms-hyphens: auto;
            hyphenate-limit-chars: 6 3 3;
            hyphenate-limit-lines: 2;
        }
        
        p, li {
            orphans: 3;
            widows: 3;
        }
        
        h1, h2, h3, h4, h5, h6 {
            page-break-after: avoid;
            break-after: avoid;
        }
        
        /* Better text rendering */
        body {
            text-rendering: optimizeLegibility;
            font-feature-settings: "kern" 1, "liga" 1;
        }
        """
        
        if soup.head:
            soup.head.append(style_tag)
    
    def _apply_smart_quotes(self, soup: BeautifulSoup) -> None:
        """Replace straight quotes with typographic quotes."""
        # Norwegian/English smart quotes
        replacements = [
            (r'"([^"]+)"', r'«\1»'),  # Norwegian guillemets
            (r"'([^']+)'", r"'\1'"),   # Single smart quotes
        ]
        
        self._apply_text_replacements(soup, replacements)
    
    def _apply_non_breaking_spaces(self, soup: BeautifulSoup) -> None:
        """Add non-breaking spaces where appropriate."""
        # Common Norwegian abbreviations and contexts
        # Using actual Unicode characters instead of escape sequences in regex
        nbsp = '\u00A0'
        patterns = [
            (r'\b(\d+)\s+(kr|mm|cm|m|km|g|kg|ml|l)\b', rf'\1{nbsp}\2'),  # Numbers + units
            (r'\bf\.\s*eks\.', f'f.{nbsp}eks.'),  # For eksempel
            (r'\bd\.\s*v\.\s*s\.', f'd.{nbsp}v.{nbsp}s.'),  # Det vil si
        ]
        
        self._apply_text_replacements(soup, patterns)
    
    def _format_numbers(self, soup: BeautifulSoup) -> None:
        """Format numbers with proper spacing and separators."""
        # Norwegian number formatting: space as thousands separator
        # Using actual thin space character instead of escape sequence
        thin_space = '\u202F'
        pattern = r'\b(\d{1,3})(\d{3})\b'
        replacement = rf'\1{thin_space}\2'
        
        self._apply_text_replacements(soup, [(pattern, replacement)])
    
    def _apply_text_replacements(self, soup: BeautifulSoup, replacements: list) -> None:
        """Apply regex replacements to text nodes, avoiding code blocks."""
        # Don't modify code elements
        skip_tags = {'code', 'pre', 'script', 'style'}
        
        for element in soup.find_all(text=True):
            if any(parent.name in skip_tags for parent in element.parents):
                continue
            
            text = str(element)
            for pattern, repl in replacements:
                text = re.sub(pattern, repl, text)
            
            if text != str(element):
                element.replace_with(NavigableString(text))
