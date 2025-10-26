# Sierra Agent - Customer Service Chatbot

Multi-turn CLI chatbot for Sierra Outfitters with OpenAI function calling for order tracking, product recommendations, and promotional discounts.

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment:**
   ```bash
   cp env.example .env
   # Edit .env and add your OPENAI_API_KEY
   ```

3. **Run the agent:**
   ```bash
   python cli.py
   ```

## Architecture & Design Decisions

### Domain-Driven Design
- **property/orders/**: Order lookup with email+order_number indexing
- **property/products/**: Keyword-based product search (no embeddings)
- **property/discounts/**: Time-window validation for Early Risers promo

### Why These Design Decisions?

**Keyword Matching Over Embeddings:**
- Avoids OpenAI embedding dependencies and heavy model downloads
- Works offline with simple string matching
- Evaluator can run with just `pip install -r requirements.txt`

**Singleton Services:**
- JSON data loaded once at startup, shared across tool calls
- Prevents repeated file I/O and improves performance
- Memory-efficient for multi-turn conversations

**OpenAI Function Calling:**
- LLM automatically selects appropriate tools based on user intent
- No manual intent classification needed
- Natural conversation flow with tool execution

**Neutral Response Design:**
- No oversharing of promotion restrictions or time windows
- Professional customer service boundaries
- Matches sierra-outfitters-agent approach

### Core Components

- **agent/**: Conversation orchestration with OpenAI function calling
- **llm/**: OpenAI client with tool execution and conversation state
- **property/**: Domain services (orders, products, discounts)
- **cli.py**: Multi-turn REPL interface
- **data/**: JSON files for orders and products

## Features

- **Multi-Turn Conversation**: CLI chatbot with conversation memory
- **Order Tracking**: Email + order number lookup with tracking URLs
- **Product Recommendations**: Keyword-based product search with SKU resolution
- **Promotional Discounts**: Early Risers discount with time window validation
- **Brand Personality**: Enthusiastic, outdoorsy tone with mountain emojis

## Optional: Neural Embeddings with spaCy

For better search quality, the system uses neural embeddings with spaCy:

```bash
pip install spacy
python -m spacy download en_core_web_sm
```

This will:
- Load the en_core_web_sm model (12MB) for neural embeddings
- Provide semantic search (understands "hiking" ≈ "trekking" ≈ "backpack")
- Much more powerful than TF-IDF or keyword matching
- No torch dependencies or compatibility issues

If spaCy is not installed, the system automatically falls back to keyword matching.

## Testing

```bash
python -m pytest tests/ -v
```

The test suite provides comprehensive coverage with zero external dependencies.