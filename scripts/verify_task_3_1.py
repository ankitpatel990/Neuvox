"""
Verification Script for Task 3.1: Language Detection

This script verifies all acceptance criteria:
- AC-1.1.1: Hindi detection >95% accuracy
- AC-1.1.2: English detection >98% accuracy
- AC-1.1.3: Handles Hinglish without errors
- AC-1.1.4: Returns result within 100ms
"""

import time
import sys
sys.path.insert(0, '.')

from app.models.language import detect_language, LanguageDetector


def verify_hindi_accuracy():
    """AC-1.1.1: Hindi detection >95% accuracy"""
    hindi_tests = [
        "आप जीत गए हैं",
        "आपका खाता ब्लॉक हो जाएगा",
        "तुरंत पैसे भेजें",
        "यह बैंक से आधिकारिक संदेश है",
        "आप गिरफ्तार हो जाएंगे",
        "पुलिस आपको ढूंढ रही है",
        "जुर्माना भरें",
        "नमस्ते कैसे हैं आप",
        "आज का मौसम अच्छा है",
        "कल मिलते हैं",
    ]
    
    correct = sum(1 for t in hindi_tests if detect_language(t)[0] == "hi")
    accuracy = correct / len(hindi_tests)
    passed = accuracy >= 0.95
    
    return {
        "id": "AC-1.1.1",
        "description": "Hindi detection >95% accuracy",
        "accuracy": accuracy,
        "correct": correct,
        "total": len(hindi_tests),
        "passed": passed,
    }


def verify_english_accuracy():
    """AC-1.1.2: English detection >98% accuracy"""
    english_tests = [
        "You won 10 lakh rupees!",
        "Congratulations! You have been selected.",
        "Send your OTP immediately to claim the prize.",
        "Your bank account will be blocked.",
        "This is urgent! Call now.",
        "Hello, how are you today?",
        "Lets meet for coffee tomorrow.",
        "Your order has been shipped.",
        "Please verify your account details.",
        "Thank you for your payment.",
        "The meeting is scheduled for 3 PM.",
        "Please send me the document.",
        "Have a great day!",
        "I will call you back later.",
        "The weather is nice today.",
    ]
    
    correct = sum(1 for t in english_tests if detect_language(t)[0] == "en")
    accuracy = correct / len(english_tests)
    passed = accuracy >= 0.98
    
    return {
        "id": "AC-1.1.2",
        "description": "English detection >98% accuracy",
        "accuracy": accuracy,
        "correct": correct,
        "total": len(english_tests),
        "passed": passed,
    }


def verify_hinglish_handling():
    """AC-1.1.3: Handles Hinglish without errors"""
    hinglish_tests = [
        "Aapne jeeta hai 10 lakh",
        "Bhai ये देखो urgent है",
        "Please करो payment जल्दी",
        "Hello भाई कैसे हो",
        "Send करो OTP मुझे",
    ]
    
    errors = []
    for text in hinglish_tests:
        try:
            lang, conf = detect_language(text)
            assert lang in ["en", "hi", "hinglish"], f"Invalid lang: {lang}"
            assert 0.0 <= conf <= 1.0, f"Invalid confidence: {conf}"
        except Exception as e:
            errors.append({"text": text, "error": str(e)})
    
    return {
        "id": "AC-1.1.3",
        "description": "Handles Hinglish without errors",
        "total_tests": len(hinglish_tests),
        "errors": errors,
        "passed": len(errors) == 0,
    }


def verify_response_time():
    """AC-1.1.4: Returns result within 100ms"""
    test_texts = [
        ("English", "You have won a prize! Send OTP immediately to claim."),
        ("Hindi", "आप जीत गए हैं 10 लाख रुपये! अपना OTP शेयर करें।"),
        ("Hinglish", "Aapne jeeta है 10 lakh rupees! Claim करो now."),
        ("Long English", "You have won a prize! " * 50),
    ]
    
    results = []
    all_under_100ms = True
    
    for name, text in test_texts:
        start = time.time()
        detect_language(text)
        elapsed_ms = (time.time() - start) * 1000
        passed = elapsed_ms < 100
        if not passed:
            all_under_100ms = False
        results.append({
            "name": name,
            "elapsed_ms": elapsed_ms,
            "passed": passed,
        })
    
    return {
        "id": "AC-1.1.4",
        "description": "Returns result within 100ms",
        "results": results,
        "passed": all_under_100ms,
    }


def main():
    print("=" * 60)
    print("Task 3.1: Language Detection - Acceptance Criteria Verification")
    print("=" * 60)
    print()
    
    # Run all verifications
    hindi_result = verify_hindi_accuracy()
    english_result = verify_english_accuracy()
    hinglish_result = verify_hinglish_handling()
    response_result = verify_response_time()
    
    # Print Hindi results
    print(f"AC-1.1.1: Hindi detection accuracy")
    print(f"  Accuracy: {hindi_result['accuracy']:.0%} ({hindi_result['correct']}/{hindi_result['total']})")
    print(f"  Required: >95%")
    status = "PASS" if hindi_result["passed"] else "FAIL"
    print(f"  Status: {status}")
    print()
    
    # Print English results
    print(f"AC-1.1.2: English detection accuracy")
    print(f"  Accuracy: {english_result['accuracy']:.0%} ({english_result['correct']}/{english_result['total']})")
    print(f"  Required: >98%")
    status = "PASS" if english_result["passed"] else "FAIL"
    print(f"  Status: {status}")
    print()
    
    # Print Hinglish results
    print(f"AC-1.1.3: Hinglish handling")
    print(f"  Tests: {hinglish_result['total_tests']}")
    print(f"  Errors: {len(hinglish_result['errors'])}")
    if hinglish_result["errors"]:
        for err in hinglish_result["errors"]:
            print(f"    - {err['text']}: {err['error']}")
    print(f"  Required: No errors")
    status = "PASS" if hinglish_result["passed"] else "FAIL"
    print(f"  Status: {status}")
    print()
    
    # Print Response time results
    print(f"AC-1.1.4: Response time")
    for r in response_result["results"]:
        status = "PASS" if r["passed"] else "FAIL"
        print(f"  {r['name']}: {r['elapsed_ms']:.2f}ms [{status}]")
    print(f"  Required: <100ms")
    status = "PASS" if response_result["passed"] else "FAIL"
    print(f"  Status: {status}")
    print()
    
    # Summary
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    all_results = [hindi_result, english_result, hinglish_result, response_result]
    all_passed = all(r["passed"] for r in all_results)
    
    for r in all_results:
        status = "PASS" if r["passed"] else "FAIL"
        print(f"  {r['id']}: {r['description']} - {status}")
    
    print()
    if all_passed:
        print("ALL ACCEPTANCE CRITERIA PASSED")
        return 0
    else:
        print("SOME ACCEPTANCE CRITERIA FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
