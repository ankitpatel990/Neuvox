"""Quick verification of Task 3.2 tests from TASKS.md"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, '.')

from app.models.detector import ScamDetector, reset_detector_cache

print('Verification tests from TASKS.md:')
print()

reset_detector_cache()
detector = ScamDetector(load_model=False)

# Test English scam
result1 = detector.detect("You won 10 lakh! Send OTP now!")
print(f'Test 1: detector.detect("You won 10 lakh! Send OTP now!")')
print(f'  Result: scam_detected={result1["scam_detected"]}, confidence={result1["confidence"]:.2f}')
assert result1['scam_detected'] == True, f'Expected scam_detected=True, got {result1["scam_detected"]}'
assert result1['confidence'] > 0.85, f'Expected confidence > 0.85, got {result1["confidence"]}'
print('  PASS')

# Test legitimate
result2 = detector.detect("Hi, how are you?")
print(f'Test 2: detector.detect("Hi, how are you?")')
print(f'  Result: scam_detected={result2["scam_detected"]}, confidence={result2["confidence"]:.2f}')
assert result2['scam_detected'] == False, f'Expected scam_detected=False, got {result2["scam_detected"]}'
print('  PASS')

print()
print('All verification tests from TASKS.md PASSED!')
