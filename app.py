import os
import logging
from flask import Flask, render_template, request, jsonify
import json
from openai import OpenAI

# Import our local tools and config
from tools.web_search import WebSearchTool
from tools.calculator import CalculatorTool
from config import Config

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev_key")

# Initialize OpenAI client
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# Create tools
web_search_tool = WebSearchTool()
calculator_tool = CalculatorTool()

# Helper function to convert our tool to OpenAI function
def convert_tool_to_function(tool):
    """Convert our tool to an OpenAI function definition."""
    return {
        "type": "function",
        "function": {
            "name": tool.name(),
            "description": tool.description(),
            "parameters": {
                "type": "object",
                "properties": {
                    "input": {
                        "type": "string",
                        "description": f"Input for {tool.name()}"
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
    
    try:
        # Build the agent
        agent = planner_agent.build()
        
        # Run the agent synchronously (convert async to sync)
        result = asyncio.run(Runner.run(agent, user_input))
        
        # Return the agent's response
        return jsonify({
            'response': result.final_output,
            'trace_id': getattr(result, 'trace_id', None)
        })
        
    except Exception as e:
        logging.error(f"Error running agent: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/about')
def about():
    """Render the about page with information about the agent system."""
    tools = [
        {
            'name': web_search_tool.name,
            'description': web_search_tool.description
        },
        {
            'name': calculator_tool.name,
            'description': calculator_tool.description
        }
    ]
    
    return render_template('about.html', tools=tools, model=Config.DEFAULT_MODEL)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
