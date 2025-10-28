#!/usr/bin/env python3
"""
Test script for API endpoints
"""

import requests
import json
import time

# API base URL
BASE_URL = "http://localhost:8000"  # Adjust if your API runs on a different port

def test_rag_stats():
    """Test the RAG stats endpoint"""
    print("=== Testing RAG Stats Endpoint ===")
    
    try:
        response = requests.get(f"{BASE_URL}/rag/stats")
        response.raise_for_status()
        stats = response.json()
        
        print("✓ RAG Stats retrieved successfully:")
        print(f"  - Total documents: {stats.get('total_documents', 0)}")
        print(f"  - Total chunks: {stats.get('total_chunks', 0)}")
        print(f"  - Unique sources: {stats.get('unique_sources', 0)}")
        
        if stats.get('sources'):
            print("  - Sources:")
            for source in stats['sources'][:5]:  # Show first 5 sources
                print(f"    • {source}")
            if len(stats['sources']) > 5:
                print(f"    ... and {len(stats['sources']) - 5} more")
        
        return True
    except Exception as e:
        print(f"✗ Error testing RAG stats: {e}")
        return False

def test_chat_with_rag():
    """Test the chat endpoint with RAG"""
    print("\n=== Testing Chat Endpoint with RAG ===")
    
    test_messages = [
        {
            "messages": [
                {"text": "What are the underwriting guidelines for life insurance?", "isUser": True}
            ],
            "context": {}
        },
        {
            "messages": [
                {"text": "Tell me about home insurance coverage", "isUser": True}
            ],
            "context": {}
        }
    ]
    
    for i, test_data in enumerate(test_messages, 1):
        print(f"\nTest {i}: {test_data['messages'][0]['text']}")
        
        try:
            response = requests.post(
                f"{BASE_URL}/chat",
                json=test_data,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            result = response.json()
            
            print("✓ Response received:")
            print(f"  Text: {result['text'][:200]}..." if len(result['text']) > 200 else f"  Text: {result['text']}")
            
            if result.get('followUpOptions'):
                print("  Follow-up options:")
                for option in result['followUpOptions']:
                    print(f"    • {option}")
            
            # Check if the response mentions retrieved documents
            if "according to" in result['text'].lower() or "based on" in result['text'].lower():
                print("  ✓ Response appears to use RAG context")
            
        except Exception as e:
            print(f"✗ Error testing chat: {e}")

def test_index_endpoint():
    """Test the index endpoint"""
    print("\n=== Testing Index Endpoint ===")
    
    try:
        # Test indexing without reindex
        response = requests.post(
            f"{BASE_URL}/rag/index",
            json={"reindex": False},
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        result = response.json()
        
        print("✓ Index endpoint called successfully:")
        print(f"  Status: {result['status']}")
        print(f"  Message: {result['message']}")
        
        if result.get('stats'):
            print(f"  Stats: Success={result['stats']['success']}, Failed={result['stats']['failed']}, Skipped={result['stats']['skipped']}")
        
        return True
    except Exception as e:
        print(f"✗ Error testing index endpoint: {e}")
        return False

def main():
    """Run all tests"""
    print("Starting API tests...\n")
    
    # Wait a moment for the server to be ready
    print("Waiting for server to be ready...")
    time.sleep(2)
    
    # Run tests
    test_rag_stats()
    test_chat_with_rag()
    # test_index_endpoint()  # Uncomment to test indexing
    
    print("\n=== API Tests Complete ===")

if __name__ == "__main__":
    main()