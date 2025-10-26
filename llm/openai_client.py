import json
import time
import logging
from typing import Any, Callable, Dict, List, Optional

from openai import OpenAI
from config import Settings

logger = logging.getLogger(__name__)

ToolFn = Callable[..., Any]

class OpenAIResponsesClient:
    """
    Chat client for OpenAI LLMs using the Responses API with native tool calling support.
    - Keeps conversation state (history + tool calls)
    - Exposes local Python functions as "function tools"
    """
    def __init__(self, settings: Settings):
        self.client = OpenAI(api_key=settings.openai_api_key, timeout=settings.openai_timeout)
        self.model = settings.openai_model
        self.timeout = settings.openai_timeout
        self.max_retries = 3
        self.base_delay = 1.0
        self.temperature = 0.1

        # Conversation state: includes messages, function calls, and function outputs
        self._state: List[Dict[str, Any]] = []

        # System prompt (uses 'instructions' in Responses API)
        self._instructions: str = ""

        # Registered tools
        self._tools: List[Dict[str, Any]] = []
        self._tool_registry: Dict[str, ToolFn] = {}

    def set_system_prompt(self, instructions: str) -> None:
        """Set system-level behavior/policies for the model."""
        self._instructions = instructions

    def reset(self) -> None:
        """Clear conversation history (but keep registered tools and system prompt)."""
        self._state = []

    def register_function_tool(
        self,
        *,
        name: str,
        description: str,
        parameters: Dict[str, Any],
        func: ToolFn,
        strict: bool = True,
    ) -> None:
        """
        Register a JSON-schema function tool and its Python implementation.
        The `parameters` dict is a JSON Schema for the tool's arguments.
        """
        tool = {
            "type": "function",
            "function": {
                "name": name,
                "description": description,
                "parameters": parameters,
            }
        }
        self._tools.append(tool)
        self._tool_registry[name] = func

    def send(self, user_message: str) -> str:
        """
        Send a message and return the assistant's final text after executing any tool calls.
        Conversation history is preserved in self._state.
        """
        # Add the new user turn to the running state
        self._state.append({"role": "user", "content": user_message})

        # Keep calling the model until there are no more tool calls to fulfill
        last_response = None
        while True:
            last_response = self._call_model(self._state)
            # Always append the model's output items back into the state
            self._state.extend(last_response)

            # Check if there are any tool calls to execute
            tool_calls = []
            for item in last_response:
                if item.get("role") == "assistant" and "tool_calls" in item:
                    tool_calls.extend(item["tool_calls"])

            if not tool_calls:
                # No more tool calls, return the final text response
                break

            # Execute the tool calls and add results to state
            tool_results = self._execute_tools(tool_calls)
            self._state.extend(tool_results)

        # Extract the final text response
        for item in reversed(last_response):
            if item.get("role") == "assistant" and "content" in item:
                return item["content"]

        return "I'm sorry, I couldn't process your request properly."

    def _call_model(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Call the OpenAI model with retry logic."""
        for attempt in range(self.max_retries):
            try:
                # Add system prompt as first message if not already present
                call_messages = messages.copy()
                if self._instructions and (not call_messages or call_messages[0].get("role") != "system"):
                    call_messages.insert(0, {"role": "system", "content": self._instructions})
                
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=call_messages,
                    tools=self._tools if self._tools else None,
                    tool_choice="auto" if self._tools else None,
                    temperature=self.temperature,
                )

                # Convert response to our expected format
                result = []
                for choice in response.choices:
                    message = {"role": "assistant", "content": choice.message.content}
                    if choice.message.tool_calls:
                        message["tool_calls"] = [
                            {
                                "id": call.id,
                                "type": "function",
                                "function": {
                                    "name": call.function.name,
                                    "arguments": call.function.arguments,
                                },
                            }
                            for call in choice.message.tool_calls
                        ]
                    result.append(message)

                return result

            except Exception as e:
                logger.warning(f"OpenAI API call failed (attempt {attempt + 1}/{self.max_retries}): {e}")
                if attempt < self.max_retries - 1:
                    delay = self.base_delay * (2 ** attempt)
                    time.sleep(delay)
                else:
                    raise

    def _execute_tools(self, tool_calls: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Execute tool calls and return results."""
        results = []
        
        for tool_call in tool_calls:
            tool_id = tool_call["id"]
            function_name = tool_call["function"]["name"]
            function_args = json.loads(tool_call["function"]["arguments"])
            
            try:
                # Get the registered function
                if function_name not in self._tool_registry:
                    error_msg = f"Tool '{function_name}' not found"
                    logger.error(error_msg)
                    result = {"role": "tool", "tool_call_id": tool_id, "content": error_msg}
                else:
                    # Execute the function
                    func = self._tool_registry[function_name]
                    result_value = func(**function_args)
                    
                    # Format result as JSON string
                    if isinstance(result_value, str):
                        result_content = result_value
                    else:
                        result_content = json.dumps(result_value)
                    
                    result = {
                        "role": "tool",
                        "tool_call_id": tool_id,
                        "content": result_content
                    }
                    
            except Exception as e:
                error_msg = f"Error executing tool '{function_name}': {str(e)}"
                logger.error(error_msg)
                result = {"role": "tool", "tool_call_id": tool_id, "content": error_msg}
            
            results.append(result)
        
        return results
