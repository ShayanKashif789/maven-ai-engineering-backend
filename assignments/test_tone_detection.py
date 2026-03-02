#!/usr/bin/env python3
"""
Test script to verify tone detection in MultiAgents4
This script tests the tone detection logic without requiring the full system to run
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from MultiAgents4.agents.writing_supervisor import _score_signals, _llm_fallback_writer_classifier
from MultiAgents4.state.writing_supervisor import WritingState

def test_tone_detection():
    """Test tone detection with various sample queries"""
    
    test_queries = [
        # Professional tone examples
        "Write a professional post about industry trends",
        "Create a formal announcement about our company",
        
        # Conversational tone examples  
        "Share a casual update about my weekend",
        "Write something conversational about team building",
        
        # Opinionated tone examples
        "Give me a hot take on remote work",
        "Write an opinionated post about AI ethics",
        
        # Storytelling tone examples
        "Tell a story about my career journey",
        "Create a storytelling post about overcoming challenges",
        
        # Educational tone examples
        "Teach others about machine learning basics",
        "Write an educational post about blockchain technology",
        
        # Threatening tone examples (NEW!)
        "Write a threatening post about cybersecurity risks",
        "Create a warning about data privacy concerns",
        "Share an urgent message about industry changes",
        "Post about competitive threats in our market",
        
        # Ambiguous examples
        "Write a post about technology",
        "Create content about business",
    ]
    
    print("🎯 TONE DETECTION TEST RESULTS")
    print("=" * 60)
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{i}. Query: \"{query}\"")
        print("-" * 50)
        
        # Test rule-based detection
        try:
            tone, post_type, confidence, tone_nonzero, post_nonzero = _score_signals(query)
            print(f"   Rule-based Detection:")
            print(f"   📝 Tone: {tone}")
            print(f"   📊 Post Type: {post_type}")
            print(f"   🎯 Confidence: {confidence:.2f}")
            print(f"   🔢 Tone Signals: {tone_nonzero}")
            print(f"   🔢 Post Signals: {post_nonzero}")
        except Exception as e:
            print(f"   ❌ Rule-based error: {e}")
        
        # Test LLM fallback (only if confidence is low or for demonstration)
        try:
            llm_tone, llm_post_type, llm_format = _llm_fallback_writer_classifier(query)
            print(f"   LLM Fallback:")
            print(f"   🤖 Tone: {llm_tone}")
            print(f"   🤖 Post Type: {llm_post_type}")
            print(f"   🤖 Format: {llm_format}")
        except Exception as e:
            print(f"   ❌ LLM fallback error: {e}")
    
    print("\n" + "=" * 60)
    print("✅ Test completed!")
    
    # Test the WritingState validation
    print("\n🔍 Testing WritingState validation...")
    try:
        # Test all valid tones
        valid_tones = ["PROFESSIONAL", "CONVERSATIONAL", "OPINIONATED", "STORYTELLING", "EDUCATIONAL", "THREATENING"]
        for tone in valid_tones:
            state = WritingState(tone=tone)
            print(f"   ✅ {tone}: Valid")
    except Exception as e:
        print(f"   ❌ WritingState validation error: {e}")

if __name__ == "__main__":
    test_tone_detection()
