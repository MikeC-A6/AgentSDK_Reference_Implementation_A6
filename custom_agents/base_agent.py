from typing import List, Dict, Any, Optional, Type
import logging

# Import from the OpenAI Agents SDK (openai-agents)
# The package is imported as 'agents' in Python
from agents import Agent, ModelSettings, function_tool

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
        self.model_settings = ModelSettings(**Config.get_model_settings())
    
    def build(self) -> Agent:
        """
        Build and return an Agent instance.
        
        This implements the Factory Method pattern, allowing
        different agent types to customize how agents are built.
        
        Returns:
            An Agent instance configured based on this agent's properties
        """
        logging.info(f"Building agent: {self.name}")
        
        # Convert tools to a list of function tools if they aren't already
        function_tools = []
        for tool in self.tools:
            if hasattr(tool, 'to_function_tool'):
                function_tools.append(tool.to_function_tool())
            else:
                function_tools.append(tool)
        
        return Agent(
            name=self.name,
            instructions=self.instructions,
            model=Config.DEFAULT_MODEL,
            model_settings=self.model_settings,
            tools=function_tools
        )
