import sys
import os
sys.path.append('.')

# Set a dummy OpenAI key to avoid initialization issues
os.environ['OPENAI_API_KEY'] = 'dummy-key-for-testing'

from app.services.pydantic_intake_agent import _check_for_empty_fields, _update_tracking_for_review, _field_has_data

# Your actual data from the conversation
data = {
    "email": "matthew.weiner@poundofcureweightloss.com",
    "phone": {
        "home": "",
        "work": "",
        "mobile": "2488352997",
        "preferred": "mobile",
        "workExtension": ""
    },
    "gender": "male",
    "address": {
        "city": "",
        "state": "",
        "country": "us",
        "zipCode": "",
        "addressLine1": "3010 E Camino Juan Paisano",
        "addressLine2": ""
    },
    "lastName": "patient",
    "firstName": "testing",
    "isComplete": True,
    "middleName": "Jeremy",
    "dateOfBirth": "1972-07-28",
    "maritalStatus": "married",
    "emergencyContact": {
        "name": "Loren Weiner",
        "phone": "2488427542",
        "relationship": "wife"
    },
    "employmentStatus": "employed",
    "careTeamProviders": [
        {
            "name": "Dr. Gallasso",
            "specialty": ""
        }
    ],
    "communicationPreferences": {
        "preferredMethod": "",
        "textNotifications": True,
        "emailNotifications": True,
        "voiceNotifications": True
    }
}

print('Testing specific known empty fields:')
empty_test_fields = ['address.city', 'address.state', 'address.zipCode', 'careTeamProviders.specialty']
for field in empty_test_fields:
    has_data = _field_has_data(data, field)
    print(f'  {field}: has_data={has_data}')

print('\nTesting fields that should have data:')
filled_test_fields = ['emergencyContact.name', 'emergencyContact.phone', 'emergencyContact.relationship']
for field in filled_test_fields:
    has_data = _field_has_data(data, field)
    print(f'  {field}: has_data={has_data}')

print('\nAll empty fields found:')
empty_fields = _check_for_empty_fields('intake_demographics', data)
for field in empty_fields:
    print(f'  {field}')

print('\nTesting the review logic:')
tracking = {'unasked_fields': [], 'reviewed': False, 'isComplete': False, 'pushed_to_charm': False}
updated_tracking = _update_tracking_for_review(tracking, 'intake_demographics', data)
print(f'Updated tracking: {updated_tracking}')

# Count expected vs actual empty fields
expected_empty = ['address.city', 'address.state', 'address.zipCode', 'careTeamProviders.specialty']
actual_empty = updated_tracking['unasked_fields']
print(f'\nExpected empty fields: {len(expected_empty)}')
print(f'Actual empty fields found: {len(actual_empty)}')
print(f'Missing from actual: {set(expected_empty) - set(actual_empty)}')
print(f'Extra in actual: {set(actual_empty) - set(expected_empty)}')