from app.services.pydantic_intake_agent import
  _check_for_empty_fields, _get_all_field_paths,
  _field_has_data

  # Test data from your example
  data = {
      'email':
  'matthew.weiner@poundofcureweightloss.com',
      'phone': {'home': '', 'work': '', 'mobile':
  '2488352997', 'preferred': 'mobile',
  'workExtension': ''},
      'gender': 'male',
      'address': {'city': '', 'state': '', 'country':      
  'us', 'zipCode': '', 'addressLine1': '3010 E Camino Juan Paisano', 'addressLine2': ''},
      'lastName': 'patient',
      'firstName': 'testing',
      'middleName': 'Jeremy',
      'dateOfBirth': '1972-07-28',
      'careTeamProviders': [{'name': 'Dr. Gallasso',       
  'specialty': ''}]
  }

  print('All field paths:')
  all_paths =_get_all_field_paths('intake_demographics')
  for path in sorted(all_paths):
      print(f'  {path}')

  print('\nTesting specific empty fields:')
  test_fields = ['address.city', 'address.state',
  'address.zipCode', 'careTeamProviders.specialty']        
  for field in test_fields:
      has_data = _field_has_data(data, field)
      print(f'  {field}: has_data={has_data}')

  print('\nEmpty fields found:')
  empty_fields =
  _check_for_empty_fields('intake_demographics', data)     
  for field in empty_fields:
      print(f'  {field}')