import urllib.request
import urllib.parse
import json
import ssl
from typing import List, Dict, Any, Optional
import logging

from tools.base_tool import BaseTool
from config import Config

class WebSearchTool(BaseTool):
    """Tool for searching the web."""
    
    @property
    def name(self) -> str:
        return "web_search"
    
    @property
    def description(self) -> str:
        return "Search the web for information. Provide a search query to get results."
    
    def execute(self, query: str) -> str:
        """
        Execute a web search for the given query.
        
        Args:
            query: The search query string
            
        Returns:
            A string containing the search results
        """
        logging.info(f"Executing web search for query: {query}")
        try:
            # Create a safe context for HTTPS connections
            context = ssl._create_unverified_context()
            
            # URL encode the query
            encoded_query = urllib.parse.quote(query)
            
            # Use a simple search API (this is a mockup - in reality you'd use a proper search API)
            url = f"https://ddg-api.herokuapp.com/search?query={encoded_query}&limit={Config.SEARCH_RESULT_COUNT}"
            
            # Send the request
            with urllib.request.urlopen(url, context=context, timeout=Config.SEARCH_TIMEOUT) as response:
                response_data = response.read().decode('utf-8')
                
            # Parse the response
            results = json.loads(response_data)
            
            # Format the results
            formatted_results = self._format_results(results)
            return formatted_results
            
        except Exception as e:
            logging.error(f"Error in web search: {str(e)}")
            return f"Error performing web search: {str(e)}"
    
    def _format_results(self, results: List[Dict[str, Any]]) -> str:
        """Format the search results for the agent."""
        formatted = "Web search results:\n\n"
        
        if not results:
            return formatted + "No results found."
        
        for i, result in enumerate(results, 1):
            title = result.get('title', 'No title')
            url = result.get('link', 'No link')
            snippet = result.get('snippet', 'No description available')
            
            formatted += f"{i}. {title}\n"
            formatted += f"   URL: {url}\n"
            formatted += f"   Description: {snippet}\n\n"
        
        return formatted
