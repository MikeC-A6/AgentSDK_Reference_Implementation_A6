# Custom agents module - separate from the OpenAI agents SDK
# This is to prevent circular imports

# Import the agent classes when they're requested, but not at the module level
# This breaks the circular import chain
__all__ = ['BaseAgent', 'PlannerAgent', 'WebSearchAgent']

# These will be populated when they're first imported
BaseAgent = None
PlannerAgent = None
WebSearchAgent = None

def __getattr__(name):
    """Lazy loading of agent classes to avoid circular imports."""
    if name == 'BaseAgent':
        from .base_agent import BaseAgent as _BaseAgent
        globals()['BaseAgent'] = _BaseAgent
        return _BaseAgent
    elif name == 'PlannerAgent':
        from .planner_agent import PlannerAgent as _PlannerAgent
        globals()['PlannerAgent'] = _PlannerAgent
        return _PlannerAgent
    elif name == 'WebSearchAgent':
        from .web_search_agent import WebSearchAgent as _WebSearchAgent
        globals()['WebSearchAgent'] = _WebSearchAgent
        return _WebSearchAgent
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
