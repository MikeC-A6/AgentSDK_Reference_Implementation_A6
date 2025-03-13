from typing import List, Dict, Any, Optional, Type
import logging

from config import Config

class BaseAgent:
    """Base agent class that provides common functionality for all agents."""
    
    def __init__(self, name: str, instructions: str, tools: Optional[List] = None):
        """
        Initialize a base agent.
        
        Args:
            name: The agent's name
            instructions: Instructions for the agent
            tools: Optional list of tools to provide to the agent
        """
        self.name = name
        self.instructions = instructions
        self.tools = tools or []
        self.model_name = Config.DEFAULT_MODEL
        self.model_settings_dict = Config.get_model_settings()
    
    def build(self, agent_factory=None, function_tool_factory=None, model_settings_factory=None):
        """
        Build and return an Agent instance.
        
        This implements the Factory Method pattern, allowing
        different agent types to customize how agents are built.
        
        Args:
            agent_factory: A function that creates an Agent instance
            function_tool_factory: A function that creates a function tool
            model_settings_factory: A function that creates ModelSettings
            
        Returns:
            An Agent instance configured based on this agent's properties
        """
        logging.info(f"Building agent: {self.name}")
        
        # If we don't have the required factories, return a placeholder
        if not all([agent_factory, function_tool_factory, model_settings_factory]):
            logging.warning("Missing required factories, returning self as placeholder")
            return self
            
        # Create the model settings
        model_settings = model_settings_factory(**self.model_settings_dict)
        
        # Convert tools to a list of function tools
        function_tools = []
        for tool in self.tools:
            if hasattr(tool, 'to_function_tool'):
                tool_fn = tool.to_function_tool(function_tool_factory)
                if tool_fn:
                    function_tools.append(tool_fn)
                    logging.info(f"Successfully converted tool {tool.name} to function tool")
            else:
                function_tools.append(tool)
                logging.warning(f"Tool {getattr(tool, 'name', 'unknown')} does not have to_function_tool method")
        
        # Create and return the agent
        return agent_factory(
            name=self.name,
            instructions=self.instructions,
            model=self.model_name,
            model_settings=model_settings,
            tools=function_tools
        )
