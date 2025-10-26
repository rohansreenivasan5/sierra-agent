"""
Main orchestrator that handles customer conversations using LLM with function calling.
"""
import logging
from config import Settings
from llm.openai_client import OpenAIResponsesClient
from agent.prompt import SYSTEM_PROMPT
from property.orders.tools import lookup_order
from property.discounts.tools import check_promotional_discount
from property.products.tools import recommend_products, MAX_PRODUCT_RECOMMENDATIONS

logger = logging.getLogger(__name__)

class SierraAgentOrchestrator:
    """
    Main orchestrator that handles customer conversations using LLM with function calling.
    """
    
    def __init__(self, settings: Settings):
        # Initialize the OpenAI client with function calling support
        self.client = OpenAIResponsesClient(settings)
        
        # Set the system prompt
        self.client.set_system_prompt(SYSTEM_PROMPT)
        
        # Register our tools with the LLM
        self._register_tools()
        
    def _register_tools(self):
        """Register tools with the LLM."""
        
        # Tool 1: Order lookup
        self.client.register_function_tool(
            name="lookup_order",
            description="Look up customer order status and tracking information using email and order number.",
            parameters={
                "type": "object",
                "properties": {
                    "email": {
                        "type": "string",
                        "description": "Customer's email address"
                    },
                    "order_number": {
                        "type": "string", 
                        "description": "Order number (with # prefix, like #W001)"
                    }
                },
                "required": ["email", "order_number"],
                "additionalProperties": False
            },
            func=lookup_order,
            strict=True
        )
        
        # Tool 2: Promotional discount check
        self.client.register_function_tool(
            name="check_promotional_discount",
            description="Check for promotional discount eligibility based on customer request and timing constraints.",
            parameters={
                "type": "object",
                "properties": {
                    "request_text": {
                        "type": "string",
                        "description": "The customer's exact words requesting a promotional discount."
                    }
                },
                "required": ["request_text"],
                "additionalProperties": False
            },
            func=check_promotional_discount,
            strict=True
        )
        
        # Tool 3: Product recommendations
        self.client.register_function_tool(
            name="recommend_products", 
            description=f"Search for and recommend various products based on any and all customer needs and interests. Returns up to {MAX_PRODUCT_RECOMMENDATIONS} product recommendations.",
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query describing what the customer is looking for (e.g., 'hiking backpack', 'cold weather gear', 'waterproof jacket'). Include multiple keywords or terms if searching broadly."
                    }
                },
                "required": ["query"],
                "additionalProperties": False
            },
            func=recommend_products,
            strict=True
        )
        
        logger.info("Registered tools with Sierra Agent: lookup_order, check_promotional_discount, recommend_products")
    
    def process_message(self, user_message: str) -> str:
        """
        Process a user message and return the agent's response.
        The LLM will decide which tools to call based on the conversation context.
        """
        try:
            response = self.client.send(user_message)
            return response
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return "🏔️ Sorry, I encountered an error processing your request. Please try again! Onward into the unknown!"
    
    def reset_conversation(self):
        """Clear conversation history while keeping tools and system prompt."""
        self.client.reset()
        logger.info("Conversation history reset")
