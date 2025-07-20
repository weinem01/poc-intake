import sys
import os
import json
sys.path.append('.')

# Set a dummy OpenAI key to avoid initialization issues
os.environ['OPENAI_API_KEY'] = 'dummy-key-for-testing'

from app.models.intake_schemas import IntakeDemographics

# Get the full schema to see the structure
schema = IntakeDemographics.model_json_schema()

print("Full schema structure:")
print(json.dumps(schema, indent=2))

print("\n\nAddress field details:")
address_field = schema.get('properties', {}).get('address', {})
print(json.dumps(address_field, indent=2))

print("\n\nCareTeamProviders field details:")
care_team_field = schema.get('properties', {}).get('careTeamProviders', {})
print(json.dumps(care_team_field, indent=2))