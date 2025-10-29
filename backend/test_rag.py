#!/usr/bin/env python3
"""
Test script for RAG functionality
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from rag_utils import RAGManager
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_rag():
    """Test the RAG manager functionality"""
    
    print("=== Testing RAG Manager ===\n")
    
    # Initialize RAG Manager
    print("1. Initializing RAG Manager...")
    rag_manager = RAGManager(s3_bucket_name="pptbalbucket")
    print("✓ RAG Manager initialized\n")
    
    # Get current stats
    print("2. Getting current statistics...")
    stats = rag_manager.get_stats()
    print(f"✓ Total documents indexed: {stats['total_documents']}")
    print(f"✓ Total chunks: {stats['total_chunks']}")
    print(f"✓ Unique sources: {stats['unique_sources']}\n")
    
    # Test search functionality
    print("3. Testing search functionality...")
    test_queries = [
        "What are the transaction dispute procedures?",
        "How do I increase my credit limit?",
        "What rewards program benefits are available?",
        "How do I report a lost or stolen card?"
    ]
    
    for query in test_queries:
        print(f"\nQuery: '{query}'")
        results = rag_manager.search(query, k=2)
        
        if results:
            print(f"Found {len(results)} relevant documents:")
            for i, result in enumerate(results, 1):
                print(f"  {i}. Source: {result['source']}")
                print(f"     Score: {result['score']:.3f}")
                print(f"     Preview: {result['content'][:100]}...")
        else:
            print("  No relevant documents found")
    
    # Test context generation
    print("\n\n4. Testing context generation for prompts...")
    test_prompt = "What documents are needed to file a transaction dispute?"
    context = rag_manager.get_context_for_prompt(test_prompt, k=3)
    
    if context:
        print(f"Generated context for: '{test_prompt}'")
        print("-" * 50)
        print(context[:500] + "..." if len(context) > 500 else context)
        print("-" * 50)
    else:
        print("No context generated (no relevant documents found)")
    
    print("\n=== RAG Manager Test Complete ===")

if __name__ == "__main__":
    test_rag()