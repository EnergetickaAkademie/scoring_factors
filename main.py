from MeritOrder import Power
from Scoring import calculate_final_scores
import numpy as np
import json
import matplotlib.pyplot as plt

building_consumptions = {
	"Team A": 500,
	"Team B": 600,
	"Team C": 450,
	"Team D": 700,
	"Team E": 750
}

history = [
	# --- Round 1 ---
	{
		"Team A": {'productions': [(Power.NUCLEAR, 1500), (Power.WIND, 100)], 'total_consumption': 1600},
		"Team B": {'productions': [(Power.COAL, 1000), (Power.GAS, 800)], 'total_consumption': 1800},
		"Team C": {'productions': [(Power.NUCLEAR, 800), (Power.GAS, 400), (Power.WIND, 100)], 'total_consumption': 1300},
		"Team D": {'productions': [(Power.WATER, 2500)], 'total_consumption': 2000},
		"Team E": {'productions': [(Power.WIND, 1200), (Power.PHOTOVOLTAIC, 400)], 'total_consumption': 1500},
	},
	# --- Round 2 ---
	{
		"Team A": {'productions': [(Power.NUCLEAR, 1500), (Power.WIND, 300)], 'total_consumption': 1800},
		"Team B": {'productions': [(Power.COAL, 1200), (Power.GAS, 800)], 'total_consumption': 2000},
		"Team C": {'productions': [(Power.NUCLEAR, 800), (Power.GAS, 500), (Power.WIND, 200)], 'total_consumption': 1500},
		"Team D": {'productions': [(Power.WATER, 2500)], 'total_consumption': 2200},
		"Team E": {'productions': [(Power.WIND, 1400), (Power.PHOTOVOLTAIC, 600)], 'total_consumption': 1700}, # Barely meeting demand
	},
	# --- Round 3 ---
	{
		"Team A": {'productions': [(Power.NUCLEAR, 1500), (Power.WIND, 500), (Power.PHOTOVOLTAIC, 100)], 'total_consumption': 2000},
		"Team B": {'productions': [(Power.COAL, 1300), (Power.GAS, 900)], 'total_consumption': 2200},
		"Team C": {'productions': [(Power.NUCLEAR, 900), (Power.GAS, 500), (Power.WIND, 300)], 'total_consumption': 1700},
		"Team D": {'productions': [(Power.WATER, 2500), (Power.GAS, 100)], 'total_consumption': 2400}, # Demand exceeds hydro
		"Team E": {'productions': [(Power.WIND, 1000), (Power.PHOTOVOLTAIC, 400)], 'total_consumption': 1900}, # BLACKOUT!
	},
	# --- Round 4 ---
	{
		"Team A": {'productions': [(Power.NUCLEAR, 2000), (Power.WIND, 500)], 'total_consumption': 2200}, # New nuclear plant
		"Team B": {'productions': [(Power.COAL, 1500), (Power.GAS, 1000)], 'total_consumption': 2400},
		"Team C": {'productions': [(Power.NUCLEAR, 900), (Power.GAS, 600), (Power.WIND, 400)], 'total_consumption': 1900},
		"Team D": {'productions': [(Power.WATER, 2500), (Power.GAS, 300)], 'total_consumption': 2600},
		"Team E": {'productions': [(Power.WIND, 2000), (Power.PHOTOVOLTAIC, 800)], 'total_consumption': 2100},
	},
	# --- Round 5 ---
	{
		"Team A": {'productions': [(Power.NUCLEAR, 2000), (Power.WIND, 700), (Power.PHOTOVOLTAIC, 100)], 'total_consumption': 2400},
		"Team B": {'productions': [(Power.COAL, 1600), (Power.GAS, 1100)], 'total_consumption': 2600},
		"Team C": {'productions': [(Power.NUCLEAR, 1000), (Power.GAS, 600), (Power.WIND, 500)], 'total_consumption': 2100},
		"Team D": {'productions': [(Power.WATER, 2500), (Power.GAS, 500)], 'total_consumption': 2800},
		"Team E": {'productions': [(Power.WIND, 1500), (Power.PHOTOVOLTAIC, 600), (Power.GAS, 100)], 'total_consumption': 2300}, # Added a gas peaker
	},
	# --- Round 6 ---
	{
		"Team A": {'productions': [(Power.NUCLEAR, 2000), (Power.WIND, 900), (Power.PHOTOVOLTAIC, 300)], 'total_consumption': 2600},
		"Team B": {'productions': [(Power.COAL, 1800), (Power.GAS, 1200)], 'total_consumption': 2800},
		"Team C": {'productions': [(Power.NUCLEAR, 1000), (Power.GAS, 700), (Power.WIND, 600)], 'total_consumption': 2300},
		"Team D": {'productions': [(Power.WATER, 2500), (Power.COAL, 500)], 'total_consumption': 3000}, # Built a coal plant
		"Team E": {'productions': [(Power.WIND, 1200), (Power.PHOTOVOLTAIC, 500), (Power.GAS, 100)], 'total_consumption': 2500}, # BLACKOUT!
	},
	# --- Round 7 ---
	{
		"Team A": {'productions': [(Power.NUCLEAR, 2500), (Power.WIND, 1000)], 'total_consumption': 2800}, # Another nuclear plant
		"Team B": {'productions': [(Power.COAL, 2000), (Power.GAS, 1200)], 'total_consumption': 3000},
		"Team C": {'productions': [(Power.NUCLEAR, 1200), (Power.GAS, 700), (Power.WIND, 700)], 'total_consumption': 2500},
		"Team D": {'productions': [(Power.WATER, 2500), (Power.COAL, 800)], 'total_consumption': 3200},
		"Team E": {'productions': [(Power.WIND, 2500), (Power.PHOTOVOLTAIC, 1000), (Power.GAS, 200)], 'total_consumption': 2700},
	},
	# --- Round 8 ---
	{
		"Team A": {'productions': [(Power.NUCLEAR, 2500), (Power.WIND, 1200), (Power.PHOTOVOLTAIC, 300)], 'total_consumption': 3000},
		"Team B": {'productions': [(Power.COAL, 2200), (Power.GAS, 1300)], 'total_consumption': 3200},
		"Team C": {'productions': [(Power.NUCLEAR, 1200), (Power.GAS, 800), (Power.WIND, 800)], 'total_consumption': 2700},
		"Team D": {'productions': [(Power.WATER, 2500), (Power.COAL, 1000)], 'total_consumption': 3400},
		"Team E": {'productions': [(Power.WIND, 1800), (Power.PHOTOVOLTAIC, 800), (Power.GAS, 200)], 'total_consumption': 2900}, # Another blackout!
	},
	# --- Round 9 ---
	{
		"Team A": {'productions': [(Power.NUCLEAR, 2500), (Power.WIND, 1500), (Power.PHOTOVOLTAIC, 400)], 'total_consumption': 3200},
		"Team B": {'productions': [(Power.COAL, 2400), (Power.GAS, 1400)], 'total_consumption': 3400},
		"Team C": {'productions': [(Power.NUCLEAR, 1200), (Power.GAS, 900), (Power.WIND, 900)], 'total_consumption': 2900},
		"Team D": {'productions': [(Power.WATER, 2500), (Power.COAL, 1200)], 'total_consumption': 3600},
		"Team E": {'productions': [(Power.WIND, 3000), (Power.PHOTOVOLTAIC, 1200), (Power.GAS, 200)], 'total_consumption': 3100},
	},
	# --- Round 10 ---
	{
		"Team A": {'productions': [(Power.NUCLEAR, 3000), (Power.WIND, 1500)], 'total_consumption': 3400},
		"Team B": {'productions': [(Power.COAL, 2500), (Power.GAS, 1500)], 'total_consumption': 3600},
		"Team C": {'productions': [(Power.NUCLEAR, 1500), (Power.GAS, 1000), (Power.WIND, 1000)], 'total_consumption': 3100},
		"Team D": {'productions': [(Power.WATER, 2500), (Power.COAL, 1500)], 'total_consumption': 3800},
		"Team E": {'productions': [(Power.WIND, 2000), (Power.PHOTOVOLTAIC, 1000), (Power.GAS, 500)], 'total_consumption': 3300},
	},
]

final_scores = calculate_final_scores(history, building_consumptions)

print(json.dumps(final_scores, indent=4))

teams = list(final_scores.keys())
factors = list(final_scores[teams[0]].keys())
factor_labels = {
	"ecology": "Ekologie",
	"finance": "Finance",
	"stability": "Energetický mix",
	"popularity": "Popularita"
}

team_count = len(teams)
factor_count = len(factors)
x = np.arange(team_count)
width = 0.15
colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']

fig, ax = plt.subplots(figsize=(12, 8))

for i, factor in enumerate(factors):
	values = [final_scores[team][factor] for team in teams]
	offset = width * (i - (factor_count - 1) / 2)
	rects = ax.bar(x + offset, values, width, label=factor_labels[factor], color=colors[i % len(colors)])

ax.set_ylabel('Skóre')
ax.set_title('Finální skóre týmů podle faktorů')
ax.set_xticks(x)
ax.set_xticklabels(teams)
ax.legend()

fig.tight_layout()
plt.show()