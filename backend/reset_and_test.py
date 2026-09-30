import requests

# First reset the data
r = requests.post('http://localhost:8000/admin/reset')
print('Data reset:', r.json())

# Then test again
r = requests.get('http://localhost:8000/facilities')
for f in r.json():
    print(f"  {f['name']} ({f['facility_id']}): overall={f['overall_risk']}")

# Check PHC_01 stock
r = requests.get('http://localhost:8000/facilities/PHC_01/stock')
for item in r.json()['items']:
    print(f"  {item['item_name']}: stock={item['current_stock']}, days={item['days_remaining']}, risk={item['risk_level']}")

# Test recommendation
r = requests.post('http://localhost:8000/transfer/recommend', params={'item_id': 'ORS', 'facility_id': 'PHC_01'})
print('Recommendation:', r.json())

# Test simulation
r = requests.post('http://localhost:8000/simulate', json={'item_id': 'ORS', 'facility_id': 'PHC_01', 'delay_days': 3})
print('Simulation:', r.json())