from typing import List, Optional, Dict, Any
import logging

from custom_agents.base_agent import BaseAgent
from tools.base_tool import BaseTool

class PlannerAgent(BaseAgent):
    """
    An agent specialized in creating and executing plans.
    
    This agent extends the base agent with planning-specific instructions.
    """
    
    def __init__(self, tools: Optional[List[BaseTool]] = None, enable_web_search: bool = True):
        """
        Initialize a planner agent.
        
        Args:
            tools: Optional list of tools to provide to the agent
            enable_web_search: Whether to enable web search capabilities via handoff
        """
        # Enhanced instructions for planning capabilities
        planning_instructions = """
        You are a helpful assistant with planning capabilities. When faced with complex tasks:
        
        1. Break down the task into smaller steps
        2. Create a clear plan to achieve the goal
        3. Execute the plan step by step
        4. ALWAYS use the calculator tool for ANY mathematical operations, no matter how simple
        5. When you need up-to-date information or to verify facts, hand off to the Web Search Assistant
        6. Always explain your reasoning and current step of the plan
        
        When using the calculator tool:
        - Use it for ALL calculations, even simple ones like addition or multiplication
        - Format your request as a clear mathematical expression
        - Show both the expression you're calculating and the result
        - Example: To calculate 25 * 4, use the calculator tool with expression "25 * 4"
        
        When you need to search the web:
        - Use the web_search_preview tool to hand off to the Web Search Assistant with a clear, specific query
        - The Web Search Assistant will search the web and provide you with the information
        - Continue your plan with the information provided
        
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
        
        # Override the model name to use o3-mini explicitly
        self.model_name = "o3-mini"
        
        # Store whether web search is enabled
        self.enable_web_search = enable_web_search
        
        logging.info("PlannerAgent initialized with planning capabilities")
    
    def build(self, agent_factory=None, function_tool_factory=None, model_settings_factory=None):
        """
        Build the agent with the specified factories.
        
        Args:
            agent_factory: Factory function to create an agent
            function_tool_factory: Factory function to create function tools
            model_settings_factory: Factory function to create model settings
            
        Returns:
            An agent instance
        """
        logging.debug(f"Building PlannerAgent with model: {self.model_name}")
        
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
        
        # If web search is enabled, add handoff to the WebSearchAgent
        handoffs = []
        if self.enable_web_search:
            logging.info("Web search is enabled, attempting to add web search handoff")
            
            try:
                # Import the WebSearchAgent
                from custom_agents.web_search_agent import WebSearchAgent
                
                # Try to get the handoff function from agent_wrapper
                try:
                    from agent_wrapper import handoff
                    
                    if handoff is None:
                        logging.error("handoff function is None in agent_wrapper")
                        raise ImportError("handoff function is None")
                        
                    logging.info("Successfully imported handoff from agent_wrapper")
                except (ImportError, AttributeError) as e:
                    logging.error(f"Failed to import handoff from agent_wrapper: {str(e)}")
                    logging.warning("Will try to create a simple handoff dictionary instead")
                    
                    # Create a simple handoff dictionary as fallback
                    def handoff_fallback(agent, tool_name_override=None, tool_description_override=None):
                        logging.warning("Using handoff_fallback function")
                        return {
                            "agent": agent,
                            "tool_name": tool_name_override or f"handoff_to_{agent.name}",
                            "tool_description": tool_description_override or f"Handoff to {agent.name}"
                        }
                    
                    handoff = handoff_fallback
                
                # Create the web search agent
                web_search_agent = WebSearchAgent()
                
                # Build the web search agent
                built_web_search_agent = web_search_agent.build(
                    agent_factory=agent_factory,
                    function_tool_factory=function_tool_factory,
                    model_settings_factory=model_settings_factory
                )
                
                # Log the built web search agent details
                logging.debug(f"Built WebSearchAgent: {built_web_search_agent.name}, model: {getattr(built_web_search_agent, 'model', 'unknown')}")
                
                # Get the correct tool name from the WebSearchTool
                try:
                    from agents import WebSearchTool
                    tool_name = WebSearchTool().name  # Get the name from the actual tool
                    logging.debug(f"Using tool name from WebSearchTool: {tool_name}")
                except ImportError:
                    tool_name = "web_search_preview"  # Fallback to the known name
                    logging.warning(f"Could not import WebSearchTool, using fallback name: {tool_name}")
                
                # Create a handoff to the web search agent
                web_search_handoff = handoff(
                    agent=built_web_search_agent,
                    tool_name_override=tool_name,  # Use the name from the WebSearchTool
                    tool_description_override="Search the web for information. Use this when you need up-to-date information or to verify facts."
                )
                
                # Define the input schema for the handoff
                input_schema = {
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
                
                # If the handoff function returned a dictionary, add the input schema
                if isinstance(web_search_handoff, dict):
                    web_search_handoff["input_schema"] = input_schema
                    logging.debug(f"Added input schema to handoff dictionary: {web_search_handoff}")
                # If it's an object with an input_json_schema attribute, try to update it
                elif hasattr(web_search_handoff, "input_json_schema"):
                    try:
                        web_search_handoff.input_json_schema = input_schema
                        logging.debug(f"Updated input_json_schema on handoff object")
                    except (AttributeError, TypeError) as e:
                        logging.warning(f"Could not update input_json_schema on handoff object: {str(e)}")
                
                # Log the handoff details
                if isinstance(web_search_handoff, dict):
                    logging.debug(f"Created handoff dictionary: {web_search_handoff}")
                else:
                    logging.debug(f"Created handoff object of type: {type(web_search_handoff)}")
                
                # Add the handoff to the handoffs list
                handoffs.append(web_search_handoff)
                logging.info("Added web search handoff to the handoffs list")
            except Exception as e:
                logging.error(f"Failed to add web search handoff: {str(e)}", exc_info=True)
        else:
            logging.info("Web search is disabled")
        
        # Create and return the agent with handoffs
        try:
            # Try to create the agent with handoffs
            agent_kwargs = {
                "name": self.name,
                "instructions": self.instructions,
                "model": self.model_name,
                "model_settings": model_settings,
                "tools": function_tools
            }
            
            # Only add handoffs if we have any
            if handoffs:
                agent_kwargs["handoffs"] = handoffs
                
            # Log the agent creation parameters
            logging.debug(f"Creating agent with parameters: {agent_kwargs}")
            
            # Create the agent
            agent = agent_factory(**agent_kwargs)
            
            logging.info(f"Successfully built PlannerAgent with {len(function_tools)} tools and {len(handoffs)} handoffs")
            return agent
        except TypeError as e:
            # If we get a TypeError, it might be because the agent_factory doesn't accept 'handoffs'
            # Try again without handoffs
            if "unexpected keyword argument 'handoffs'" in str(e):
                logging.warning(f"Agent factory doesn't accept 'handoffs' parameter: {str(e)}")
                logging.warning("Trying again without handoffs parameter")
                
                agent = agent_factory(
                    name=self.name,
                    instructions=self.instructions,
                    model=self.model_name,
                    model_settings=model_settings,
                    tools=function_tools
                )
                
                logging.info(f"Successfully built PlannerAgent without handoffs parameter")
                return agent
            # If we get a TypeError about 'model', try without it
            elif "unexpected keyword argument 'model'" in str(e):
                logging.warning(f"Agent factory doesn't accept 'model' parameter: {str(e)}")
                logging.warning("Trying again without model parameter")
                
                agent = agent_factory(
                    name=self.name,
                    instructions=self.instructions,
                    model_settings=model_settings,
                    tools=function_tools,
                    handoffs=handoffs if handoffs else None
                )
                
                logging.info(f"Successfully built PlannerAgent without model parameter")
                return agent
            else:
                # For other TypeErrors, log and return self
                logging.error(f"Failed to create agent: {str(e)}", exc_info=True)
                return self
        except Exception as e:
            logging.error(f"Failed to create agent: {str(e)}", exc_info=True)
            return self
