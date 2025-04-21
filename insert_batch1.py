import json
import requests

with open("quatrains_batch1.json", "r") as file:
    data = json.load(file)

for q in data:
    response = requests.post("http://localhost:5000/quatrain", json=q)
    print(response.status_code, response.json())
