"""
Mercari AI Shopping Agent

This agent works with OpenAI's GPT models including GPT-4.1 via GitHub Models.
It uses OpenAI's function calling API for tool execution.
"""

from openai import OpenAI
import os
import json
import logging
from typing import Dict, Any, Optional, Generator
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)

# Load environment variables from .env file
load_dotenv()

from tools import TOOLS_OPENAI, execute_tool


class MercariAgentOpenAI:
    """
    AI Agent for shopping on Mercari Japan using OpenAI's function calling capabilities.
    """
    
    def __init__(
        self, 
        api_key: Optional[str] = None, 
        model: str = "gpt-4.1",
        base_url: Optional[str] = None
    ):
        """
        Initialize the Mercari AI Agent with OpenAI.
        
        Args:
            api_key: OpenAI API key or GitHub token (defaults to OPENAI_API_KEY or GITHUB_TOKEN env var)
            model: Model to use (default: gpt-4.1)
            base_url: Base URL for API (use "https://models.inference.ai.azure.com" for GitHub Models)
        """
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
            You are a helpful AI shopping assistant for Mercari Japan.

            IMPORTANT - ACTION-FIRST APPROACH:
            When a user asks to find something, DO NOT ask clarifying questions first. Instead:
            1. Immediately search using reasonable defaults based on their request
            2. Translate English keywords to Japanese if needed (e.g., "toys" → "おもちゃ")
            3. Use the search_mercari function right away
            4. Analyze results with analyze_products to get top 3 recommendations
            5. Present recommendations in this format:

            [Product Name](Product URL)
            - Price: ¥X,XXX
            - Condition: [condition]
            - Why recommended: [reasons]

            6. ALWAYS include the 'reasons' from analyze_products results
            7. At the END, offer to refine the search with follow-up questions

            Be proactive. Search first, show results with reasoning, then offer to refine.
            Always provide product URLs so users can view items on Mercari."""
        }
    
    def chat(self, user_message: str) -> str:
        """Process a user message and return the agent's response."""
        self.conversation_history.append({"role": "user", "content": user_message})
        response = self._run_agent_loop(stream=False)
        self.conversation_history.append({"role": "assistant", "content": response})
        return response
    
    def chat_stream(self, user_message: str) -> Generator[str, None, None]:
        """Process a user message and stream the agent's response."""
        self.conversation_history.append({"role": "user", "content": user_message})
        
        full_response = ""
        for chunk in self._run_agent_loop(stream=True):
            full_response += chunk
            yield chunk
        
        self.conversation_history.append({"role": "assistant", "content": full_response})
    
    def _run_agent_loop(self, stream: bool = False, max_iterations: int = 10):
        """
        Execute the agentic loop with function calling.
        
        Args:
            stream: If True, yields chunks; if False, returns full response string
            max_iterations: Maximum iterations to prevent infinite loops
        """
        messages = [self.system_message] + self.conversation_history
        
        for _ in range(max_iterations):
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=TOOLS_OPENAI,
                tool_choice="auto"
            )
            
            response_message = response.choices[0].message
            
            # Process function calls if any
            if response_message.tool_calls:
                messages.append(response_message)
                
                for tool_call in response_message.tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)
                    
                    logging.info(f"Using function: {function_name}")
                    logging.info(f"Function input: {json.dumps(function_args, indent=2, ensure_ascii=False)}")
                    
                    function_result = execute_tool(function_name, function_args)
                    
                    logging.info(f"Function result: {json.dumps(function_result, indent=2, ensure_ascii=False)[:500]}...")
                    
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": function_name,
                        "content": json.dumps(function_result, ensure_ascii=False)
                    })
                continue
            
            # No more function calls return final response
            if stream:
                # Streaming for final response
                stream_response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    stream=True
                )
                for chunk in stream_response:
                    if chunk.choices and len(chunk.choices) > 0 and chunk.choices[0].delta.content:
                        yield chunk.choices[0].delta.content
                return
            else:
                return response_message.content or "I apologize, but I couldn't generate a response."
        
        error_msg = "I apologize, but I've reached the maximum number of processing steps."
        if stream:
            yield error_msg
        else:
            return error_msg
    
    def reset_conversation(self):
        """Reset the conversation history."""
        self.conversation_history = []
        logging.info("Conversation history reset.")


def main():
    """Main function to run the agent interactively."""
    print("=" * 60)
    print("Mercari Japan AI Shopping Agent")
    print("=" * 60)
    print("\nWelcome! I can help you find products on Mercari Japan.")
    print("Tell me what you're looking for, and I'll search and recommend the best options.\n")
    
    github_token = os.environ.get("GITHUB_TOKEN")
    openai_key = os.environ.get("OPENAI_API_KEY")
    
    if github_token:
        print("Using GitHub Models (free GPT-4.1)\n")
    elif openai_key:
        print("Using OpenAI API\n")
    
    print("Type 'quit' to exit, 'reset' to start a new conversation.\n")
    
    # Initialize agent
    try:
        if github_token:
            agent = MercariAgentOpenAI(
                api_key=github_token,
                base_url="https://models.inference.ai.azure.com",
                model="gpt-4.1"
            )
        else:
            agent = MercariAgentOpenAI()
    except ValueError as e:
        print(f"Error: {e}")
        print("\nSetup: Set GITHUB_TOKEN or OPENAI_API_KEY environment variable.")
        return
    
    # Interactive loop
    while True:
        try:
            user_input = input("You: ").strip()
            
            if not user_input:
                continue
            if user_input.lower() in ['quit', 'exit']:
                print("\nGoodbye!")
                break
            if user_input.lower() == 'reset':
                agent.reset_conversation()
                print("\nConversation reset.\n")
                continue
            
            # Stream response
            print("\nAgent: ", end="", flush=True)
            for chunk in agent.chat_stream(user_input):
                print(chunk, end="", flush=True)
            print("\n")
        
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            logging.error(f"Error: {e}")
            print("Please try again.\n")


if __name__ == "__main__":
    main()
