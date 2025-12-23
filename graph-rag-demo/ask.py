#!/usr/bin/env python3
"""
Phase 4: Simple Q&A CLI

Ask questions about your documents using RAG.

Usage:
    python ask.py "What is Graph RAG?"
    python ask.py  # Interactive mode
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from chat.qa_chain import QAChain


def print_result(result):
    """Pretty print a Q&A result"""
    print("\n" + "=" * 60)
    print("💬 ANSWER")
    print("=" * 60)
    print(result.answer)
    
    print("\n" + "-" * 60)
    print(f"📚 SOURCES ({len(result.sources)} chunks)")
    print("-" * 60)
    for i, source in enumerate(result.sources):
        score = source['distance']
        doc = source['doc_id']
        pos = source['position']
        text_preview = source['text'][:80].replace('\n', ' ') + "..."
        print(f"  {i+1}. [{score:.3f}] {doc} (chunk {pos})")
        print(f"     {text_preview}")
    print()


def interactive_mode():
    """Run interactive Q&A session"""
    print("\n" + "=" * 60)
    print("   📚 GRAPH RAG Q&A")
    print("   Type 'quit' to exit")
    print("=" * 60)
    
    with QAChain() as qa:
        while True:
            try:
                question = input("\n❓ Question: ").strip()
            except (KeyboardInterrupt, EOFError):
                print("\nGoodbye!")
                break
            
            if question.lower() in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break
            
            if not question:
                continue
            
            print("\n⏳ Thinking...")
            result = qa.ask(question, verbose=False)
            print_result(result)


def single_question(question: str):
    """Answer a single question"""
    print(f"\n❓ Question: {question}")
    print("⏳ Thinking...")
    
    with QAChain() as qa:
        result = qa.ask(question, verbose=False)
        print_result(result)


def main():
    if len(sys.argv) > 1:
        # Single question mode
        question = " ".join(sys.argv[1:])
        single_question(question)
    else:
        # Interactive mode
        interactive_mode()


if __name__ == "__main__":
    main()

