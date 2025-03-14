import os
import logging
import asyncio
import concurrent.futures
import time
from flask import Flask, render_template, request, jsonify, session
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
from tools.calculator import CalculatorTool
from config import Config

# Import our agent wrapper module
import agent_wrapper

# Global variables for agent components
planner_agent = None
# Create a global event loop for async operations
loop = None
# Create a thread pool executor for running async tasks with timeouts
executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)

def get_event_loop():
    """Get or create an event loop for async operations."""
    global loop
    if loop is None or loop.is_closed():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop

def run_async_with_timeout(coro, timeout=25):
    """Run an async coroutine with a timeout."""
    loop = get_event_loop()
    
    # Create a future that will be set when the coroutine completes
    future = asyncio.run_coroutine_threadsafe(coro, loop)
    
    try:
        # Wait for the future to complete with a timeout
        return future.result(timeout)
    except concurrent.futures.TimeoutError:
        # If the coroutine times out, cancel it and raise a timeout error
        future.cancel()
        raise TimeoutError(f"Operation timed out after {timeout} seconds")

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
        
        # Import our agents
        from custom_agents.planner_agent import PlannerAgent
        
        # Create our tools
        calculator_tool = CalculatorTool()
        
        # Create the planner agent with calculator tool and web search handoff enabled
        planner_agent_instance = PlannerAgent(
            tools=[calculator_tool],
            enable_web_search=True
        )
        planner_agent = planner_agent_instance
        
        logger.info("Successfully initialized PlannerAgent with tools and web search handoff capability")
        return True
        
    except ImportError as e:
        logger.error(f"Failed to import Agent SDK: {str(e)}")
        return False

# Helper function to convert our tool to OpenAI function
def convert_tool_to_function(tool):
    """Convert our tool to an OpenAI function definition."""
    # Use the tool's parameter_schema if available
    if hasattr(tool, 'parameter_schema'):
        parameters = tool.parameter_schema
    else:
        # Default schema if not provided
        parameters = {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string", 
                    "description": f"Input for {tool.name}"
                }
            },
            "required": ["expression"]
        }
    
    return {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description,
            "parameters": parameters
        }
    }

@app.route('/')
def index():
    """Render the main page."""
    return render_template('index.html')

@app.route('/ask', methods=['POST'])
def ask():
    """Handle user queries to the agent with a single agent session."""
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
            model_settings_factory=agent_wrapper.get_model_settings
        )
        
        logger.debug(f"Agent built successfully with handoffs: {getattr(agent, 'handoffs', None)}")
        
        # Create a modified prompt that asks for a plan first, then execution
        modified_prompt = f"""
        For the following task: {user_input}
        
        First, I'll create a clear plan to address this request, then provide a comprehensive response.
        
        Please format your response in two distinct sections:
        
        1. "## Plan"
        A concise, bulleted list of steps you'll take to answer this question. Keep it brief and focused.
        If the task involves any calculations, explicitly mention that you'll use the calculator tool.
        
        2. "## Response"
        Your complete, well-structured answer to the question. Include all relevant information, citations, 
        and supporting details here. Make this section comprehensive and directly useful to the user.
        
        Important instructions:
        - For ANY mathematical calculations, use the 'calculate' tool rather than doing the math yourself.
        - When using the calculator tool, show both the expression you're calculating and the result.
        - Do not include "Execution" steps or numbered execution points in your response.
        - Simply provide the final, polished answer in the Response section.
        """
        
        # Run the agent with the modified prompt
        run = agent_wrapper.create_run(
            agent=agent,
            messages=[
                {
                    "role": "user",
                    "content": modified_prompt
                }
            ]
        )
        
        # Start a background task to get the result with a timeout
        try:
            # Get the final result with a timeout
            start_time = time.time()
            logger.debug(f"Starting agent run at {start_time}")
            
            # Use our timeout function to prevent hanging
            result = run_async_with_timeout(run.get_final_run_result(), timeout=25)
            
            end_time = time.time()
            logger.debug(f"Agent run completed in {end_time - start_time:.2f} seconds")
            
            # Parse the result to separate plan and execution
            response_text = result.final_output
            
            # Extract plan and execution sections
            plan = ""
            execution = ""
            
            if "## Plan" in response_text and "## Response" in response_text:
                parts = response_text.split("## Response")
                if len(parts) >= 2:
                    plan_section = parts[0]
                    plan = plan_section.replace("## Plan", "").strip()
                    execution = parts[1].strip()
            else:
                # If the format wasn't followed, make a best guess
                plan = "The agent will search for information about your query and provide a comprehensive response with citations."
                execution = response_text
            
            # Return both the plan and the execution result
            return jsonify({
                'plan': plan,
                'response': execution,
                'trace_id': getattr(result, 'trace_id', None),
                'full_response': response_text
            })
            
        except TimeoutError as e:
            logger.error(f"Agent run timed out: {str(e)}")
            return jsonify({
                'error': 'The request took too long to process. Please try a simpler query or try again later.',
                'timeout': True
            }), 408
        
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

# Initialize the event loop in a background thread
def init_event_loop():
    global loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_forever()

# Start the event loop in a background thread
import threading
loop_thread = threading.Thread(target=init_event_loop, daemon=True)
loop_thread.start()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
