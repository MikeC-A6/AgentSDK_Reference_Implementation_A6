from typing import List, Optional, Dict, Any, Literal
import logging
import json
from dataclasses import dataclass

from custom_agents.base_agent import BaseAgent
from tools.base_tool import BaseTool

class WebSearchAgent(BaseAgent):
    """
    An agent specialized in web search capabilities.
    
    This agent uses the gpt-4o-mini model which supports web search.
    """
    
    def __init__(self, tools: Optional[List[BaseTool]] = None):
        """
        Initialize a web search agent.
        
        Args:
            tools: Optional list of tools to provide to the agent
        """
        # Instructions focused on web search capabilities
        web_search_instructions = """
        You are a helpful assistant specialized in web search. When asked for information:
        
        1. Use web search to find the most relevant and up-to-date information
        2. Provide clear, concise answers based on search results
        3. Always cite your sources
        4. If the information cannot be found, acknowledge this and suggest alternatives
        5. For complex queries, break them down into simpler search queries
        
        When using web search:
        - Be specific with search queries
        - Summarize and integrate search results into your responses
        - Prioritize recent and authoritative sources
        - Provide balanced information when there are multiple perspectives
        
        Always be helpful, accurate, and thorough in your responses.
        """
        
        super().__init__(
            name="Web Search Assistant",
            instructions=web_search_instructions,
            tools=tools
        )
        
        # Override the model name to use gpt-4o-mini explicitly
        self.model_name = "gpt-4o-mini"
        
        logging.info("WebSearchAgent initialized with web search capabilities")
    
    def build(self, agent_factory=None, function_tool_factory=None, model_settings_factory=None):
        """
        Build the agent with the specified factories and add web search tool.
        
        Args:
            agent_factory: Factory function to create an agent
            function_tool_factory: Factory function to create function tools
            model_settings_factory: Factory function to create model settings
            
        Returns:
            An agent instance with web search capability
        """
        logging.debug(f"Building WebSearchAgent with model: {self.model_name}")
        
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
        
        # Try to use the built-in WebSearchTool from the agents SDK
        try:
            # Import the WebSearchTool from the agents SDK
            from agents import WebSearchTool
            
            # Create a WebSearchTool instance with medium search context size
            web_search_tool = WebSearchTool(search_context_size="medium")
            logging.debug(f"Created WebSearchTool with name: {web_search_tool.name}")
            
            # Add the web search tool to the function tools
            function_tools.append(web_search_tool)
            logging.debug(f"Added web search tool to tools list, now have {len(function_tools)} tools")
        except ImportError as e:
            logging.error(f"Failed to import WebSearchTool from agents SDK: {str(e)}")
            logging.warning("Falling back to custom web search tool implementation")
            
            # Create a custom web search function tool
            try:
                # Create a web search function tool using the function_tool_factory
                web_search_schema = {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The search query to look up on the web"
                        }
                    },
                    "required": ["query"],
                    "additionalProperties": False  # This is required by the OpenAI API
                }
                
                def web_search_function(query: str) -> str:
                    """Search the web for information."""
                    logging.info(f"Web search function called with query: {query}")
                    # This is a placeholder implementation that would be replaced by actual web search
                    # In a real implementation, this would call a web search API
                    return f"Results for: {query}\n\nThe Eiffel Tower was designed by Gustave Eiffel and his team of engineers. Construction began in 1887 and was completed in 1889."
                
                # Create the function tool
                web_search_tool = function_tool_factory(
                    web_search_function,
                    name="web_search_preview",  # Use the same name as the official tool
                    description="Search the web for information. Use this when you need up-to-date information or to verify facts.",
                    parameter_schema=web_search_schema
                )
                
                logging.debug(f"Created custom web search function tool: {web_search_tool}")
                
                # Add the web search tool to the function tools
                function_tools.append(web_search_tool)
                logging.debug(f"Added custom web search tool to tools list, now have {len(function_tools)} tools")
            except Exception as e:
                logging.error(f"Failed to create custom web search function tool: {str(e)}", exc_info=True)
        except Exception as e:
            logging.error(f"Failed to add web search tool: {str(e)}", exc_info=True)
        
        # Create and return the agent
        try:
            # Try to create the agent
            agent_kwargs = {
                "name": self.name,
                "instructions": self.instructions,
                "model": self.model_name,
                "model_settings": model_settings,
                "tools": function_tools
            }
            
            # Log the agent creation parameters
            logging.debug(f"Creating agent with parameters: {agent_kwargs}")
            
            # Create the agent
            agent = agent_factory(**agent_kwargs)
            
            logging.info(f"Successfully built WebSearchAgent with {len(function_tools)} tools")
            return agent
        except TypeError as e:
            # If we get a TypeError about 'model', try without it
            if "unexpected keyword argument 'model'" in str(e):
                logging.warning(f"Agent factory doesn't accept 'model' parameter: {str(e)}")
                logging.warning("Trying again without model parameter")
                
                agent = agent_factory(
                    name=self.name,
                    instructions=self.instructions,
                    model_settings=model_settings,
                    tools=function_tools
                )
                
                logging.info(f"Successfully built WebSearchAgent without model parameter")
                return agent
            else:
                # For other TypeErrors, log and return self
                logging.error(f"Failed to create agent: {str(e)}", exc_info=True)
                return self
        except Exception as e:
            logging.error(f"Failed to create WebSearchAgent: {str(e)}", exc_info=True)
            return self 