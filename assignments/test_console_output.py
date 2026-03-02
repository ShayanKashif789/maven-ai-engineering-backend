#!/usr/bin/env python3
"""
Test script to demonstrate console output for tone detection
This simulates the multi-agent flow without requiring the full system
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Mock the dependencies that might not be available
class MockLLM:
    def invoke(self, messages):
        class MockResponse:
            content = '{"tone": "PROFESSIONAL", "post_type": "TECHNICAL_EXPLAINER", "target_format": "single_post"}'
        return MockResponse()

def mock_get_llm():
    return MockLLM()

# Mock the langchain imports
sys.modules['langchain_core'] = type(sys)('langchain_core')
sys.modules['langchain_core.messages'] = type(sys)('langchain_core.messages')
sys.modules['langchain_core.messages'].SystemMessage = lambda content: {"role": "system", "content": content}
sys.modules['langchain_core.messages'].HumanMessage = lambda content: {"role": "human", "content": content}

# Mock the llm_factory
sys.modules['assignments.AgenticQASystem3'] = type(sys)('assignments.AgenticQASystem3')
sys.modules['assignments.AgenticQASystem3.core'] = type(sys)('assignments.AgenticQASystem3.core')
sys.modules['assignments.AgenticQASystem3.core.llm_factory'] = type(sys)('assignments.AgenticQASystem3.core.llm_factory')
sys.modules['assignments.AgenticQASystem3.core.llm_factory'].get_llm = mock_get_llm

# Now import our modules
from MultiAgents4.agents.meta_supervisor import meta_supervisor_node
from MultiAgents4.agents.writing_supervisor import writing_supervisor_node
from MultiAgents4.graph.graph import build_initial_state

def test_console_output():
    """Test console output with different queries"""
    
    test_queries = [
        "Write a threatening post about cybersecurity risks",
        "Create a professional announcement about our new product",
        "Share a casual story about my career journey",
        "Teach others about machine learning basics",
        "Give me a hot take on remote work policies",
        "Write an educational post about blockchain technology",
    ]
    
    print("🧪 CONSOLE OUTPUT TEST FOR TONE DETECTION")
    print("=" * 80)
    print("This test will show the console output that appears during multi-agent processing")
    print("=" * 80)
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n🔥 TEST CASE {i}: {query}")
        print("🔥" * 80)
        
        # Build initial state
        state = build_initial_state(query)
        
        # Run meta supervisor (will show intent detection)
        print("\n--- META SUPERVISOR ---")
        state = meta_supervisor_node(state)
        
        # Only run writing supervisor if intent is linkedin_post
        if state.get("intent") == "linkedin_post":
            print("\n--- WRITING SUPERVISOR ---")
            state = writing_supervisor_node(state)
            print(f"\n🎉 FINAL TONE: {state.get('tone')}")
        else:
            print(f"\n⚠️  Intent was '{state.get('intent')}', skipping tone detection")
        
        print("\n" + "=" * 80)
    
    print("\n✅ All tests completed!")
    print("💡 When you run the actual multi-agent API, you'll see similar console output")

if __name__ == "__main__":
    test_console_output()
