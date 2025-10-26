#!/usr/bin/env python3

import sys
from config import Settings, setup_logging
from agent.orchestrator import SierraAgentOrchestrator

WELCOME_MESSAGE = "🏔️  Welcome to Sierra Outfitters Customer Service! 🏔️"
EXIT_MESSAGE = "\n\nThanks for choosing Sierra Outfitters! Onward into the unknown! 🏔️"

def main():
    #setup_logging()
    
    try:
        settings = Settings.from_env()
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        print("Please create a .env file with your OPENAI_API_KEY")
        return 1
    
    # Initialize the orchestrator
    orchestrator = SierraAgentOrchestrator(settings)
    
    print(WELCOME_MESSAGE)
    print("Type 'exit' or 'quit' to end the conversation, or Ctrl+C to quit.\n")
    
    try:
        while True:
            try:
                user_input = input("You: ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() in ['exit', 'quit']:
                    print(EXIT_MESSAGE)
                    break
                
                # Process message with the orchestrator (handles LLM + tools)
                response = orchestrator.process_message(user_input)
                
                print(f"\nSierra Agent: {response}\n")
                
            except KeyboardInterrupt:
                print(EXIT_MESSAGE)
                break
            except EOFError:
                # Handle case when input is piped and runs out
                print(EXIT_MESSAGE)
                break
            except Exception as e:
                print(f"\n❌ Sorry, I encountered an error: {e}")
                print("Let's try again!\n")
                
    except KeyboardInterrupt:
        print(EXIT_MESSAGE)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
