from typing import List, Optional, Dict, Any
import logging

from custom_agents.base_agent import BaseAgent
from tools.base_tool import BaseTool

class PlannerAgent(BaseAgent):
    """
    An agent specialized in creating and executing plans.
    
    This agent extends the base agent with planning-specific instructions.
    """
    
    def __init__(self, tools: Optional[List[BaseTool]] = None):
        """
        Initialize a planner agent.
        
        Args:
            tools: Optional list of tools to provide to the agent
        """
        # Enhanced instructions for planning capabilities
        planning_instructions = """
        You are a helpful assistant with planning capabilities. When faced with complex tasks:
        
        1. Break down the task into smaller steps
        2. Create a clear plan to achieve the goal
        3. Execute the plan step by step
        4. Use the available tools when needed to gather information or perform calculations
        5. Always explain your reasoning and current step of the plan
        
        When using web search:
        - Be specific with search queries
        - Summarize and integrate search results into your responses
        - Search for up-to-date information when needed
        
        When creating plans:
        - Consider possible challenges and include contingency steps
        - Estimate the time or complexity of each step
        - Clearly mark which step you're currently on
        
        Always be helpful, accurate, and thorough in your responses.
        """
        
        super().__init__(
            name="Planning Assistant",
            instructions=planning_instructions,
            tools=tools
        )
        
        logging.info("PlannerAgent initialized with planning capabilities")
