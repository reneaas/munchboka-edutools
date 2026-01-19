"""Page break processor for print layouts."""

from typing import Dict, Any
from bs4 import BeautifulSoup

from .base import Processor


class PageBreakProcessor(Processor):
    """Control page breaks for optimal print layout.
    
    Features:
    - Force page breaks before chapters
    - Avoid breaks after headings
    - Avoid breaks inside figures and tables
    - Keep related content together
    """
    
    @property
    def name(self) -> str:
        return "page_breaks"
    
    @property
    def priority(self) -> int:
        return 60
    
    def process(self, html_content: str, soup: BeautifulSoup, context: Dict[str, Any]) -> str:
        """Apply page break rules."""
        
        self._add_page_break_css(soup)
        self._apply_page_break_classes(soup)
        
        return str(soup)
    
    def _add_page_break_css(self, soup: BeautifulSoup) -> None:
        """Add CSS rules for page breaks."""
        style_tag = soup.new_tag("style")
        style_tag.string = """
        /* Page break control for print */
        @media print {
            .page-break-before {
                page-break-before: always;
                break-before: page;
            }
            
            .page-break-after {
                page-break-after: always;
                break-after: page;
            }
            
            .avoid-break-inside {
                page-break-inside: avoid;
                break-inside: avoid;
            }
            
            .avoid-break-after {
                page-break-after: avoid;
                break-after: avoid;
            }
            
            /* Headings */
            h1 {
                page-break-before: always;
                break-before: page;
            }
            
            h2, h3, h4, h5, h6 {
                page-break-after: avoid;
                break-after: avoid;
            }
            
            /* Keep content together */
            figure, table, .admonition, .code-block {
                page-break-inside: avoid;
                break-inside: avoid;
            }
            
            /* Keep heading with following paragraph */
            h1, h2, h3, h4, h5, h6 {
                page-break-after: avoid;
                break-after: avoid;
            }
            
            h1 + p, h2 + p, h3 + p, h4 + p, h5 + p, h6 + p {
                page-break-before: avoid;
                break-before: avoid;
            }
        }
        """
        
        if soup.head:
            soup.head.append(style_tag)
    
    def _apply_page_break_classes(self, soup: BeautifulSoup) -> None:
        """Add page break classes to appropriate elements."""
        
        # Force page breaks before chapters (h1)
        if self.config.get("break_before_chapters", True):
            for h1 in soup.find_all('h1'):
                if 'class' in h1.attrs:
                    h1['class'].append('page-break-before')
                else:
                    h1['class'] = ['page-break-before']
        
        # Avoid breaks inside specific elements
        avoid_break_selectors = [
            'figure',
            'table',
            '.admonition',
            '.sidebar',
            '.example',
            '.proof',
        ]
        
        for selector in avoid_break_selectors:
            for element in soup.select(selector):
                if 'class' in element.attrs:
                    element['class'].append('avoid-break-inside')
                else:
                    element['class'] = ['avoid-break-inside']
