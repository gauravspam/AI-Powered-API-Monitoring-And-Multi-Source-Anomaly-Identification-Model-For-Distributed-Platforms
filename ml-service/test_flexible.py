import requests
import json

print("Testing flexible multimodal prediction\n")

tests = [
    {'metrics': {'cpu_usage': 99, 'memory_usage': 99, 'response_time_ms': 5000, 'error_rate': 0.9}},
    {'metrics': {'cpu_usage': 50, 'memory_usage': 50}},
    {'logs': [{'level': 'CRITICAL', 'message': 'Database connection failed'}]},
    {'metrics': {'cpu_usage': 85}, 'logs': [{'level': 'ERROR', 'message': 'timeout'}], 'traces': [{'duration': 5000, 'status_code': 500}]}
]

for i, data in enumerate(tests):
    r = requests.post('http://localhost:9000/predict/flexible', json=data)
    res = r.json()
    print(f'Test {i+1}:')
    print(f'  Score: {res["final_score"]}')
    print(f'  Severity: {res["severity"]}')
    print(f'  Confidence: {res["confidence"]}')
    print(f'  Modalities: {res["modalities_present"]}')
    print(f'  Raw MSIF: {res["msif_score"]}, PLE: {res["ple_score"]}')
    print()