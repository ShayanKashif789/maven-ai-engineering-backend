#!/usr/bin/env python3
"""
Test script for MultiAgents4 API endpoints
Run this script to test the API endpoints after starting the FastAPI server
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000/api"

def test_health_check():
    """Test basic health check"""
    print("🔍 Testing health check...")
    response = requests.get(f"{BASE_URL}/../")
    if response.status_code == 200:
        print("✅ Health check passed")
        return True
    else:
        print(f"❌ Health check failed: {response.status_code}")
        return False

def test_multi_agent_status():
    """Test multi-agent system status"""
    print("\n🔍 Testing multi-agent status...")
    response = requests.get(f"{BASE_URL}/multi-agent/status")
    if response.status_code == 200:
        print("✅ Status check passed")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return True
    else:
        print(f"❌ Status check failed: {response.status_code}")
        return False

def test_research_only():
    """Test research-only endpoint"""
    print("\n🔍 Testing research-only endpoint...")
    
    request_data = {
        "query": "What are the latest developments in artificial intelligence?",
        "async_execution": False
    }
    
    response = requests.post(
        f"{BASE_URL}/multi-agent/research-only",
        json=request_data
    )
    
    if response.status_code == 200:
        print("✅ Research-only test passed")
        result = response.json()
        print(f"Intent: {result.get('intent')}")
        print(f"Research Required: {result.get('research_required')}")
        print(f"Research Source: {result.get('research_source')}")
        print(f"Final Output Length: {len(result.get('final_output', ''))}")
        return True
    else:
        print(f"❌ Research-only test failed: {response.status_code}")
        print(f"Error: {response.text}")
        return False

def test_linkedin_post():
    """Test LinkedIn post generation"""
    print("\n🔍 Testing LinkedIn post generation...")
    
    request_data = {
        "query": "Write a professional LinkedIn post about the importance of continuous learning in tech",
        "async_execution": False
    }
    
    response = requests.post(
        f"{BASE_URL}/multi-agent",
        json=request_data
    )
    
    if response.status_code == 200:
        print("✅ LinkedIn post generation test passed")
        result = response.json()
        print(f"Intent: {result.get('intent')}")
        print(f"Target Team: {result.get('target_team')}")
        print(f"Tone: {result.get('tone')}")
        print(f"Target Format: {result.get('target_format')}")
        print(f"Final Output:\n{result.get('final_output', '')}")
        return True
    else:
        print(f"❌ LinkedIn post generation test failed: {response.status_code}")
        print(f"Error: {response.text}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting MultiAgents4 API Tests")
    print("=" * 50)
    
    tests = [
        test_health_check,
        test_multi_agent_status,
        test_research_only,
        test_linkedin_post
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            time.sleep(1)  # Brief pause between tests
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The API is working correctly.")
    else:
        print("⚠️  Some tests failed. Please check the server logs.")

if __name__ == "__main__":
    main()
