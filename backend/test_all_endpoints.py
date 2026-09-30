import requests

base = 'http://localhost:8000'

# Test all 8 endpoints
print('=== 1. /facilities ===')
r = requests.get(f'{base}/facilities')
for f in r.json():
    print(f'  {f["name"]}: {f["overall_risk"]}')

print('\n=== 2. /facilities/PHC_01/stock ===')
r = requests.get(f'{base}/facilities/PHC_01/stock')
for item in r.json()['items']:
    print(f'  {item["item_name"]}: {item["days_remaining"]} days, {item["risk_level"]}')

print('\n=== 3. /forecast/ORS/PHC_01 ===')
r = requests.get(f'{base}/forecast/ORS/PHC_01')
print(r.json())

print('\n=== 4. /surplus/ORS/PHC_01 ===')
r = requests.get(f'{base}/surplus/ORS/PHC_01')
for c in r.json()['candidates']:
    print(f'  {c["facility_name"]}: {c["transferable_qty"]} transferable, {c["distance_km"]}km')

print('\n=== 5. /transfer/recommend ===')
r = requests.post(f'{base}/transfer/recommend', params={'item_id': 'ORS', 'facility_id': 'PHC_01'})
print(r.json())

print('\n=== 6. /simulate ===')
r = requests.post(f'{base}/simulate', json={'item_id': 'ORS', 'facility_id': 'PHC_01', 'delay_days': 3})
print(r.json())

print('\n=== 7. /explain ===')
r = requests.post(f'{base}/explain', json={
    'facility': 'PHC Madurai North',
    'item': 'Oral Rehydration Salts',
    'days_remaining': 1.3,
    'risk_level': 'critical',
    'recommended_transfer': {'from_facility': 'PHC Melur', 'quantity': 142, 'distance_km': 25.8},
    'post_transfer_days_remaining': 6.0
})
print(r.json())

print('\n=== 8. /admin/reset ===')
r = requests.post(f'{base}/admin/reset')
print(r.json())