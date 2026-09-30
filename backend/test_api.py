import requests

base = 'http://localhost:8000'

print('=== /health ===')
print(requests.get(f'{base}/health').json())

print('\n=== /facilities ===')
facilities = requests.get(f'{base}/facilities').json()
for f in facilities:
    print(f"  {f['name']} ({f['facility_id']}): overall={f['overall_risk']}, items={len(f['items'])}")

print('\n=== /facilities/PHC_01/stock ===')
stock = requests.get(f'{base}/facilities/PHC_01/stock').json()
for item in stock['items']:
    print(f"  {item['item_name']}: stock={item['current_stock']}, days={item['days_remaining']}, risk={item['risk_level']}")

print('\n=== /forecast/ORS/PHC_01 ===')
print(requests.get(f'{base}/forecast/ORS/PHC_01').json())

print('\n=== /surplus/ORS/PHC_01 ===')
surplus = requests.get(f'{base}/surplus/ORS/PHC_01').json()
for c in surplus['candidates']:
    print(f"  {c['facility_name']}: dist={c['distance_km']}km, transferable={c['transferable_qty']}")

print('\n=== /transfer/recommend ===')
rec = requests.post(f'{base}/transfer/recommend', params={'item_id': 'ORS', 'facility_id': 'PHC_01'}).json()
print(rec)

print('\n=== /simulate ===')
sim = requests.post(f'{base}/simulate', json={'item_id': 'ORS', 'facility_id': 'PHC_01', 'delay_days': 3}).json()
print(sim)

print('\n=== /transfer/apply ===')
apply = requests.post(f'{base}/transfer/apply', json={
    'item_id': 'ORS',
    'source_facility_id': 'PHC_04',
    'destination_facility_id': 'PHC_01',
    'quantity': 142
}).json()
print(apply)