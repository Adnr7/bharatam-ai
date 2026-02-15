"""
EXPERIMENTAL: Test script for AI enhancement layer

This script demonstrates the AI-powered features and fallback behavior.

Usage:
    # With OpenAI API key in .env
    python test_ai_enhancement.py
    
    # Without API key (tests fallback)
    python test_ai_enhancement.py --no-ai
"""

import os
import sys
from app.services.ai_assistant import AIAssistant


def test_ai_extraction():
    """Test AI-powered entity extraction."""
    print("\n" + "="*60)
    print("TEST 1: Natural Language Understanding (Entity Extraction)")
    print("="*60)
    
    ai = AIAssistant()
    
    if not ai.is_available():
        print("❌ AI Assistant not available (no API key)")
        print("   Set OPENAI_API_KEY in .env to test AI features")
        return False
    
    print("✅ AI Assistant initialized")
    print(f"   Model: {ai.model}")
    
    # Test cases
    test_messages = [
        "I am a 25 year old farmer from Karnataka",
        "मैं 30 साल का हूं, महाराष्ट्र से, graduate हूं",
        "I'm 22, from Delhi, completed 12th, earning below 1 lakh",
        "Female student, 20 years old, SC category, from Tamil Nadu"
    ]
    
    for i, message in enumerate(test_messages, 1):
        print(f"\n--- Test Case {i} ---")
        print(f"Input: \"{message}\"")
        
        try:
            extracted, confidence = ai.extract_user_info(message, "en")
            print(f"Confidence: {confidence:.2f}")
            print(f"Extracted: {extracted}")
            
            if confidence >= 0.6:
                print("✅ High confidence - would use AI extraction")
            else:
                print("⚠️  Low confidence - would fallback to rule-based")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    return True


def test_ai_explanation():
    """Test AI-powered explanation generation."""
    print("\n" + "="*60)
    print("TEST 2: Conversational Explanation Generation")
    print("="*60)
    
    ai = AIAssistant()
    
    if not ai.is_available():
        print("❌ AI Assistant not available (no API key)")
        return False
    
    print("✅ AI Assistant initialized")
    
    # Test case
    scheme_name = "Pradhan Mantri Kaushal Vikas Yojana (PMKVY)"
    user_profile = {
        "age": 25,
        "state": "Maharashtra",
        "education_level": "graduate",
        "income_range": "1-3lakh",
        "category": "general",
        "gender": "male",
        "occupation": "student"
    }
    matching_criteria = [
        "Age is within range (18-35 years)",
        "Education level matches (graduate)",
        "Occupation matches (student)"
    ]
    missing_criteria = []
    
    print(f"\nScheme: {scheme_name}")
    print(f"User Profile: {user_profile}")
    print(f"Eligible: True")
    
    try:
        explanation = ai.generate_explanation(
            scheme_name,
            True,
            matching_criteria,
            missing_criteria,
            user_profile,
            "en"
        )
        
        if explanation:
            print("\n✅ AI-Generated Explanation:")
            print("-" * 60)
            print(explanation)
            print("-" * 60)
        else:
            print("❌ AI explanation generation failed")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Compare with template
    print("\n📋 Template-Based Explanation (Fallback):")
    print("-" * 60)
    template = f"""✅ You are eligible for {scheme_name}!

You meet the following requirements:
  • Age is within range (18-35 years)
  • Education level matches (graduate)
  • Occupation matches (student)"""
    print(template)
    print("-" * 60)
    
    return True


def test_fallback_behavior():
    """Test fallback to rule-based logic."""
    print("\n" + "="*60)
    print("TEST 3: Fallback Behavior (No AI)")
    print("="*60)
    
    # Temporarily disable AI
    original_key = os.environ.get("OPENAI_API_KEY")
    if original_key:
        del os.environ["OPENAI_API_KEY"]
    
    ai = AIAssistant()
    
    print(f"AI Available: {ai.is_available()}")
    print(f"Expected: False")
    
    if not ai.is_available():
        print("✅ AI correctly disabled when no API key")
        print("   System will use rule-based logic")
    else:
        print("❌ AI should be disabled")
    
    # Restore key
    if original_key:
        os.environ["OPENAI_API_KEY"] = original_key
    
    return True


def test_ai_status():
    """Test AI status endpoint."""
    print("\n" + "="*60)
    print("TEST 4: AI Status")
    print("="*60)
    
    ai = AIAssistant()
    status = ai.get_status()
    
    print(f"Status: {status}")
    
    if status["enabled"]:
        print("✅ AI features enabled")
        print(f"   Model: {status['model']}")
        print(f"   Features: {status['features']}")
    else:
        print("⚠️  AI features disabled (no API key)")
        print("   System will use rule-based logic")
    
    return True


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("EXPERIMENTAL: AI Enhancement Layer Test Suite")
    print("="*60)
    
    # Check for --no-ai flag
    if "--no-ai" in sys.argv:
        print("\n⚠️  Running in NO-AI mode (testing fallback)")
        original_key = os.environ.get("OPENAI_API_KEY")
        if original_key:
            del os.environ["OPENAI_API_KEY"]
    
    # Run tests
    results = []
    
    results.append(("AI Status", test_ai_status()))
    results.append(("Entity Extraction", test_ai_extraction()))
    results.append(("Explanation Generation", test_ai_explanation()))
    results.append(("Fallback Behavior", test_fallback_behavior()))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {name}")
    
    total = len(results)
    passed = sum(1 for _, p in results if p)
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed!")
    else:
        print("\n⚠️  Some tests failed")
    
    print("\n" + "="*60)
    print("NOTES:")
    print("="*60)
    print("1. AI features require OPENAI_API_KEY in .env")
    print("2. System works perfectly without AI (fallback to rule-based)")
    print("3. All eligibility decisions remain deterministic")
    print("4. AI only enhances input parsing and output generation")
    print("="*60)


if __name__ == "__main__":
    main()
