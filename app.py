import os
import logging
import asyncio
from flask import Flask, render_template, request, jsonify
import json
from openai import OpenAI

# Configure logging first
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev_key")

# Check for OpenAI API key
if not os.environ.get("OPENAI_API_KEY"):
    logger.warning("OPENAI_API_KEY not found in environment variables. Some features may not work.")

# Initialize OpenAI client
openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# Import our local tools and config
from tools.web_search import WebSearchTool
from tools.calculator import CalculatorTool
from config import Config

# Import our agent wrapper module
import agent_wrapper

# Global variables for agent components
planner_agent = None

# Initialize agent components
def init_agent_components():
    """Initialize agent components with proper imports."""
    global planner_agent
    
    try:
        # Check if agent wrapper initialized correctly
        if not agent_wrapper.Agent:
            logger.error("Agent wrapper failed to initialize")
            return False
        
        # Log successful import
        logger.info("Successfully imported Agent SDK")
        
        # Now import our planner agent and create an instance
        from custom_agents.planner_agent import PlannerAgent
        
        # Create our tools
        web_search_tool = WebSearchTool()
        calculator_tool = CalculatorTool()
        
        # Create the planner agent with our tools
        planner_agent_instance = PlannerAgent(tools=[web_search_tool, calculator_tool])
        planner_agent = planner_agent_instance
        
        logger.info("Successfully initialized PlannerAgent with tools")
        return True
        
    except ImportError as e:
        logger.error(f"Failed to import Agent SDK: {str(e)}")
        return False

# Helper function to convert our tool to OpenAI function
def convert_tool_to_function(tool):
    """Convert our tool to an OpenAI function definition."""
    return {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "input": {
                        "type": "string",
                        "description": f"Input for {tool.name}"
                    }
                },
                "required": ["input"]
            }
        }
    }

@app.route('/')
def index():
    """Render the main page."""
    return render_template('index.html')

@app.route('/ask', methods=['POST'])
def ask():
    """Handle user queries to the agent."""
    user_input = request.json.get('query', '')
    
    if not user_input:
        return jsonify({'error': 'Empty query'}), 400
    
    # Initialize agent components if not already done
    if planner_agent is None:
        success = init_agent_components()
        if not success:
            return jsonify({'error': 'Failed to initialize agent components'}), 500
    
    try:
        # Build the agent with required factories
        agent = planner_agent.build(
            agent_factory=agent_wrapper.Agent,
            function_tool_factory=agent_wrapper.function_tool,
            model_settings_factory=agent_wrapper.ModelSettings
        )
        
        logger.debug(f"Agent built successfully: {agent}")
        
        # Run the agent with the user input
        run = agent_wrapper.create_run(
            agent=agent,
            messages=[
                {
                    "role": "user",
                    "content": user_input
                }
            ]
        )
        result = asyncio.run(run.get_final_run_result())
        
        # Return the agent's response
        return jsonify({
            'response': result.output,
            'trace_id': getattr(result, 'trace_id', None)
        })
        
    except Exception as e:
        logger.error(f"Error running agent: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/about')
def about():
    """Render the about page with information about the agent system."""
    # Initialize agent components if not already done
    if planner_agent is None:
        init_agent_components()
    
    # Get tools from planner agent if available
    tools = []
    if planner_agent and hasattr(planner_agent, 'tools'):
        for tool in planner_agent.tools:
            tools.append({
                'name': tool.name,
                'description': tool.description
            })
    
    return render_template('about.html', tools=tools, model=Config.DEFAULT_MODEL)

# Initialize agent components when the module is loaded
init_agent_components()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
