"""
Template rendering service with Jinja2
"""

import re
from typing import Dict, Any, List
from jinja2 import Environment, BaseLoader, TemplateSyntaxError


class TemplateService:
    """Service for rendering email templates with variables"""
    
    def __init__(self):
        self.env = Environment(loader=BaseLoader())
    
    def extract_variables(self, html_content: str) -> List[str]:
        """
        Extract all variables from template content
        Variables are in format: {{variable_name}}
        """
        pattern = r'\{\{(\s*[\w\.]+\s*)\}\}'
        matches = re.findall(pattern, html_content)
        # Clean and deduplicate
        variables = list(set([var.strip() for var in matches]))
        return sorted(variables)
    
    def render(self, html_content: str, data: Dict[str, Any]) -> str:
        """
        Render template with provided data
        
        Args:
            html_content: HTML template with {{variable}} placeholders
            data: Dictionary of variable values
            
        Returns:
            Rendered HTML string
            
        Raises:
            TemplateSyntaxError: If template syntax is invalid
            ValueError: If required variables are missing
        """
        try:
            template = self.env.from_string(html_content)
            
            # Validate that all required variables are provided
            required_vars = self.extract_variables(html_content)
            missing_vars = [var for var in required_vars if var not in data]
            
            if missing_vars:
                # Provide default empty strings for missing variables
                for var in missing_vars:
                    data[var] = ""
            
            rendered = template.render(**data)
            return rendered
            
        except TemplateSyntaxError as e:
            raise ValueError(f"Invalid template syntax: {str(e)}")
        except Exception as e:
            raise ValueError(f"Error rendering template: {str(e)}")
    
    def validate_template(self, html_content: str) -> Dict[str, Any]:
        """
        Validate template syntax and return info
        
        Returns:
            Dict with: is_valid, variables, errors
        """
        try:
            # Try to parse template
            self.env.from_string(html_content)
            variables = self.extract_variables(html_content)
            
            return {
                "is_valid": True,
                "variables": variables,
                "errors": []
            }
        except TemplateSyntaxError as e:
            return {
                "is_valid": False,
                "variables": [],
                "errors": [str(e)]
            }
    
    def render_preview(
        self,
        html_content: str,
        recipient_data: Dict[str, Any],
        unsubscribe_url: str
    ) -> str:
        """
        Render a preview of the email for a specific recipient
        """
        # Merge recipient data with unsubscribe URL
        data = {
            **recipient_data,
            "unsubscribe_url": unsubscribe_url
        }
        
        return self.render(html_content, data)


# Global template service instance
_template_service = None


def get_template_service() -> TemplateService:
    """Get or create template service singleton"""
    global _template_service
    if _template_service is None:
        _template_service = TemplateService()
    return _template_service
