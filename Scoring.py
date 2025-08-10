from collections import defaultdict
from MeritOrder import MeritOrder, Power
from typing import List, Tuple, Dict
import numpy as np
import json

POPULARITY_PER_MWH = 0.5
BLACKOUT_OFFSET = 50
BLACKOUT_PENALTY = 50
SCORE_OFFSET = 248.2 #add to each score, to not reach 0

def calculate_final_scores(history: List[dict], building_consumptions: Dict[str, float]):
	"""
	Calculates final scores for all teams based on game history and building data.
	All scores have SCORE_OFFSET added as a base value.
	
	Args:
		history: List of rounds with team production/consumption data
		building_consumptions: Dictionary mapping team_name to total building consumption (MW)
	"""

	raw_metrics = defaultdict(lambda: {
		'total_co2': 0,
		'total_profit': 0,
		'round_stabilities': [],
		'round_popularities': []
	})
	
	round_details = []
	prices = {
		Power.COAL: 101, Power.GAS: 132, Power.NUCLEAR: 15,
		Power.WATER: 0, Power.WATER_STORAGE: 0, 
		Power.WIND: 0, Power.PHOTOVOLTAIC: 0,
	}

	for round_data in history:
		current_round_details = {}
		for team_name, data in round_data.items():
			mo = MeritOrder(prices, data['productions'], data['total_consumption'])
			
			raw_metrics[team_name]['total_co2'] += mo.getReleasedCO2()
			raw_metrics[team_name]['total_profit'] += mo.getTotalProfit()
			
			total_prod = sum(p[1] for p in data['productions'])
			consumption = data['total_consumption']
			
			if abs(total_prod - consumption) > BLACKOUT_OFFSET:
				raw_metrics[team_name]['round_stabilities'].append(BLACKOUT_PENALTY)
			else:
				raw_metrics[team_name]['round_stabilities'].append(mo.getGridStability())

			current_round_details[team_name] = {
				'price': mo.getPrice(),
				'consumption': consumption
			}
		round_details.append(current_round_details)


	for round_data in round_details:
		prices = [d['price'] for d in round_data.values()]
		consumptions = [d['consumption'] for d in round_data.values()]
		
		min_price, max_price = min(prices), max(prices)
		min_cons, max_cons = min(consumptions), max(consumptions)
		
		for team, data in round_data.items():

			price_merit = (max_price - data['price']) / (max_price - min_price) \
				if max_price > min_price else 0.5
				
			growth_merit = (data['consumption'] - min_cons) / (max_cons - min_cons) \
				if max_cons > min_cons else 0.5
				
			raw_metrics[team]['round_popularities'].append(
				0.5 * price_merit + 0.5 * growth_merit
			)

	final_scores = {}
	teams = list(raw_metrics.keys())
	
	def apply_offset(score):
		"""Adds SCORE_OFFSET to the calculated score"""
		return score + SCORE_OFFSET
	
	co2_vals = [raw_metrics[t]['total_co2'] for t in teams]
	min_co2, max_co2 = min(co2_vals), max(co2_vals)
	for team in teams:
		if max_co2 > min_co2:
			ecology = 1000 * (max_co2 - raw_metrics[team]['total_co2']) / (max_co2 - min_co2)
		else:
			ecology = 1000
		final_scores.setdefault(team, {})['ecology'] = apply_offset(ecology)
	
	profits = [raw_metrics[t]['total_profit'] for t in teams]
	min_profit, max_profit = min(profits), max(profits)
	for team in teams:
		if max_profit > min_profit:
			finance = 1000 * (raw_metrics[team]['total_profit'] - min_profit) / (max_profit - min_profit)
		else:
			finance = 1000
		final_scores[team]['finance'] = apply_offset(finance)
		
	for team in teams:
		stability = np.mean(raw_metrics[team]['round_stabilities']) * 10
		final_scores[team]['stability'] = apply_offset(stability)
		
	for team in teams:
		base_popularity = np.mean(raw_metrics[team]['round_popularities']) * 1000
		building_bonus = building_consumptions.get(team, 0) * POPULARITY_PER_MWH
		popularity = base_popularity + building_bonus
		final_scores[team]['popularity'] = apply_offset(popularity)
	
	return final_scores


if __name__ == "__main__":
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