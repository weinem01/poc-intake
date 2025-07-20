import sys
import os
sys.path.append('.')

# Set a dummy OpenAI key to avoid initialization issues
os.environ['OPENAI_API_KEY'] = 'dummy-key-for-testing'

from app.services.pydantic_intake_agent import _update_tracking_for_completeness

print('Testing simplified completion logic:')

# Test case 1: Empty unasked_fields should mark as complete
print('\nTest 1: Empty unasked_fields')
tracking1 = {'unasked_fields': [], 'isComplete': False, 'pushed_to_charm': False}
updated1 = _update_tracking_for_completeness(tracking1, 'intake_demographics')
print(f'Input: {tracking1}')
print(f'Output: {updated1}')
print(f'Expected isComplete: True, Actual: {updated1["isComplete"]}')

# Test case 2: Non-empty unasked_fields should not mark as complete
print('\nTest 2: Non-empty unasked_fields')
tracking2 = {'unasked_fields': ['address.city', 'address.state'], 'isComplete': False, 'pushed_to_charm': False}
updated2 = _update_tracking_for_completeness(tracking2, 'intake_demographics')
print(f'Input: {tracking2}')
print(f'Output: {updated2}')
print(f'Expected isComplete: False, Actual: {updated2["isComplete"]}')

# Test case 3: Already complete with empty unasked_fields should stay complete
print('\nTest 3: Already complete with empty unasked_fields')
tracking3 = {'unasked_fields': [], 'isComplete': True, 'pushed_to_charm': False}
updated3 = _update_tracking_for_completeness(tracking3, 'intake_demographics')
print(f'Input: {tracking3}')
print(f'Output: {updated3}')
print(f'Expected isComplete: True, Actual: {updated3["isComplete"]}')

print('\n✅ All tests completed!')