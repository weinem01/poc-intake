from pydantic_ai import Agent
from pydantic import BaseModel

class Test(BaseModel):
    name: str

try:
    agent = Agent('gpt-4o-mini', result_type=Test)
    print('Agent created successfully')
except Exception as e:
    print(f'Error creating agent: {e}')
    print(f'Error type: {type(e)}')