"""
Wrapper module to handle import compatibility issues with the OpenAI Agents SDK.

This module provides a clean interface around the agents SDK, handling
various import and compatibility issues.
"""

import logging
import asyncio
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Global variables for imported classes and modules
Agent = None
ModelSettings = None
function_tool = None
Runner = None
Model = None

def init_components():
    """Initialize all components needed for the agents SDK."""
    global Agent, ModelSettings, function_tool, Runner, Model
    
    try:
        # Import agents package first
        import agents
        
        # Then try to import interfaces and classes
        try:
            from agents.models.interface import Model as ModelClass
            Model = ModelClass
            
            # Patch the agents package to provide Model class
            if not hasattr(agents, 'Model'):
                agents.Model = Model
                logger.info("Patched agents.Model successfully")
        except ImportError:
            # If direct import fails, create a stub Model class
            class ModelStub:
                def __init__(self, name, **kwargs):
                    self.name = name
                    self.__dict__.update(kwargs)
            
            # Use the stub
            Model = ModelStub
            if not hasattr(agents, 'Model'):
                agents.Model = Model
        
        # Now import the rest of the components
        from agents.agent import Agent as AgentClass
        from agents.model_settings import ModelSettings as ModelSettingsClass
        from agents.tool import function_tool as function_tool_fn
        from agents.run import Runner as RunnerClass
        
        # Store the imports in our global variables
        Agent = AgentClass
        ModelSettings = ModelSettingsClass
        function_tool = function_tool_fn
        Runner = RunnerClass
        
        logger.info("Successfully initialized OpenAI Agents SDK components")
        return True
    except ImportError as e:
        logger.error(f"Failed to initialize OpenAI Agents SDK components: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during SDK initialization: {str(e)}")
        return False

# Initialize components when the module is imported
init_components()

def create_run(agent: Any, messages: List[Dict[str, Any]]) -> Any:
    """
    Create a run with the given agent and messages.
    
    This function adapts the Runner.run() API of the OpenAI Agents SDK to be 
    compatible with our expected interface.
    
    Args:
        agent: The agent to run
        messages: The messages to send to the agent
        
    Returns:
        A Run-like object that can be used to get the final result
    """
    if Runner is None:
        success = init_components()
        if not success:
            raise ImportError("Failed to initialize SDK components")
    
    # Extract the user's message content
    if messages and len(messages) > 0 and 'content' in messages[0]:
        user_input = messages[0]['content']
    else:
        user_input = ""
    
    # Create a wrapper object to provide compatibility with the expected interface
    class RunWrapper:
        def __init__(self, agent, user_input):
            self.agent = agent
            self.user_input = user_input
            
        async def get_final_run_result(self):
            # Run the agent using the Runner class
            try:
                result = await Runner.run(
                    starting_agent=self.agent,
                    input=self.user_input
                )
                return result
            except Exception as e:
                logger.error(f"Error running agent: {str(e)}")
                # Return a simple error result
                class ErrorResult:
                    def __init__(self, error):
                        self.output = f"Error: {str(error)}"
                        self.trace_id = None
                return ErrorResult(e)
    
    # Return the wrapper object
    return RunWrapper(agent, user_input)

def get_model_settings(**kwargs) -> Any:
    """
    Create a ModelSettings instance with the given kwargs.
    
    Args:
        **kwargs: Arguments to pass to the ModelSettings constructor
        
    Returns:
        A ModelSettings instance
    """
    if ModelSettings is None:
        success = init_components()
        if not success:
            raise ImportError("Failed to initialize SDK components")
    
    return ModelSettings(**kwargs)