#!/usr/bin/env python3
"""
Test the specific query that was having issues
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the scoring function
from MultiAgents4.agents.writing_supervisor import _score_signals

def test_specific_query():
    """Test the specific query that was having issues"""
    
    query = "write a threatening post about ai replacing developers in future"
    
    print("🎯 TESTING SPECIFIC QUERY")
    print("=" * 50)
    print(f"Query: {query}")
    print("-" * 50)
    
    # Test the scoring
    tone, post_type, confidence, tone_nonzero, post_nonzero = _score_signals(query)
    
    print(f"🔍 Detected Tone: {tone}")
    print(f"📊 Confidence Score: {confidence:.2f}")
    print(f"🎯 Post Type: {post_type}")
    print(f"🔢 Tone Signals Found: {tone_nonzero}")
    print(f"🔢 Post Signals Found: {post_nonzero}")
    print("-" * 50)
    
    if confidence >= 0.55:
        print(f"✅ CONFIDENCE ABOVE THRESHOLD (0.55)")
        print(f"✅ FINAL TONE: {tone}")
    else:
        print(f"⚠️  CONFIDENCE BELOW THRESHOLD (0.55)")
        print(f"⚠️  Would trigger LLM fallback")
    
    print("=" * 50)

if __name__ == "__main__":
    test_specific_query()
