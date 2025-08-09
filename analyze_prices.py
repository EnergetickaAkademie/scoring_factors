import json

with open('powerplants.json', 'r') as f:
	data = json.load(f)

for source in data:
	prices = [float(plant['price']) for plant in data[source]]
	mean_price = sum(prices) / len(prices)
	print(f"{source}: {mean_price:.2f}")
