"""
Mercari AI Shopping Agent

This agent works with OpenAI's GPT models including GPT-4o via GitHub Models.
It uses OpenAI's function calling API for tool execution.
"""

from openai import OpenAI
import os
import json
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from tools_openai import TOOLS_OPENAI, execute_tool


class MercariAgentOpenAI:
    """
    AI Agent for shopping on Mercari Japan using OpenAI's function calling capabilities.
    """
    
    def __init__(
        self, 
        api_key: Optional[str] = None, 
        model: str = "gpt-4.1", #We could change to any other gpt models
        base_url: Optional[str] = None
    ):
        """
        Initialize the Mercari AI Agent with OpenAI.
        
        Args:
            api_key: OpenAI API key or GitHub token (if not provided, will use OPENAI_API_KEY or GITHUB_TOKEN env var)
            model: Model to use (default: gpt-4.1)
            base_url: Base URL for API (use "https://models.inference.ai.azure.com" for GitHub Models)
        
        For GitHub Models (free):
            1. Get token from https://github.com/settings/tokens
            2. Set base_url="https://models.inference.ai.azure.com"
            3. Use model="gpt-4.1"
        """
        # Try to get API key from environment
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY") or os.environ.get("GITHUB_TOKEN")
        if not self.api_key:
            raise ValueError(
                "API key must be provided or set in OPENAI_API_KEY or GITHUB_TOKEN environment variable.\n"
                "For GitHub Models: Get token from https://github.com/settings/tokens"
            )
        
        # Initialize OpenAI client
        client_kwargs = {"api_key": self.api_key}
        if base_url:
            client_kwargs["base_url"] = base_url
        
        self.client = OpenAI(**client_kwargs)
        self.model = model
        self.conversation_history = []
        
        self.system_message = {
            "role": "system",
            "content": """
            You are a helpful AI shopping assistant for Mercari Japan, a popular online marketplace in Japan.

            IMPORTANT - ACTION-FIRST APPROACH:
            When a user asks to find something, DO NOT ask clarifying questions first. Instead:
            1. Immediately search using reasonable defaults based on their request
            2. Translate English keywords to Japanese if needed (e.g., "toys" → "おもちゃ")
            3. Use the search_mercari function right away
            4. Analyze results with analyze_products to get top 3 recommendations
            5. Present the recommendations in this EXACT format:

            [Product Name](Product URL)
            - Price: ¥X,XXX
            - Condition: [condition]
            - Why recommended: [List each reason from the 'reasons' array on a new line]

            6. ALWAYS include the 'reasons' from the analyze_products results - these explain WHY each product is a good match
            7. THEN at the END, offer to refine the search with follow-up questions about:
            - Specific types, brands, or features
            - Condition preferences (new vs used)
            - Price range adjustments

            Be proactive and helpful. Don't overthink - just search first, show results with clear reasoning, then offer to refine.
            Always provide product URLs so users can view items on Mercari."""
        }
    
    def chat(self, user_message: str) -> str:
        """
        Process a user message and return the agent's response.
        
        Args:
            user_message: The user's message/request
        
        Returns:
            The agent's response
        """
        # Add user message to conversation history
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })
        
        # Start the agentic loop
        response = self._agentic_loop()
        
        # Add assistant response to conversation history
        self.conversation_history.append({
            "role": "assistant",
            "content": response
        })
        
        return response
    
    def _agentic_loop(self, max_iterations: int = 10) -> str:
        """
        Execute the agentic loop with function calling.
        
        Args:
            max_iterations: Maximum number of iterations to prevent infinite loops
        
        Returns:
            Final response to the user
        """
        iteration = 0
        
        # Prepare messages with system message
        messages = [self.system_message] + self.conversation_history
        
        while iteration < max_iterations:
            iteration += 1
            
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=TOOLS_OPENAI,
                tool_choice="auto"
            )
            
            response_message = response.choices[0].message
            
            # Check if we need to process function calls
            if response_message.tool_calls:
                # Add assistant's response to messages
                messages.append(response_message)
                
                # Process all function calls
                for tool_call in response_message.tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)
                    
                    print(f"[Agent] Using function: {function_name}")
                    print(f"[Agent] Function input: {json.dumps(function_args, indent=2, ensure_ascii=False)}")
                    
                    # Execute the function
                    function_result = execute_tool(function_name, function_args)
                    
                    print(f"[Agent] Function result: {json.dumps(function_result, indent=2, ensure_ascii=False)[:500]}...")
                    
                    # Add function result to messages
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": function_name,
                        "content": json.dumps(function_result, ensure_ascii=False)
                    })
                
                # Continue loop to get next response
                continue
            
            else:
                # No more function calls, return the final response
                return response_message.content or "I apologize, but I couldn't generate a response."
        
        return "I apologize, but I've reached the maximum number of processing steps. Please try simplifying your request."
    
    def reset_conversation(self):
        """Reset the conversation history."""
        self.conversation_history = []
        print("[Agent] Conversation history reset.")


def format_recommendation(recommendation: Dict) -> str:
    """
    Format a single recommendation for display.
    
    Args:
        recommendation: Recommendation dictionary
    
    Returns:
        Formatted string
    """
    product = recommendation['product']
    rank = recommendation['rank']
    reasons = recommendation['reasons']
    
    output = f"\n{'='*60}\n"
    output += f"RECOMMENDATION #{rank}\n"
    output += f"{'='*60}\n"
    output += f"Product: {product.get('name', 'Unknown')}\n"
    output += f"Price: {product.get('price_display', 'N/A')}\n"
    output += f"Condition: {product.get('condition', 'Not specified')}\n"
    output += f"URL: {product.get('url', 'N/A')}\n"
    output += f"\nWhy this recommendation:\n"
    for i, reason in enumerate(reasons, 1):
        output += f"  {i}. {reason}\n"
    
    if product.get('is_sold'):
        output += f"\n⚠️  Note: This item is marked as SOLD\n"
    
    return output


def main():
    """
    Main function to run the agent interactively.
    """
    print("="*60)
    print("Mercari Japan AI Shopping Agent (OpenAI Version)")
    print("="*60)
    print("\nWelcome! I can help you find products on Mercari Japan.")
    print("Tell me what you're looking for, and I'll search and recommend the best options.\n")
    
    # Check for GitHub Models setup
    github_token = os.environ.get("GITHUB_TOKEN")
    openai_key = os.environ.get("OPENAI_API_KEY")
    
    if github_token:
        print("🎉 Using GitHub Models (free GPT-4o)")
        print("   Base URL: https://models.inference.ai.azure.com\n")
    elif openai_key:
        print("Using OpenAI API\n")
    
    print("Type 'quit' or 'exit' to end the session.")
    print("Type 'reset' to start a new conversation.\n")
    
    # Initialize agent
    try:
        # Try GitHub Models first, then fall back to OpenAI
        if github_token:
            agent = MercariAgentOpenAI(
                api_key=github_token,
                base_url="https://models.inference.ai.azure.com",
                model="gpt-4o"
            )
        else:
            agent = MercariAgentOpenAI()
    except ValueError as e:
        print(f"Error: {e}")
        print("\nSetup options:")
        print("\n1. GitHub Models (FREE):")
        print("   - Get token from: https://github.com/settings/tokens")
        print("   - Set: export GITHUB_TOKEN='your-github-token'")
        print("\n2. OpenAI:")
        print("   - Get API key from: https://platform.openai.com/api-keys")
        print("   - Set: export OPENAI_API_KEY='your-openai-key'")
        return
    
    # Interactive loop
    while True:
        try:
            user_input = input("You: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ['quit', 'exit']:
                print("\nThank you for using Mercari AI Shopping Agent. Goodbye!")
                break
            
            if user_input.lower() == 'reset':
                agent.reset_conversation()
                print("\nConversation reset. What would you like to find?\n")
                continue
            
            # Get agent response
            print("\n[Agent is thinking...]\n")
            response = agent.chat(user_input)
            
            print(f"Agent: {response}\n")
        
        except KeyboardInterrupt:
            print("\n\nSession interrupted. Goodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}")
            print("Please try again.\n")


if __name__ == "__main__":
    main()
