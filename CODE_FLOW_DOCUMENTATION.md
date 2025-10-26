# Sierra Agent Code Flow Documentation

## Overview
This document describes the complete code flow of the Sierra Agent system from startup to conversation completion, including data ingestion, embeddings setup, and agent interaction flow.

## System Architecture

The Sierra Agent follows a domain-driven architecture with three main domains:
- **Orders**: Customer order tracking and lookup
- **Products**: Product catalog and recommendations with semantic search
- **Discounts**: Promotional discount validation and code generation

## Complete Code Flow

### 1. Application Startup (`cli.py`)

**Entry Point**: `python cli.py`

**Flow**:
1. **Configuration Loading**: 
   - Loads environment variables from `.env` file
   - Creates `Settings` object with OpenAI API key, model, and timeout
   - Exits with error if API key is missing

2. **Orchestrator Initialization**:
   - Creates `SierraAgentOrchestrator` instance
   - Passes settings to orchestrator constructor

3. **User Interface Setup**:
   - Displays welcome message: "🏔️ Welcome to Sierra Outfitters Customer Service! 🏔️"
   - Enters main conversation loop
   - Handles user input with `input("You: ")` prompts

### 2. Orchestrator Initialization (`agent/orchestrator.py`)

**Constructor Flow**:
1. **OpenAI Client Creation**:
   - Creates `OpenAIResponsesClient` instance
   - Passes API key, model, timeout, and retry settings
   - Sets temperature to 0.1 for consistent responses

2. **System Prompt Setup**:
   - Loads `SYSTEM_PROMPT` from `agent/prompt.py`
   - Sets system prompt in OpenAI client
   - Prompt includes brand personality, tool descriptions, and product catalog

3. **Tool Registration**:
   - Registers three function tools with the LLM:
     - `lookup_order`: Order tracking with email + order number
     - `check_promotional_discount`: Discount eligibility checking
     - `recommend_products`: Product search and recommendations
   - Each tool has JSON schema parameters and Python function implementation

### 3. Data Ingestion and Service Initialization

**Product Service Initialization** (`property/products/service.py`):
1. **JSON Data Loading**:
   - Loads `data/products.json` file
   - Creates `Product` objects for each item
   - Builds SKU index for fast lookups
   - Logs number of products loaded

2. **Embedding Strategy Setup**:
   - Checks `USE_EMBEDDINGS` flag from config
   - If spaCy available: loads `en_core_web_sm` model
   - If spaCy unavailable: falls back to keyword search
   - Sets `_use_embeddings` flag based on success

**Order Service Initialization** (`property/orders/service.py`):
1. **JSON Data Loading**:
   - Loads `data/orders.json` file
   - Creates `Order` objects for each order
   - Normalizes email (lowercase) and order numbers (uppercase with # prefix)
   - Builds lookup dictionary with (email, order_number) keys

**Discount Service Initialization** (`property/discounts/service.py`):
1. **Timezone Setup**:
   - Configures Pacific timezone for Early Risers promotion
   - Sets up time window validation (8:00 AM - 10:00 AM PT)

### 4. Message Processing Flow

**User Input Processing** (`orchestrator.process_message()`):
1. **Message Forwarding**:
   - Passes user message to OpenAI client
   - Client handles conversation state and tool calling

**OpenAI Client Processing** (`llm/openai_client.py`):
1. **Message Addition**:
   - Adds user message to conversation state
   - Maintains full conversation history

2. **Model Call Loop**:
   - Calls OpenAI API with conversation history
   - Includes system prompt, tools, and previous messages
   - Uses temperature 0.1 for consistency

3. **Tool Call Detection**:
   - Checks if model wants to call tools
   - Extracts tool calls from model response
   - If no tool calls: returns final text response

4. **Tool Execution**:
   - Executes each tool call with provided parameters
   - Captures results and errors
   - Adds tool results to conversation state
   - Continues loop until no more tool calls

### 5. Tool Execution Examples

**Order Lookup Tool** (`property/orders/tools.py`):
1. **Parameter Extraction**:
   - Extracts email and order_number from LLM call
   - Normalizes inputs (email lowercase, order number uppercase with #)

2. **Order Service Lookup**:
   - Uses singleton OrderService instance
   - Looks up order by normalized email + order number
   - Returns None if not found

3. **Product Resolution**:
   - For found orders: resolves SKUs to product names
   - Uses ProductService to get product details
   - Handles missing products gracefully

4. **Response Formatting**:
   - Returns JSON with order details
   - Includes customer name, status, products, tracking info
   - Handles error cases with appropriate messages

**Product Recommendation Tool** (`property/products/tools.py`):
1. **Query Processing**:
   - Splits query into search terms
   - Uses ProductService for search

2. **Search Strategy**:
   - If embeddings available: uses spaCy neural embeddings
   - If embeddings unavailable: falls back to keyword matching
   - Computes cosine similarity for semantic search

3. **Result Formatting**:
   - Limits to MAX_PRODUCT_RECOMMENDATIONS (5)
   - Returns JSON with product name, SKU, description
   - Handles empty results by returning all products

**Discount Check Tool** (`property/discounts/tools.py`):
1. **Request Analysis**:
   - Checks if request is explicit (mentions "Early Risers")
   - Validates current time against promotion window

2. **Time Validation**:
   - Checks if current time is between 8:00 AM - 10:00 AM PT
   - Uses Pacific timezone for validation

3. **Code Generation**:
   - If eligible: generates unique discount code
   - Format: "EARLY10-{CUSTOMER_NAME}"
   - Returns success message with code

4. **Error Handling**:
   - Returns appropriate messages for invalid times
   - Handles non-explicit requests gracefully

### 6. Conversation Example Flow

**Example: "I need hiking gear"**

1. **User Input**: "I need hiking gear"
2. **LLM Analysis**: Determines this needs product recommendations
3. **Tool Call**: `recommend_products("hiking gear")`
4. **Product Search**:
   - Splits query: ["hiking", "gear"]
   - Searches products using keyword matching or embeddings
   - Finds relevant products (backpack, outdoor gear)
5. **Tool Result**: Returns JSON with product recommendations
6. **LLM Response**: Formats response with product details and enthusiastic tone
7. **User Output**: "Get ready for your next adventure! Here are some fantastic hiking options..."

**Example: "What's my order status?"**

1. **User Input**: "What's my order status?"
2. **LLM Analysis**: Determines this needs order lookup but missing parameters
3. **LLM Response**: "I can help with that! Please provide your email and order number."
4. **User Input**: "john.doe@example.com #W001"
5. **Tool Call**: `lookup_order("john.doe@example.com", "#W001")`
6. **Order Lookup**:
   - Normalizes email: "john.doe@example.com"
   - Normalizes order: "#W001"
   - Looks up in order dictionary
   - Finds order and resolves product SKUs
7. **Tool Result**: Returns JSON with order details
8. **LLM Response**: "Great news, John! Your order #W001 has been delivered! Here's what you ordered..."

### 7. Error Handling and Fallbacks

**Embedding Fallback**:
- If spaCy model fails to load: falls back to keyword search
- If embedding computation fails: falls back to keyword search
- Logs warnings but continues operation

**Tool Execution Errors**:
- Captures exceptions in tool execution
- Returns error messages to LLM
- Continues conversation flow

**API Failures**:
- Retries OpenAI API calls with exponential backoff
- Maximum 3 retries with increasing delays
- Returns error message if all retries fail

### 8. Memory Management

**Singleton Pattern**:
- Services use singleton pattern to load data once
- ProductService, OrderService, DiscountService loaded once per session
- Prevents repeated JSON file loading

**Conversation State**:
- OpenAI client maintains full conversation history
- Includes user messages, assistant responses, tool calls, and tool results
- Enables multi-turn conversations with context

### 9. Configuration and Environment

**Environment Variables**:
- `OPENAI_API_KEY`: Required for API access
- `OPENAI_MODEL`: Model to use (default: gpt-4o-mini)
- `OPENAI_TIMEOUT`: Request timeout (default: 30 seconds)

**Logging**:
- Console-only logging (no log files)
- INFO level for normal operations
- WARNING level for fallbacks
- ERROR level for failures

### 10. Performance Optimizations

**Data Loading**:
- JSON files loaded once at startup
- In-memory dictionaries for fast lookups
- No repeated file I/O during conversations

**Embedding Caching**:
- spaCy model loaded once per session
- Embeddings computed once per product
- No repeated embedding computation

**API Efficiency**:
- Tool calling reduces API calls
- Conversation state maintained in memory
- Retry logic prevents unnecessary API calls

## Summary

The Sierra Agent system provides a robust, multi-turn conversational interface with:
- **Domain-driven architecture** for clean separation of concerns
- **Semantic search** with keyword fallback for product recommendations
- **Tool calling** for structured data access
- **Error handling** with graceful degradation
- **Memory management** with singleton services
- **Performance optimization** with in-memory caching

The system successfully handles complex multi-turn conversations while maintaining context, providing accurate information, and delivering an enthusiastic brand experience.
