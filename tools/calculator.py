import logging
import math
import re
from typing import Dict, Any

from tools.base_tool import BaseTool

class CalculatorTool(BaseTool):
    """A simple calculator tool for basic arithmetic operations."""
    
    @property
    def name(self) -> str:
        return "calculate"
    
    @property
    def description(self) -> str:
        return "Perform mathematical calculations. Supports addition, subtraction, multiplication, division, exponentiation, and basic math functions like sin, cos, sqrt."

    def execute(self, *args, **kwargs) -> Any:
        """
        Execute the calculator with the provided arguments.
        
        Args:
            *args: Positional arguments (first one is used as expression if provided)
            **kwargs: Keyword arguments (looks for 'expression' key)
            
        Returns:
            A string containing the result of the calculation or an error message
        """
        # Extract expression from either args or kwargs
        if args and len(args) > 0:
            expression = args[0]
        elif 'expression' in kwargs:
            expression = kwargs['expression']
        else:
            return "Error: No expression provided. Please provide a mathematical expression to evaluate."
            
        logging.info(f"Calculating expression: {expression}")
        
        try:
            # Clean and validate the expression
            cleaned_expr = self._clean_expression(expression)
            if self._is_unsafe_expression(cleaned_expr):
                return "Error: The expression contains unsafe operations or functions."
            
            # Define allowed math functions
            math_context = {
                "sin": math.sin, 
                "cos": math.cos, 
                "tan": math.tan, 
                "sqrt": math.sqrt, 
                "log": math.log,
                "exp": math.exp,
                "abs": abs,
                "pi": math.pi, 
                "e": math.e
            }
            
            # Evaluate the expression with restricted context
            result = eval(cleaned_expr, {"__builtins__": None}, math_context)
            
            # Format the result
            if isinstance(result, (int, float)):
                if isinstance(result, int) or float(result).is_integer():
                    return str(int(result))
                else:
                    return str(round(result, 8))
            else:
                return str(result)
                
        except Exception as e:
            logging.error(f"Error in calculation: {str(e)}")
            return f"Error calculating: {str(e)}"
    
    def _clean_expression(self, expression: str) -> str:
        """Clean and sanitize the expression for evaluation."""
        if not isinstance(expression, str):
            expression = str(expression)
            
        # Replace common mathematical notations
        expression = expression.lower().replace('^', '**')
        
        # Clean whitespace
        expression = re.sub(r'\s+', '', expression)
        
        return expression
    
    def _is_unsafe_expression(self, expression: str) -> bool:
        """Check if the expression contains unsafe operations."""
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
        
        Args:
            function_tool_factory: A function that creates a function tool
        
        Returns:
            A function tool for the OpenAI Agents SDK
        """
        if function_tool_factory is None:
            return self
        
        # Create a properly typed wrapper function for the SDK that will map to our execute method
        # The function signature must match what we want in our parameters
        def calculator_function(expression: str) -> str:
            """
            Perform mathematical calculations. Supports addition, subtraction, multiplication, division, exponentiation, and basic math functions like sin, cos, sqrt.
            
            Args:
                expression: The mathematical expression to evaluate
            
            Returns:
                The result of the calculation as a string
            """
            return self.execute(expression)
        
        # Return the function tool
        # The SDK will automatically extract the schema from the function signature and docstring
        return function_tool_factory(calculator_function)
