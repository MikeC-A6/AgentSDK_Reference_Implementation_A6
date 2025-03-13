import os
from typing import Dict, Any

class Config:
    """Configuration for the agent system."""
    
    # OpenAI API settings
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    
    # Agent settings
    DEFAULT_MODEL = "o3-mini"  # Using o3-mini as requested
    DEFAULT_REASONING_EFFORT = "medium"  # Medium reasoning effort
    
    # Web search settings
    SEARCH_RESULT_COUNT = 5
    SEARCH_TIMEOUT = 10  # Timeout in seconds
    
    # Tracing settings
    ENABLE_TRACING = True
    TRACE_WORKFLOW_NAME = "Agent with Planning and Search"

    @classmethod
    def get_model_settings(cls) -> Dict[str, Any]:
        """Returns model settings dictionary."""
        return {
            "reasoning": {"effort": cls.DEFAULT_REASONING_EFFORT}
        }
