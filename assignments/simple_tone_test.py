#!/usr/bin/env python3
"""
Simple tone detection test without external dependencies
"""

import re
from typing import Tuple

# Copy the relevant functions from writing_supervisor.py
_WORD_RE = re.compile(r"[a-z0-9']+")

_TONE_KEYWORDS = {
    "professional": "PROFESSIONAL",
    "formal": "PROFESSIONAL",
    "casual": "CONVERSATIONAL",
    "conversational": "CONVERSATIONAL",
    "opinionated": "OPINIONATED",
    "hot take": "OPINIONATED",
    "story": "STORYTELLING",
    "storytelling": "STORYTELLING",
    "educational": "EDUCATIONAL",
    "teach": "EDUCATIONAL",
    "explainer": "EDUCATIONAL",
    "threatening": "THREATENING",
    "threat": "THREATENING",
    "warning": "THREATENING",
    "urgent": "THREATENING",
}

def _normalize(text: str) -> str:
    return " ".join(_WORD_RE.findall(text.lower().strip()))

def _score_signals(text: str) -> Tuple[str, float]:
    """Simplified version of tone scoring"""
    normalized = _normalize(text)
    tone_scores = {
        "PROFESSIONAL": 0.0,
        "CONVERSATIONAL": 0.0,
        "OPINIONATED": 0.0,
        "STORYTELLING": 0.0,
        "EDUCATIONAL": 0.0,
        "THREATENING": 0.0,
    }

    for phrase, tone in _TONE_KEYWORDS.items():
        if phrase in normalized:
            tone_scores[tone] += 1.0 if " " in phrase else 0.6

    tone = max(tone_scores, key=tone_scores.get)
    confidence = tone_scores[tone]
    
    return tone, confidence

def test_tone_detection():
    """Test tone detection with various queries"""
    
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
    print("=" * 70)
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{i}. Query: \"{query}\"")
        print("-" * 50)
        
        tone, confidence = _score_signals(query)
        print(f"   📝 Detected Tone: {tone}")
        print(f"   📊 Confidence Score: {confidence:.2f}")
        
        if confidence == 0.0:
            print(f"   ⚠️  No tone keywords detected - would use default PROFESSIONAL")
        elif confidence >= 1.0:
            print(f"   ✅ Strong tone signal detected")
        else:
            print(f"   🔍 Moderate tone signal detected")
    
    print("\n" + "=" * 70)
    print("📊 SUMMARY:")
    
    # Count detected tones
    tone_counts = {}
    for query in test_queries:
        tone, _ = _score_signals(query)
        tone_counts[tone] = tone_counts.get(tone, 0) + 1
    
    print(f"   Total queries tested: {len(test_queries)}")
    for tone, count in sorted(tone_counts.items()):
        print(f"   {tone}: {count} queries")
    
    print("\n🎉 Test completed!")

if __name__ == "__main__":
    test_tone_detection()
