from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Type

class BaseTool(ABC):
    """Base class for all tools in the system.
    
    Following the Interface Segregation and Dependency Inversion principles,
    this abstract base class defines the interface that all tools must implement.
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the tool."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Description of what the tool does."""
        pass
    
    @abstractmethod
    def execute(self, *args, **kwargs) -> Any:
        """Execute the tool with the provided arguments."""
        pass
    
    def to_function_tool(self, function_tool_factory=None):
        """
        Convert this tool to a function tool for the OpenAI Agents SDK.
        
        Args:
            function_tool_factory: A function that creates a function tool,
                usually agents.function_tool
        
        Returns:
            A function tool for the OpenAI Agents SDK
        """
        if function_tool_factory is None:
            # If no factory is provided, return a placeholder
            # This will be replaced in the actual agent creation
            return self
        
        # Create a wrapper function with the same signature as execute
        wrapper = lambda *args, **kwargs: self.execute(*args, **kwargs)
        
        # Set the name and docstring of the wrapper
        wrapper.__name__ = self.name
        wrapper.__doc__ = self.description
        
        # Create and return the function tool
        return function_tool_factory(wrapper)
