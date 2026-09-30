import requests

base = 'http://localhost:8000'

# Test apply transfer
rec = requests.post(f'{base}/transfer/recommend', params={'item_id': 'ORS', 'facility_id': 'PHC_01'}).json()
print('Recommendation:', rec['recommendation'])

if rec['recommendation']:
    r = rec['recommendation']
    apply = requests.post(f'{base}/transfer/apply', json={
        'item_id': r['item_id'],
        'source_facility_id': r['source_facility_id'],
        'destination_facility_id': r['requesting_facility_id'],
        'quantity': r['quantity']
    }).json()
    print('Apply result:', apply)

# Verify new state
stock = requests.get(f'{base}/facilities/PHC_01/stock').json()
print('\nPHC_01 after transfer:')
for item in stock['items']:
    print(f"  {item['item_name']}: stock={item['current_stock']}, days={item['days_remaining']}, risk={item['risk_level']}")

stock = requests.get(f'{base}/facilities/PHC_04/stock').json()
print('\nPHC_04 after transfer:')
for item in stock['items']:
    print(f"  {item['item_name']}: stock={item['current_stock']}, days={item['days_remaining']}, risk={item['risk_level']}")