from enum import Enum
from typing import List, Tuple
import numpy as np

class Power(Enum):
	COAL = 0,
	GAS = 1,
	NUCLEAR = 2,
	WATER = 3,
	WATER_STORAGE = 4,
	WIND = 5,
	PHOTOVOLTAIC = 6,

class MeritOrder:
	def __init__(self, prices: dict[Power, float], productions: List[Tuple[Power, float]], total_consumption: float):
		self.prices = prices
		self.productions = np.array(productions)
		self.total_consumption = total_consumption
		self.sorted_productions = np.array(sorted(self.productions, key = lambda x: self.prices[x[0]]))

	def getPrice(self):
		'''Get the current price of power in EUR/MWh, by ordering the powerplant according to the merit order, and getting the lowest price that satisfies the total consumption.'''
	
		cmsm = np.cumsum(self.sorted_productions[:, 1])

		for idx, el in enumerate(cmsm):
			if el >= self.total_consumption:
				return self.prices[self.sorted_productions[idx][0]]

		return 0

	def getTotalCost(self):
		'''Get the total cost of electricity production with the current consumption total.'''
		price_per_mwh = self.getPrice()

		return price_per_mwh * self.total_consumption

	def getTotalProfit(self):
		'''Get total profit in EUR for all the powerplants, that produce, with a given consumption.'''

		price = self.getPrice()

		cmsm = np.cumsum(self.sorted_productions[:, 1])

		total = 0

		for idx, el in enumerate(cmsm):
			if el >= self.total_consumption:
				pp_type, _ = self.sorted_productions[idx]
				pp_price = self.prices[pp_type]

				production = self.total_consumption - cmsm[idx - 1] #the previous cumsum element

				pp_selling_cost = production * price
				pp_operating_cost = production * pp_price

				total += pp_selling_cost - pp_operating_cost #profit for powerplant

				break

			else:
				pp_type, pp_power = self.sorted_productions[idx]
				pp_price = self.prices[pp_type]

				pp_selling_cost = pp_power * price
				pp_operating_cost = pp_power * pp_price

				total += pp_selling_cost - pp_operating_cost #profit for powerplant

		return total


if __name__ == "__main__":
	prices = {
		Power.COAL: 101,
		Power.GAS: 132,
		Power.NUCLEAR: 15,
		Power.WATER: 0,
		Power.WATER_STORAGE: 0,
		Power.WIND: 0,
		Power.PHOTOVOLTAIC: 0,
	}

	productions = [
		(Power.COAL, 300),
		(Power.COAL, 400),
		(Power.GAS, 200),
		(Power.NUCLEAR, 1000),
		(Power.WATER, 50),
		(Power.WIND, 100),
		(Power.PHOTOVOLTAIC, 50),
	]
	
	mo = MeritOrder(prices, productions, 1001)

	print(f"price: {mo.getPrice()} EUR/MWh")
	print(f"cost: {mo.getTotalCost()} EUR")
	print(f"profit: {mo.getTotalProfit()} EUR")