import sys
print("Python path:")
for path in sys.path:
    print(f"  {path}")

try:
    import agents
    print("\nAgents module found!")
    print(f"Agents module path: {agents.__file__}")
    print(f"Agents module contents: {dir(agents)}")
    
    # Check for submodules
    print("\nChecking for submodules:")
    for item in dir(agents):
        if not item.startswith('__'):
            try:
                module = getattr(agents, item)
                if hasattr(module, '__file__'):
                    print(f"Submodule: {item} at {module.__file__}")
                    print(f"Contents: {dir(module)}")
            except Exception as e:
                print(f"Error inspecting {item}: {e}")
    
    # Try to find Agent class
    print("\nLooking for Agent class:")
    try:
        from agents.agent import Agent
        print(f"Found Agent in agents.agent: {Agent}")
    except ImportError as e:
        print(f"Failed to import Agent from agents.agent: {e}")
    
    try:
        from agents import Agent
        print(f"Found Agent directly in agents: {Agent}")
    except ImportError as e:
        print(f"Failed to import Agent directly from agents: {e}")
    
    # Try to find handoff function
    print("\nLooking for handoff function:")
    try:
        from agents import handoff
        print(f"Found handoff directly in agents: {handoff}")
    except ImportError as e:
        print(f"Failed to import handoff directly from agents: {e}")
    
    try:
        from agents.handoffs import handoff
        print(f"Found handoff in agents.handoffs: {handoff}")
    except ImportError as e:
        print(f"Failed to import handoff from agents.handoffs: {e}")
    
    # Try to find Runner
    print("\nLooking for Runner:")
    try:
        from agents.run import Runner
        print(f"Found Runner in agents.run: {Runner}")
    except ImportError as e:
        print(f"Failed to import Runner from agents.run: {e}")
    
    try:
        from agents import Runner
        print(f"Found Runner directly in agents: {Runner}")
    except ImportError as e:
        print(f"Failed to import Runner directly from agents: {e}")
    
    try:
        from agents import AgentRunner
        print(f"Found AgentRunner directly in agents: {AgentRunner}")
    except ImportError as e:
        print(f"Failed to import AgentRunner directly from agents: {e}")
    
except ImportError as e:
    print(f"\nFailed to import agents module: {e}")

# Check if the package is installed
print("\nChecking installed packages:")
try:
    import pkg_resources
    for package in pkg_resources.working_set:
        if 'agent' in package.key.lower() or 'openai' in package.key.lower():
            print(f"  {package.key} {package.version}")
except Exception as e:
    print(f"Error checking packages: {e}") 