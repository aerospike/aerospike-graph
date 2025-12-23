#!/usr/bin/env python3
"""
Phase 1: Test connectivity to Aerospike Graph and Ollama

Run this to verify your setup before proceeding.
"""

import sys
import requests
from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection
from gremlin_python.process.anonymous_traversal import traversal

import config


def test_aerospike_graph():
    """Test connection to Aerospike Graph via Gremlin"""
    print("\n" + "=" * 50)
    print("Testing Aerospike Graph Connection...")
    print("=" * 50)
    
    try:
        # Connect to Aerospike Graph
        connection_string = f"ws://{config.GRAPH_HOST}:{config.GRAPH_PORT}/gremlin"
        print(f"Connecting to: {connection_string}")
        
        connection = DriverRemoteConnection(connection_string, "g")
        g = traversal().withRemote(connection)
        
        # Simple test: count vertices
        vertex_count = g.V().count().next()
        print(f"✅ Connected! Current vertex count: {vertex_count}")
        
        # Test: create and delete a test vertex
        print("Testing write operations...")
        test_vertex = g.addV("TestVertex").property("name", "connection_test").next()
        print(f"✅ Created test vertex: {test_vertex}")
        
        # Clean up - use toList() for compatibility with older TinkerPop versions
        g.V().has("TestVertex", "name", "connection_test").drop().toList()
        print("✅ Deleted test vertex")
        
        connection.close()
        print("✅ Aerospike Graph connection successful!\n")
        return True
        
    except Exception as e:
        print(f"❌ Aerospike Graph connection failed: {e}")
        print("\nTroubleshooting:")
        print(f"  1. Is Aerospike Graph running at {config.GRAPH_HOST}:{config.GRAPH_PORT}?")
        print("  2. Check with: docker ps | grep aerospike")
        print("  3. Check logs: docker logs <container_id>")
        return False


def test_ollama():
    """Test connection to Ollama"""
    print("\n" + "=" * 50)
    print("Testing Ollama Connection...")
    print("=" * 50)
    
    try:
        # Check if Ollama is running
        print(f"Connecting to: {config.OLLAMA_BASE_URL}")
        response = requests.get(f"{config.OLLAMA_BASE_URL}/api/tags", timeout=5)
        response.raise_for_status()
        
        models = response.json().get("models", [])
        model_names = [m["name"] for m in models]
        print(f"✅ Ollama is running. Available models: {model_names}")
        
        # Check if required models are available
        required_models = [config.OLLAMA_MODEL, config.OLLAMA_EMBED_MODEL]
        missing_models = []
        
        for model in required_models:
            # Check with and without :latest suffix
            if model not in model_names and f"{model}:latest" not in model_names:
                # Try partial match (e.g., "llama3.2" matches "llama3.2:latest")
                if not any(m.startswith(model) for m in model_names):
                    missing_models.append(model)
        
        if missing_models:
            print(f"\n⚠️  Missing required models: {missing_models}")
            print("Install them with:")
            for model in missing_models:
                print(f"  ollama pull {model}")
            return False
        
        # Test generation with the LLM model
        print(f"\nTesting {config.OLLAMA_MODEL} generation...")
        response = requests.post(
            f"{config.OLLAMA_BASE_URL}/api/generate",
            json={
                "model": config.OLLAMA_MODEL,
                "prompt": "Say 'Hello Graph RAG' in exactly 3 words.",
                "stream": False
            },
            timeout=60
        )
        response.raise_for_status()
        result = response.json()["response"]
        print(f"✅ LLM response: {result.strip()}")
        
        # Test embeddings
        print(f"\nTesting {config.OLLAMA_EMBED_MODEL} embeddings...")
        response = requests.post(
            f"{config.OLLAMA_BASE_URL}/api/embeddings",
            json={
                "model": config.OLLAMA_EMBED_MODEL,
                "prompt": "Test embedding"
            },
            timeout=60
        )
        response.raise_for_status()
        embedding = response.json()["embedding"]
        print(f"✅ Embedding dimension: {len(embedding)}")
        
        if len(embedding) != config.EMBEDDING_DIMENSION:
            print(f"⚠️  Warning: Expected {config.EMBEDDING_DIMENSION} dimensions, got {len(embedding)}")
            print(f"   Update EMBEDDING_DIMENSION in config.py")
        
        print("\n✅ Ollama connection successful!\n")
        return True
        
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to Ollama at {config.OLLAMA_BASE_URL}")
        print("\nTroubleshooting:")
        print("  1. Is Ollama running? Start with: ollama serve")
        print("  2. Check if it's on a different port")
        return False
    except Exception as e:
        print(f"❌ Ollama test failed: {e}")
        return False


def main():
    print("\n" + "=" * 50)
    print("   GRAPH RAG DEMO - CONNECTIVITY TEST")
    print("=" * 50)
    
    graph_ok = test_aerospike_graph()
    ollama_ok = test_ollama()
    
    print("\n" + "=" * 50)
    print("   SUMMARY")
    print("=" * 50)
    print(f"Aerospike Graph: {'✅ OK' if graph_ok else '❌ FAILED'}")
    print(f"Ollama:          {'✅ OK' if ollama_ok else '❌ FAILED'}")
    
    if graph_ok and ollama_ok:
        print("\n🎉 All systems ready! Proceed to Phase 2.")
        return 0
    else:
        print("\n⚠️  Fix the issues above before proceeding.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

