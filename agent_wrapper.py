"""
Wrapper module to handle import compatibility issues with the OpenAI Agents SDK.

This module provides a clean interface around the agents SDK, handling
various import and compatibility issues.
"""

import logging
import asyncio
from typing import Any, Dict, List, Optional
import importlib
import sys

logger = logging.getLogger(__name__)

# Global variables for imported classes and modules
Agent = None
ModelSettings = None
function_tool = None
Runner = None
AgentRunner = None
Model = None
handoff = None

def init_components():
    """Initialize all components needed for the agents SDK."""
    global Agent, ModelSettings, function_tool, Runner, AgentRunner, Model, handoff
    
    try:
        # Import agents package first
        import agents
        logger.info(f"Successfully imported agents module from {agents.__file__}")
        
        # Try multiple import paths for Agent and handoff
        try:
            # Try direct import from agents
            from agents import Agent as AgentClass
            from agents import handoff as handoff_fn
            logger.info("Successfully imported Agent and handoff directly from agents")
        except (ImportError, AttributeError) as e:
            logger.warning(f"Direct import failed: {str(e)}, trying alternative paths")
            
            # Try importing from agents.agent
            try:
                from agents.agent import Agent as AgentClass
                logger.info("Successfully imported Agent from agents.agent")
            except (ImportError, AttributeError) as e:
                logger.warning(f"agents.agent import failed: {str(e)}")
                
                # Create a stub Agent class if all imports fail
                class AgentStub:
                    def __init__(self, name, instructions, model=None, model_settings=None, tools=None, handoffs=None):
                        self.name = name
                        self.instructions = instructions
                        self.model = model
                        self.model_settings = model_settings
                        self.tools = tools or []
                        self.handoffs = handoffs or []
                
                AgentClass = AgentStub
                logger.warning("Using AgentStub as fallback")
            
            # Try importing handoff from various locations
            try:
                from agents.handoffs import handoff as handoff_fn
                logger.info("Successfully imported handoff from agents.handoffs")
            except (ImportError, AttributeError):
                try:
                    from agents.agent import handoff as handoff_fn
                    logger.info("Successfully imported handoff from agents.agent")
                except (ImportError, AttributeError):
                    # Create a stub handoff function if all imports fail
                    def handoff_stub(agent, tool_name_override=None, tool_description_override=None):
                        logger.warning("Using handoff_stub as fallback")
                        return {
                            "agent": agent,
                            "tool_name": tool_name_override or f"handoff_to_{agent.name}",
                            "tool_description": tool_description_override or f"Handoff to {agent.name}"
                        }
                    
                    handoff_fn = handoff_stub
                    logger.warning("Using handoff_stub as fallback")
        
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
        
        # Import other components
        try:
            from agents.model_settings import ModelSettings as ModelSettingsClass
            ModelSettings = ModelSettingsClass
        except ImportError:
            class ModelSettingsStub:
                def __init__(self, **kwargs):
                    self.__dict__.update(kwargs)
            ModelSettings = ModelSettingsStub
            logger.warning("Using ModelSettingsStub as fallback")
        
        try:
            from agents.tool import function_tool as function_tool_fn
            function_tool = function_tool_fn
        except ImportError:
            def function_tool_stub(fn=None, **kwargs):
                return fn
            function_tool = function_tool_stub
            logger.warning("Using function_tool_stub as fallback")
        
        # Try to import Runner or AgentRunner
        try:
            from agents.run import Runner as RunnerClass
            Runner = RunnerClass
        except ImportError:
            try:
                from agents import Runner as RunnerClass
                Runner = RunnerClass
            except ImportError:
                # If Runner is not available, try AgentRunner
                try:
                    from agents import AgentRunner as AgentRunnerClass
                    AgentRunner = AgentRunnerClass
                    Runner = AgentRunnerClass  # Use AgentRunner as a fallback for Runner
                    logger.info("Using AgentRunner as a fallback for Runner")
                except ImportError:
                    # Create a stub Runner class
                    class RunnerStub:
                        @staticmethod
                        async def run(starting_agent, input):
                            logger.warning("Using RunnerStub.run as fallback")
                            class ResultStub:
                                def __init__(self, output):
                                    self.output = output
                                    self.trace_id = None
                                    self.final_output = output
                            return ResultStub(f"Stub response from {starting_agent.name}: {input}")
                    
                    Runner = RunnerStub
                    logger.warning("Using RunnerStub as fallback")
        
        # Store the imports in our global variables
        Agent = AgentClass
        handoff = handoff_fn
        
        # Print available attributes in the agents module
        logger.info(f"Available attributes in agents module: {dir(agents)}")
        
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
    runner = Runner or AgentRunner
    if runner is None:
        success = init_components()
        if not success:
            raise ImportError("Failed to initialize SDK components")
    
    # Extract the user's message content
    if messages and len(messages) > 0 and 'content' in messages[0]:
        user_input = messages[0]['content']
    else:
        user_input = ""
    
    # Log agent details
    logger.debug(f"Creating run with agent: {agent.name}, model: {agent.model}")
    logger.debug(f"Agent has {len(agent.tools) if hasattr(agent, 'tools') and agent.tools else 0} tools")
    logger.debug(f"Agent has {len(agent.handoffs) if hasattr(agent, 'handoffs') and agent.handoffs else 0} handoffs")
    if hasattr(agent, 'handoffs') and agent.handoffs:
        for i, h in enumerate(agent.handoffs):
            logger.debug(f"Handoff {i+1}: {getattr(h, 'agent_name', 'unknown')}")
    
    # Create a wrapper object to provide compatibility with the expected interface
    class RunWrapper:
        def __init__(self, agent, user_input):
            self.agent = agent
            self.user_input = user_input
            
        async def get_final_run_result(self):
            # Run the agent using the Runner class
            try:
                logger.debug(f"Starting agent run with input: {self.user_input[:100]}...")
                result = await runner.run(
                    starting_agent=self.agent,
                    input=self.user_input
                )
                logger.debug(f"Agent run completed successfully, trace_id: {getattr(result, 'trace_id', None)}")
                return result
            except Exception as e:
                logger.error(f"Error running agent: {str(e)}", exc_info=True)
                # Return a simple error result
                class ErrorResult:
                    def __init__(self, error):
                        self.output = f"Error: {str(error)}"
                        self.trace_id = None
                        self.final_output = f"Error: {str(error)}"
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