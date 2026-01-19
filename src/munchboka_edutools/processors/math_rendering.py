"""Math rendering processor for enhanced mathematical typesetting."""

from typing import Dict, Any
from bs4 import BeautifulSoup

from .base import Processor


class MathRenderingProcessor(Processor):
    """Enhance mathematical content rendering.
    
    Features:
    - Optimize MathJax/KaTeX output for print
    - Ensure proper font sizes in equations
    - Add page break protection for equations
    - Improve equation numbering and references
    """
    
    @property
    def name(self) -> str:
        return "math_rendering"
    
    @property
    def priority(self) -> int:
        return 30
    
    def process(self, html_content: str, soup: BeautifulSoup, context: Dict[str, Any]) -> str:
        """Apply math rendering enhancements."""
        
        self._add_math_css(soup)
        self._protect_math_from_breaks(soup)
        
        if self.config.get("enhance_equation_numbers", True):
            self._enhance_equation_numbers(soup)
        
        return str(soup)
    
    def _add_math_css(self, soup: BeautifulSoup) -> None:
        """Add CSS for better math rendering in print."""
        style_tag = soup.new_tag("style")
        style_tag.string = """
        /* Math rendering enhancements */
        .math, .math-display {
            font-size: inherit;
            overflow-x: auto;
            overflow-y: hidden;
        }
        
        @media print {
            /* Prevent page breaks inside equations */
            .math-display, .MathJax_Display {
                page-break-inside: avoid;
                break-inside: avoid;
            }
            
            /* Ensure proper margins for display math */
            .math-display {
                margin: 1em 0;
            }
            
            /* Equation numbers */
            .math .eqno {
                float: right;
                margin-left: 1em;
            }
        }
        
        /* Better inline math alignment */
        .math-inline {
            display: inline-block;
            vertical-align: middle;
        }
        """
        
        if soup.head:
            soup.head.append(style_tag)
    
    def _protect_math_from_breaks(self, soup: BeautifulSoup) -> None:
        """Add page break protection to math elements."""
        
        # Find all math containers
        math_selectors = [
            '.math',
            '.math-display',
            '.MathJax_Display',
            '.katex-display',
            'div.math',
        ]
        
        for selector in math_selectors:
            for math_element in soup.select(selector):
                if 'class' in math_element.attrs:
                    if 'avoid-break-inside' not in math_element['class']:
                        math_element['class'].append('avoid-break-inside')
                else:
                    math_element['class'] = ['avoid-break-inside']
    
    def _enhance_equation_numbers(self, soup: BeautifulSoup) -> None:
        """Improve equation numbering styling."""
        
        # Find equation numbers and ensure they're properly styled
        for eqno in soup.select('.eqno'):
            if 'class' in eqno.attrs:
                eqno['class'].append('equation-number')
            else:
                eqno['class'] = ['equation-number']
