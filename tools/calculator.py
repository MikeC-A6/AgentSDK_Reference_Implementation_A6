import logging
from typing import Any, Dict
import math
import re

from tools.base_tool import BaseTool

class CalculatorTool(BaseTool):
    """A simple calculator tool for basic arithmetic operations."""
    
    @property
    def name(self) -> str:
        return "calculate"
    
    @property
    def description(self) -> str:
        return "Perform basic calculations. Supports addition, subtraction, multiplication, division, and exponentiation."

    @property
    def parameter_schema(self) -> Dict:
        """Get the parameter schema for this tool."""
        return {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "The mathematical expression to evaluate"
                }
            },
            "required": ["expression"]
        }
    
    def execute(self, *args, **kwargs) -> str:
        """
        Calculate the result of a mathematical expression.
        
        Args:
            expression: A string containing a mathematical expression to evaluate
            
        Returns:
            A string containing the result of the calculation or an error message
        """
        # Extract expression from either args or kwargs
        if args and len(args) > 0:
            expression = args[0]
        elif 'expression' in kwargs:
            expression = kwargs['expression']
        else:
            return "Error: No expression provided. Please specify a mathematical expression to evaluate."
            
        logging.info(f"Calculating expression: {expression}")
        
        try:
            # Clean the expression
            cleaned_expr = self._clean_expression(expression)
            
            # Check for unsafe operations
            if self._is_unsafe_expression(cleaned_expr):
                return "Error: The expression contains unsafe operations or functions."
            
            # Evaluate the expression
            result = eval(cleaned_expr, {"__builtins__": None}, 
                         {"sin": math.sin, "cos": math.cos, "tan": math.tan, 
                          "sqrt": math.sqrt, "pi": math.pi, "e": math.e})
            
            # Format the result
            if isinstance(result, int) or result.is_integer():
                return str(int(result))
            else:
                return str(round(result, 8))
                
        except Exception as e:
            logging.error(f"Error in calculation: {str(e)}")
            return f"Error calculating: {str(e)}"
    
    def _clean_expression(self, expression: str) -> str:
        """Clean and sanitize the expression for evaluation."""
        # Replace common mathematical notations
        expression = expression.lower().replace('^', '**')
        
        # Clean whitespace
        expression = re.sub(r'\s+', '', expression)
        
        return expression
    
    def _is_unsafe_expression(self, expression: str) -> bool:
        """Check if the expression contains unsafe operations."""
        # List of patterns to reject
        unsafe_patterns = [
            r'import',
            r'exec',
            r'eval',
            r'compile',
            r'open',
            r'__',
            r'globals',
            r'locals',
            r'getattr',
            r'setattr',
            r'system',
            r'subprocess',
            r'os\.',
            r'sys\.',
        ]
        
        for pattern in unsafe_patterns:
            if re.search(pattern, expression):
                return True
        
        return False
        
    def to_function_tool(self, function_tool_factory=None):
        """
        Convert this tool to a function tool for the OpenAI Agents SDK.
        
        Override the base method to provide a proper schema.
        
        Args:
            function_tool_factory: A function that creates a function tool
        
        Returns:
            A function tool for the OpenAI Agents SDK
        """
        if function_tool_factory is None:
            return self
        
        # Create a wrapper function that matches our execute method
        def wrapper(expression: str) -> str:
            return self.execute(expression)
        
        # Set the name and docstring
        wrapper.__name__ = self.name
        wrapper.__doc__ = self.description
        
        # Create the function tool with the proper schema
        return function_tool_factory(
            wrapper,
            schema=self.parameter_schema
        )
