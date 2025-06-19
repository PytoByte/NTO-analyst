from tkinter import *
from tkinter import ttk
from tkinter import filedialog as fd
import csv
import json
import random
import numpy as np

def randColor():
	return "#%06x" % random.randint(0, 0xFFFFFF)

teams = []
forecast = {}
TAGS = {}

class Buildings():
	def __init__(self):
		self.IDs = {}
		self.dt = DataTransformer(100, self)
		self.buffer = Buffer()

	def getByName(self, name):
		return self.IDs[name]

	def getByGroup(self, group):
		result = []
		for build in self.IDs.values():
			if type(build).__name__ == group:
				result.append(build)
		return result

	def getAll(self):
		return list(self.IDs.values())

	def regClass(self, cls):
		if cls.name not in self.IDs.keys():
			self.IDs[cls.name] = cls
			self.dt.update(buildings = self)
			return True

		else:
			print(f"Ошибка! Класс с именем {cls.name} уже существует")

		return False


class WidgetStyle():
	def __init__(self):
		self.styles = {}

	def newStyle(self, name, **options):
		self.styles[name] = options

	def getStyle(self, name, **extraOptions):
		style = self.styles[name].copy()
		style.update(extraOptions)
		return style


ws = WidgetStyle()
ws.newStyle("labelMegatitle", font=("Arial Bold", 20), bg="#1c1c1c", fg="lightgray")
ws.newStyle("labelTitle", font=("Arial Bold", 15), bg="#1c1c1c", fg="lightgray")
ws.newStyle("labelText", font=("Arial Bold", 13), bg="#1c1c1c", fg="lightgray")
ws.newStyle("entryMain", font=("Arial Bold", 15), bg="#333232", fg="lightgray")
ws.newStyle("entrySub", font=("Arial Bold", 13), bg="#333232", fg="lightgray")
ws.newStyle("buttonMain", font=("Arial Bold", 15), bg="black", fg="gray")
ws.newStyle("checkboxMain", font=("Arial Bold", 15), bg="#1c1c1c", fg="black")

ws.newStyle("labelMyTeam", font=("Arial Bold", 13), bg="lightgreen", fg="black")
ws.newStyle("entryMyTeam", font=("Arial Bold", 15), bg="lightgreen", fg="black")

TEAMCOLOR = {
	0:"lightgreen",
	1:"pink",
	2:"yellow",
	3:"lightblue",
	4:"white",
	5:"orange",
	6:"magenta"
}
# ws.newStyle("frameVisible", borderwidth=1, relief="solid", padding=[8, 10])
# ws.newStyle("frameInvisible", borderwidth=0, relief="flat", padding=[0, 0])


class Infrastructure():
	def __init__(self, name, priority, buildings, logs=True):
		self.priority = priority
		self.name = name
		self.accurancy = []
		self.min = []
		self.costs = []
		self.count = 0
		self.buildings = buildings
		self.forecast = None
		self.logs = logs
		self.special = {}

		self.special["Дома А"] ={
			"miningA":True,
			"miningPrice":5
		}

		self.special["Дома Б"] ={
			"miningB":True,
			"miningPrice":9
		}
		if not self.buildings.regClass(self):
			if self.logs:
				print("Ошибка! Класс инициализинован с именем None")
			self.name = None
		else:
			if self.logs:
				print(f"Инициализированна инфраструктура {name}")

	def updateForecast(self):
		if self.logs:
			print(f"Получен прогноз погоды для {self.name}")
		self.forecast = list(map(float, forecast[self.name]))

	def clearData(self):
		self.accurancy.clear()
		self.min.clear()
		self.costs.clear()
		self.count = 0

	def setData(self, data):
		for build in data:
			self.costs.append(float(build[0]))
			self.accurancy.append(float(build[1]))
			self.min.append(float(build[2]))
		self.count = len(self.costs)
		if self.logs:
			pass
			#print(f"Данные для {self.name} полученны")

	def getForecastModerate(self):
		allForecasts = []
		for i, border in enumerate(self.min):
			newForecast = self.getForecast()
			newForecast = list(map(lambda x: x*self.accurancy[i], newForecast))
			newForecast = list(map(lambda x: 0 if x<border else x, newForecast))
			newForecast = self.mining(newForecast, self.costs[i])
			newForecast = list(map(lambda x: -x, newForecast))
			allForecasts.append(newForecast)

		if len(allForecasts) == 0:
			allForecasts.append( [0, ]*self.buildings.dt.stepsCount )
		return allForecasts

	def getForecast(self):
		return list(map(float, forecast[self.name]))

	def mining(self, forecast, price):
		if self.special.get(self.name):
			if self.special[self.name].get("miningA")==True:
				if price<self.special[self.name]["miningPrice"]:
					newForecast = list(map(lambda x: x+0.82*(self.special[self.name]["miningPrice"]-price)**2.6, forecast))
					return newForecast
			elif self.special[self.name].get("miningB")==True:
				if price<self.special[self.name]["miningPrice"]:
					newForecast = list(map(lambda x: x+0.24*(self.special[self.name]["miningPrice"]-price)**2.2, forecast))
					return newForecast
		return forecast

	def getCosts(self):
		if self.costs == []:
			return [[0, ]*self.buildings.dt.stepsCount]
		else:
			result = []
			for i, forecast in enumerate(self.getForecastModerate()):
				if self.name=="Дома А":
					if self.costs[i]<self.special[self.name]["miningPrice"]:
						miningConst = 0.82*(self.special[self.name]["miningPrice"]-self.costs[i])**2.6
					else:
						miningConst = 0
					result.append( list(map(lambda x: -(x+miningConst)*self.costs[i], forecast)) )
				elif self.name=="Дома Б":
					if self.costs[i]<self.special[self.name]["miningPrice"]:
						miningConst = 0.24*(self.special[self.name]["miningPrice"]-self.costs[i])**2.2
					else:
						miningConst = 0
					result.append( list(map(lambda x: -(x+miningConst)*self.costs[i], forecast)) )
				else:
					result.append( list(map(lambda x: -x*self.costs[i], forecast)) )
				
			return result
		return [[0, ]*self.buildings.dt.stepsCount]


class Generators(Infrastructure):
	def __init__(self, name, buildings, logs=True):
		self.name = name
		self.accurancy = []
		self.min = []
		self.costs = []
		self.forecast = None
		self.count = 0
		self.buildings = buildings
		self.logs = logs
		self.special = {}
		self.types = []

		self.special["Ветер"] = {
			"useKs":True,
			"ks":[0.05, 0.2, 0.3, 0.4, 0.05],
			"centerK":3,
			"breakValue":87.5,
			"maxFrom":86,
			"maxValue":25,
			"useTypes":True
		}

		self.special["Солнце"] = {
			"useKs":False,
			"maxFrom":None,
			"maxValue":25
		}
		
		if not self.buildings.regClass(self):
			if self.logs:
				print("Ошибка! Класс инициализинован с именем None")
			self.name = None
		else:
			if self.logs:
				print(f"Инициализированна инфраструктура {name}")

	def updateForecast(self):
		if not self.name=="Ветер":
			if self.logs:
				print(f"Получен прогноз погоды для {self.name}")
	
			#############################################
			#############################################
				#############################################
				#############################################
			self.forecast = list(map(float, forecast[self.name]))

	def getForecast(self, tag=None):
		if tag==None:
			tag = self.name
		
		return list(map(float, forecast[tag]))

	def clearData(self):
		self.accurancy.clear()
		self.min.clear()
		self.costs.clear()
		self.types.clear()
		self.count = 0

	def blackout(self, forecast):
		if self.special.get(self.name)!=None:
			if self.special[self.name].get("breakValue")!=None:
				newForecast = map(lambda x: x if round((((x**3)/(16**3))*100), 1)<self.special[self.name]["breakValue"] else 0, forecast)
				return newForecast
			else:
				return forecast
		else:
			return forecast

	def lower(self, forecast):
		if self.special.get(self.name)!=None:
			if self.special[self.name].get("maxFrom")!=None and self.special[self.name].get("maxValue")!=None:
				newForecast = list(map(lambda x: (((x**3)/(16**3))*100/self.special[self.name]["maxFrom"])*self.special[self.name]["maxValue"], forecast))
			else:
				newForecast = list(map(lambda x: ((x**3)/(16**3))*self.special[self.name]["maxValue"], forecast))
			return newForecast
		else:
			return forecast

	def getForecastModerate(self):
		allForecasts = []
		for i, border in enumerate(self.min):
			if self.name=="Ветер":
				newForecast = self.getForecast(self.types[i])
			else:
				newForecast = self.getForecast()
			newForecast = list(map(lambda x: x*self.accurancy[i], newForecast))
			newForecast = list(map(lambda x: 0 if x<border else x, newForecast))
			newForecast = list(self.lower(newForecast))
			newForecast = list(self.smooth(newForecast))
			newForecast = list(self.smoothWithKs(newForecast))
			newForecast = list(self.blackout(newForecast))
			allForecasts.append(newForecast)
			
		if len(allForecasts) == 0:
			allForecasts.append( [0, ]*self.buildings.dt.stepsCount )
			
		return allForecasts
		
	def setData(self, data):
		for build in data:
			self.costs.append(float(build[0]))
			self.accurancy.append(float(build[1]))
			self.min.append(float(build[2]))
			if self.special.get(self.name)!=None:
				if self.special[self.name].get("useTypes")==True:
					self.types.append(build[4])
		self.count = len(self.costs)
		if self.logs:
			pass
			#print(f"Данные для {self.name} полученны")

	def getCosts(self):
		if self.costs == []:
			return [[0]*self.buildings.dt.stepsCount]
		else:
			res = []
			for c in self.costs:
				res.append( [c, ]*self.buildings.dt.stepsCount )
			return res
		return [[0]*self.buildings.dt.stepsCount]

	def smoothWithKs(self, forecast):
		newForecast = []
		if self.special.get(self.name)!=None:
			if self.special[self.name]["useKs"]:
				for step in range(len(forecast)):
					value = 0
					for shift, k in enumerate(self.special[self.name]["ks"]):
						if step+shift-self.special[self.name]["centerK"]<0 or step+shift-self.special[self.name]["centerK"]>=len(forecast):
							continue
						else:
							if step+shift < self.special[self.name]["centerK"]:
								value += round(newForecast[step+shift-self.special[self.name]["centerK"]]*k, 2)
							else:
								value += forecast[step+shift-self.special[self.name]["centerK"]]*k
					newForecast.append(value)
			else:
				return forecast
		else:
			return forecast
		return newForecast

	def smooth(self, y_data, win=3):
		filt = np.ones(win)/win
		return list(np.convolve(y_data, filt, mode='same'))

class Extra():
	def __init__(self, name, buildings, logs=True):
		self.name = name
		self.costs = []
		self.count = 0
		self.buildings = buildings
		self.logs = logs
		
		if not self.buildings.regClass(self):
			if self.logs:
				print("Ошибка! Класс инициализинован с именем None")
			self.name = None
		else:
			if self.logs:
				print(f"Инициализированна инфраструктура {name}")
				
	def updateForecast(self):
		pass
	
	def getForecastModerate(self):
		return [[0]*len(forecast["Дома А"])]

	def clearData(self):
		self.costs.clear()
		self.count = 0

	def setData(self, data):
		for build in data:
			self.costs.append(float(build[0]))
		self.count = len(self.costs)
		if self.logs:
			#print(f"Данные для {self.name} полученны")
			pass

	def getCosts(self):
		if self.costs == []:
			return 0
		else:
			return sum(self.costs)
		return 0
	

class DataTransformer():
	def __init__(self, stepsCount, buildings):
		self.buildings = buildings
		self.generators = buildings.getByGroup("Generators")
		self.consumers = sorted(buildings.getByGroup("Infrastructure"), key=lambda x: x.priority)
		self.extra = buildings.getByGroup("Extra")
		self.infrastructure = buildings.getAll()
		self.stepsCount = stepsCount
		self.capacity = 150
		self.maxCharge = 10
		self.maxDischarge = 10
		self.autoB = 10
		self.autoS = 1
		self.loseK = 0.7
		self.loseKprogress = 0.1

	def update(self, **kwargs):
		if kwargs.get("capacity")!=None:
			self.capacity = kwargs["capacity"]
		if kwargs.get("maxCharge")!=None:
			self.maxCharge = kwargs["maxCharge"]
		if kwargs.get("maxDischarge")!=None:
			self.maxDischarge = kwargs["maxDischarge"]
		if kwargs.get("autoB")!=None:
			self.autoB = kwargs["autoB"]
		if kwargs.get("autoS")!=None:
			self.autoS = kwargs["autoS"]
		if kwargs.get("stepsCount")!=None:
			self.stepsCount = kwargs["stepsCount"]
		if kwargs.get("buildings")!=None:
			self.buildings = kwargs["buildings"]
			self.generators = self.buildings.getByGroup("Generators")
			self.consumers = sorted(self.buildings.getByGroup("Infrastructure"), key=lambda x: x.priority)
			self.infrastructure = self.buildings.getAll()
			self.extra = self.buildings.getByGroup("Extra")
		if kwargs.get("loseK")!=None:
			self.loseK = kwargs["loseK"]
		if kwargs.get("loseKprogress")!=None:
			self.loseKprogress = kwargs["loseKprogress"]

	def sumLists(self, lists):
		#print(lists)
		sList = [0, ]*max(list(map(len, lists)))
		for l in lists:
			if len(l)<len(sList):
				l = l+[0,]*(len(sList)-len(l))
			sList = list(map(lambda x, y: x + y, sList, l))
		return sList

	def sumForecasts(self):
		return self.sumLists(list(map(lambda x: self.sumLists(x.getForecastModerate()), self.infrastructure)))
		
	def getForecastByGroup(self, name, moderate=True):
		if name=="Consumers" or name=="Infrastructure":
			if moderate:
				return list(map(lambda x: x.getForecastModerate(), self.consumers))
			else:
				return list(map(lambda x: x.getForecast(), self.consumers))
		elif name=="Generators":
			if moderate:
				return list(map(lambda x: x.getForecastModerate(), self.generators))
			else:
				return list(map(lambda x: x.getForecast(), self.generators))

	def getCostsByGroup(self, name):
		if name=="Consumers" or name=="Infrastructure":
			return list(map(lambda x: x.getCosts(), self.consumers))
		elif name=="Generators":
			return list(map(lambda x: x.getCosts(), self.generators))
		elif name=="Extra":
			return sum(map(lambda x: x.getCosts(), self.extra))

	def energyLine(self, summary = False, lose=False):
		if summary:
			forecasts = list(map(lambda x: self.sumLists(x.getForecastModerate()), self.infrastructure))
			energyLine = []
			s = 0
			for i in range(self.stepsCount):
				s1 = 0
				for forecast in forecasts:
					s1 += forecast[i]
				if lose and s1>=0:
					s1 *= (1-self.loseK)
				s += s1
				energyLine.append(s)
			return energyLine
		else:
			if lose:
				return list(map(lambda x: x*(1-self.loseK) if x>=0 else x, self.sumForecasts()))
			else:
				return self.sumForecasts()

	def blackLine(self, summary = False):
			return list(map(lambda x: -x, self.energyLine(False)))

	def blackLineWithLoses(self, summary = False):
			return list(map(lambda x,y: -(y+x), self.loseLine(self.energyLine(False)), self.energyLine(False)))

	def consumersLine(self, summary = False):
		if summary:
			forecasts = list(map(lambda x: x.getForecastModerate(), self.consumers))
			energyLine = []
			s = 0
			for i in range(self.stepsCount):
				for forecast in forecasts:
					s += forecast[i]
				energyLine.append(abs(s))
			return energyLine
		else:
			forecasts = list(map(lambda x: self.sumLists(x.getForecastModerate()), self.consumers))
			return list(map(lambda x: -x, self.sumLists(forecasts)))

	def generatorsLine(self, summary = False):
		if summary:
			forecasts = list(map(lambda x: x.getForecastModerate(), self.generators))
			energyLine = []
			s = 0
			for i in range(self.stepsCount):
				for forecast in forecasts:
					s += forecast[i]
				energyLine.append(s)
			return energyLine
		else:
			forecasts = list(map(lambda x: self.sumLists(x.getForecastModerate()), self.generators))
			return self.sumLists(forecasts)

	def energyLineBalanced(self, summary = False, lose=False):
		capacity = self.capacity
		maxCharge = self.maxCharge
		maxDischarge = self.maxDischarge
		
		capacityLimited = True
		if capacity <= 0:
			capacityLimited = False

		maxChargeLimited = True
		if maxCharge <= 0:
			maxChargeLimited = False

		maxDischargeLimited = True
		if maxDischarge <= 0:
			maxDischargeLimited = False

		# create energy balanced line
		nowCapacity = 0
		powerLineBalanced = []
		sf = self.sumForecasts()
		#print(sf)
		#print(sf)
		for i in range(self.stepsCount):
			#print(i, sf[i])
			sy = sf[i]
			freeEnergy = sy
			
			if sy >= 0: # too many energy
				if maxChargeLimited and sy > maxCharge:
					sy = maxCharge

				if capacityLimited and nowCapacity + sy > capacity:
					if nowCapacity >= capacity:
						nowCapacity = capacity
						sy = 0
					else:
						sy = capacity - nowCapacity

				nowCapacity = nowCapacity + sy

				if summary and i>0:
					if lose:
						powerLineBalanced.append( powerLineBalanced[i-1] + freeEnergy*(1-self.loseK) )
					else:
						powerLineBalanced.append( (powerLineBalanced[i-1] + freeEnergy) )
				elif summary:
					#print(i, freeEnergy, sy)
					if lose:
						powerLineBalanced.append(freeEnergy*(1-self.loseK))
					else:
						powerLineBalanced.append(freeEnergy)
				else:
					if lose:
						powerLineBalanced.append( (freeEnergy - sy) *(1-self.loseK))
					else:
						powerLineBalanced.append(freeEnergy - sy)

			else: # no energy
				if nowCapacity >= maxDischarge and maxDischargeLimited:
					if maxDischarge>=abs(sy):
						sy = 0
						nowCapacity += sy
					else:
						nowCapacity -= maxDischarge
						sy += maxDischarge
				else:
					if nowCapacity>=abs(sy):
						sy = 0
						nowCapacity += sy
					else:
						nowCapacity = 0
						sy += nowCapacity

				if summary and i>0:
					powerLineBalanced.append(powerLineBalanced[i-1] + sy)
				elif summary:
					#print(i, sy)
					powerLineBalanced.append(sy)
				else:
					powerLineBalanced.append(sy)

		#print(powerLineBalanced) 
		return powerLineBalanced

	def loseLine(self, energy, delta=False, dots=False):
		loseNow = 0
		lose = []
		breakoutDots = []
		for i, en in enumerate(energy):
			lose.append(-en*self.loseK if en>0 else 0)
			"""
			if loseNow>=self.loseK:
				breakoutDots.append(i)
				loseNow = 0
			lose.append(-en*loseNow if en>0 else 0)
			loseNow+=self.loseKprogress
			if loseNow>=1:
				loseNow=1
			"""
			
		if delta:
			return list(map(lambda x,y: y+x, lose, energy))
		else:
			if dots:
				return lose, breakoutDots
			else:
				return lose

	def perfectProfit(self):
		return self.sumLists(list(map(lambda x: self.sumLists(x), self.getCostsByGroup("Consumers"))))
	
	def moneyLine(self, energyLine, summary = False):
		autoB = self.autoB
		autoS = self.autoS
		
		gensConsume = self.sumLists(list(map(lambda x: self.sumLists(x), self.getCostsByGroup("Generators"))))
		extraConsume = self.getCostsByGroup("Extra")
		generated = self.sumLists(list(map(lambda x: self.sumLists(x), self.getForecastByGroup("Generators", True))))

		perfectProfit = self.perfectProfit()
		
		moneyLine = []
		
		for i, energy in enumerate(energyLine):
			#print("ener", energy)
			if energy >= 0:
				if summary and i>0:
					moneyLine.append(moneyLine[i-1] + perfectProfit[i] - gensConsume[i] - extraConsume + energy * autoS)
					#print(f"{i}) {moneyLine[i-1]} + {perfectProfit[i]} - {gensConsume} + {energy} * {autoS}")
				else:
					moneyLine.append(perfectProfit[i] - gensConsume[i] - extraConsume + energy * autoS)
					#print(f"{i}) {perfectProfit[i]} - {gensConsume} + {energy} * {autoS}")
			else:
				
				if summary and i>0:
					moneyLine.append(moneyLine[i-1] + perfectProfit[i] - abs(energy)*autoB - gensConsume[i] - extraConsume)
					#moneyLine.append(moneyLine[i-1] + (perfectProfit[i] - lose) - autoBuy - gensConsume)
					#print(f"{i}) ({moneyLine[i-1] + (perfectProfit[i] - lose) - autoBuy - gensConsume}) {moneyLine[i-1]} + ({perfectProfit[i]} - {lose}) - {autoBuy} - {gensConsume}")
				else:
					moneyLine.append(perfectProfit[i] - abs(energy)*autoB - gensConsume[i] - extraConsume)
					#moneyLine.append((perfectProfit[i] - lose) - autoBuy - gensConsume)
					#print(f"{i}) ({(perfectProfit[i] - lose) - autoBuy - gensConsume}) ({perfectProfit[i]} - {lose}) - {autoBuy} - {gensConsume}")
					#print(f"{i}) ({received - autoBuy - gensConsume}) {received} - {autoBuy} - {gensConsume}")

		return moneyLine


class Buffer():
	def __init__(self):
		self.data = dict()

	def get(self, name):
		return self.data[name]

	def set(self, name, value):
		self.data[name] = value
		return True

	def checkSet(self, name, value):
		if self.data.get(name)!=value:
			self.data[name] = value
			return True
		else:
			return False

	def clear(self):
		self.data = dict()


class Graph():
	def __init__(self, buildings):
		self.buildings = buildings
		self.dt = buildings.dt
		self.x = list(range(buildings.dt.stepsCount))
		self.y = dict()
		self.options = dict()
		self.canv = None
		self.maxX = 600
		self.maxY = 600
		self.minX = 10
		self.minY = 0

	def createCanvasBlock(self, frame):
		maxX = self.maxX
		maxY = self.maxY
		minX = self.minX
		minY = self.minY
		canv = self.canv

		partsLen = ((maxX - minX) // len(self.x)) * len(self.x)
		canv = Canvas(frame, width=partsLen + 20, height=partsLen + 20, bg="#333232", highlightthickness=0)
		self.maxX = partsLen + 20
		self.maxY = partsLen + 20
		self.canv = canv
		canv.pack(pady=2, side="top")

	def buildForecastGraph(self):
		self.addLine("Дома А",
					 self.dt.sumLists(self.buildings.getByName("Дома А").getForecastModerate()),
					 color="lightgreen")
		self.addLine("Дома Б",
					 self.dt.sumLists(self.buildings.getByName("Дома Б").getForecastModerate()),
					 color="green")
		self.addLine("Заводы",
					 self.dt.sumLists(self.buildings.getByName("Заводы").getForecastModerate()),
					 color="purple")
		self.addLine("Больницы",
					 self.dt.sumLists(self.buildings.getByName("Больницы").getForecastModerate()),
					 color="red")
		self.addLine("Солнце",
					 self.dt.sumLists(self.buildings.getByName("Солнце").getForecastModerate()),
					 color="yellow")
		self.addLine("Ветер",
					 self.dt.sumLists(self.buildings.getByName("Ветер").getForecastModerate()),
					 color="lightblue")
		self.addLine("Авто закупка/продажа",
					 self.dt.blackLine(),
					 color="black")
		self.addLine("Потери",
					 self.dt.loseLine(self.dt.energyLine()),
					 color="darkred")
		self.drawGraph()

	def buildPowerGraph(self):
		perfectEnergyLine = self.dt.energyLineBalanced(True, True)
		energyLine = self.dt.energyLine(True, True)

		self.addLine("Суммарная энергия",
					 energyLine,
					 color="#0bbdae")
		self.addLine("Идеальная суммарная энергия",
					 perfectEnergyLine,
					 color="#0ced97")

		self.drawGraph()

		self.canv.create_text(140, 10,
							  text=f"Суммарная энергия: {round(energyLine[-1], 1)}",
							  fill="#0bbdae",
							  font=("Consolas", "10"),
							  justify='left')

		self.canv.create_text(175, 30,
							  text=f"Идеальная суммарная энергия: {round(perfectEnergyLine[-1], 1)}",
							  fill="#0ced97",
							  font=("Consolas", "10"),
							  justify='left')
		
	def buildMoneyGraph(self):
		energyLine = self.dt.energyLine(False, True)
		moneyLine = self.dt.moneyLine(energyLine, True)
		
		perfectEnergyLine = self.dt.energyLineBalanced(False, True)
		perfectMoneyLine = self.dt.moneyLine(perfectEnergyLine, True)

		self.addLine("Суммарный доход",
					 moneyLine,
					 color="orange")
		self.addLine("Идеальный суммарный доход",
					 perfectMoneyLine,
					 color="yellow")

		self.drawGraph()

		self.canv.create_text(140, 10,
							  text=f"Суммарный доход: {round(moneyLine[-1], 1)}",
							  fill="orange",
							  font=("Consolas", "10"),
							  justify='left')
			
		self.canv.create_text(175, 30,
							  text=f"Идеальный суммарный доход: {round(perfectMoneyLine[-1], 1)}",
							  fill="yellow",
							  font=("Consolas", "10"),
							  justify='left')

	def buildBalanceGraph(self):
		self.addLine("Авто закупка/продажа",
					 self.dt.blackLine(),
					 color="black")
		self.addLine("Линия потребления",
					 self.dt.consumersLine(),
					 color="blue")
		self.addLine("Линия генерации",
					 self.dt.generatorsLine(),
					 color="lightblue")
		self.addLine("Линия потерь",
					 self.dt.loseLine(self.dt.energyLine()),
					 color="darkred")
		self.drawGraph()
			
	def drawGraph(self, **extra):
		self.canv.delete("all") #clear canv
		
		# include extra
		default = False

		if extra.get("lines") != None:
			lines = extra.get("lines")
		else:
			lines = self.y

		if extra.get("options") != None:
			if extra.get("options") == "default":
				default = True
			else:
				options = extra.get("options")
		else:
			options = self.options

		# Draw process
		maxX = self.maxX
		maxY = self.maxY
		minX = self.minX
		minY = self.minY
		canv = self.canv

		# get highest Y
		highestY = 0
		for line in lines.values():
			if line == None:
				continue
			else:
				line = max(list(map(abs, line)))
				if line > highestY:
					highestY = line

		if highestY == 0:
			print(f"Не все данные введены")
			#print(lines)
			canv.create_text(maxX / 2, maxY / 2, text="Не все данные введены", fill="red", font=("Consolas", "20"))
			return
		highestY = int(highestY) + 1

		# parts
		k = 3
		partX = (maxX - minX) // len(self.x)

		# draw
		for key in lines.keys():
			line = lines[key]
			for i in range(len(line) - 1):
				y = 0
				y1 = 0
				yFromHighest = (line[i] / highestY)
				y1FromHighest = (line[i + 1] / highestY)
				color = ""
				if yFromHighest < 0:
					y = abs(yFromHighest) * (maxY / 2 - 20) + (maxY / 2)
				else:
					y = (maxY / 2) - yFromHighest * (maxY / 2 - 20)
				if y1FromHighest < 0:
					y1 = abs(y1FromHighest) * (maxY / 2 - 20) + (maxY / 2)
					color = "red"
				else:
					y1 = (maxY / 2) - y1FromHighest * (maxY / 2 - 20)
					color = "lightgreen"

				if default:
					canv.create_line((minX + partX * i, y), (minX + partX * (i + 1), y1), fill=color, width=2)
				else:
					canv.create_line((minX + partX * i, y), (minX + partX * (i + 1), y1), fill=options[key]["color"],
									 width=2)

		# FOR Y:
		canv.create_line(minX, maxY, minX, minY, width=2, arrow="last", fill="lightgray")
		r = range(0, highestY + 1, 1)
		mult = 1
		while highestY // (10 * mult) > 0:
			mult = mult * 2
			r = range(0, highestY + 1, 1 * mult)

		for i in r:
			if i == 0:
				continue
			canv.create_line(minX + k, (maxY / 2) - (maxY / 2 - 20) * (int(i) / highestY), minX - k,
							 (maxY / 2) - (maxY / 2 - 20) * (int(i) / highestY), width=2, fill="pink")
			canv.create_line(minX + k, (maxY / 2) + (maxY / 2 - 20) * (int(i) / highestY), minX - k,
							 (maxY / 2) + (maxY / 2 - 20) * (int(i) / highestY), width=2, fill="pink")
			canv.create_text(minX + (k + 12), (maxY / 2) - (maxY / 2 - 20) * (int(i) / highestY), text=str(int(i)),
							 fill="pink", font=("Consolas", "10"))
			canv.create_text(minX + (k + 12), (maxY / 2) + (maxY / 2 - 20) * (int(i) / highestY), text=str(int(i)),
							 fill="pink", font=("Consolas", "10"))

		# FOR X
		canv.create_line(minX, maxY / 2, maxX, maxY / 2, width=2, arrow="last", fill="lightgray")

		for i in self.x:
			if i % 10 == 0:
				canv.create_line(minX + partX * i, maxY / 2 + k, minX + partX * i, maxY / 2 - k, width=2, fill="pink")
				canv.create_text(10 + partX * i, maxY / 2 - (k - 12), text=str(i), fill="pink", font=("Consolas", "10"))
			else:
				canv.create_line(minX + partX * i, maxY / 2 + k, minX + partX * i, maxY / 2 - k, width=2,
								 fill="lightgray")

		self.clearLines()

	def buildGraph(self, tag, infoType):
		if tag == "forecast":
			if infoType=="graph":
				self.buildForecastGraph()
		elif tag == "power":
			if infoType=="graph":
				self.buildPowerGraph()
		elif tag == "money":
			if infoType=="graph":
				self.buildMoneyGraph()
		elif tag == "balance":
			if infoType=="graph":
				self.buildBalanceGraph()
		else:
			self.drawGraph()

	def newX(self, x):
		self.x = x + 1

	def addLine(self, name, values, **options):
		if values == None:
			print(f"График {name} имеет значение None")
		self.y.update({name: [0] + values})
		self.options.update({name: options})

	def clearLines(self):
		self.y = dict()
		self.colors = dict()


class MainMenu():
	def __init__(self):
		self.forecast = None
		self.autoBuy = None
		self.autoSell = None
		self.InfrastBlocks = dict()
		self.usedPlace = []
		self.graphs = []
		self.teamLabels = []
		
	def convertCSV(self):
		path = self.entryPath.get()
		if path[-3:] == "csv":
			values = []
			keys = []

			with open(path, newline='', encoding="utf-8") as f:
				fl = True
				for row in csv.reader(f, delimiter=',', quotechar='"'):
					if fl:
						keys = row
						print("keys", keys)
						fl = False
						for j in keys:
							values.append([])
					else:
						for i, v in enumerate(row):
							values[i].append(v)

			result = dict(zip(keys, values))
			forecast.update(result)
			self.forecast = forecast
			for team in teams:
				for building in team.getAll():
					building.updateForecast()

			TAGS.clear()
			tagGroup = "Ветер"
			TAGS[tagGroup] = []
			for key in forecast.keys():
				print(key)
				if key.count(tagGroup)>0:
					TAGS[tagGroup].append(key)
					
			for block in self.InfrastBlocks.values():
				block.updateTags()

			self.entryPath["fg"] = "green"
		else:
			self.entryPath["fg"] = "red"

	def chooseFilePath(self):
		path = fd.askopenfilename()
		self.entryPath.delete(0, "end")
		if path[-3:] == "csv":
			self.entryPath.insert(0, path)
		else:
			self.entryPath.insert(0, "Не верный файл")
		self.entryPath.update()

		self.convertCSV()

	def importOptions(self):
		path = fd.askopenfilename()
		if path[-5:] == ".json":
			importOpt(path)

	def exportOptions(self):
		exportOpt()

	def createPathBlock(self, window, side):
		frame = ttk.Frame(window, borderwidth=1, relief=SOLID, padding=[8, 10], style="My.TLabel")
		lbl = Label(frame, ws.getStyle("labelTitle", text="Указать путь к файлу csv", width=23))
		lbl.pack(side='top')

		self.entryPath = Entry(frame, ws.getStyle("entryMain"))
		self.entryPath.pack(side='top')

		btn = Button(frame, text="Указать", bg="black", fg="gray", font=("Arial Bold", 15),
					 command=self.chooseFilePath)
		btn1 = Button(frame, text="Подтвердить", bg="black", fg="gray", font=("Arial Bold", 15),
					  command=self.convertCSV)
		btn.pack(side='top', padx=1, pady=5)
		btn1.pack(side='top', padx=1, pady=5)

		lbl = Label(frame, ws.getStyle("labelTitle", text="Импорт настроек", width=23))
		lbl.pack(side='top')

		btn = Button(frame, text="Импорт", bg="black", fg="gray", font=("Arial Bold", 15),
					 command=self.importOptions)
		btn.pack(side='top', padx=1, pady=5)

		lbl = Label(frame, ws.getStyle("labelTitle", text="Экспорт настроек", width=23))
		lbl.pack(side='top')
		btn1 = Button(frame, text="Экспорт", bg="black", fg="gray", font=("Arial Bold", 15),
					 command=self.exportOptions)
		btn1.pack(side='top', padx=1, pady=5)

		frame.pack(side=side, anchor="nw")

	def addOption(self, parent, name, default):
		lbl = Label(parent, ws.getStyle("labelTitle", text=f"{name}:", width=23))
		lbl.pack(side='top')
		entry = Entry(parent, ws.getStyle("entryMain", width=20))
		entry.insert(0, str(default))
		entry.pack(side="top")
		return entry

	def energyBalance(self):
		BalanceWindow(self.window)

	def createGraphBlock(self, window):
		frame = ttk.Frame(window, borderwidth=1, relief=SOLID, padding=[8, 10], style="My.TLabel")
		lbl = Label(frame, ws.getStyle("labelTitle", text="Графики", width=23))
		lbl.pack(side='top')

		btn = Button(frame, ws.getStyle("buttonMain", text="Баланс", command=self.energyBalance))
		btn.pack(side='top', padx=1, pady=5)

		btn = Button(frame, ws.getStyle("buttonMain", text="Построить", command=self.buildGraph))
		btn.pack(side='top', padx=1, pady=5)

		self.autoBuy = self.addOption(frame, "Цена автозакупки", 10)
		self.autoSell = self.addOption(frame, "Цена автопродажи", 1)
		self.capacity = self.addOption(frame, "Ёмкость заряда", 150)
		self.maxCharge = self.addOption(frame, "Макс. заряд", 10)
		self.maxDischarge = self.addOption(frame, "Макс. разряд", 10)
		self.loseK = self.addOption(frame, "Сброс потерь при", 0.7)
		self.loseKprogress = self.addOption(frame, "Прогресс потерь", 0.1)

		frame.grid(column=1, row=1, padx=1, pady=1)

	def buildGraph(self):
		for team in teams:
			for build in team.getAll():
				build.clearData()
				
		for block in self.InfrastBlocks.values():
			block.updateData()

		for team in teams:
			team.dt.update(autoB = float(self.autoBuy.get()),
						   autoS = float(self.autoSell.get()),
						   capacity = float(self.capacity.get()),
						   maxCharge = float(self.maxCharge.get()),
						   maxDischarge = float(self.maxDischarge.get()),
						   loseK = float(self.loseK.get()),
						   loseKprogress = float(self.loseKprogress.get())
						   )

		for teamGraphs in self.graphs:
			teamGraphs[0].buildGraph("forecast", "graph")
			teamGraphs[1].buildGraph("power", "graph")
			teamGraphs[2].buildGraph("money", "graph")
			teamGraphs[3].buildGraph("balance", "graph")

	def destroyTeam(self, teamBlock, teamID, graphsID, teamLabelsID):
		teamBlock.destroy()
		teams.remove(teamID)
		self.graphs.remove(graphsID)
		i = self.teamLabels.index(teamLabelsID)
		self.teamLabels.remove(teamLabelsID)
		for lbl in self.teamLabels:
			num = int(lbl["text"].split("№")[1])
			if num>i:
				lbl["text"] = f"Команда №{num-1}"
				
		self.mainCanvas.configure(scrollregion=self.mainCanvas.bbox("all"))
##		self.mainCanvas.bind("<Configure>", lambda e: self.mainCanvas.configure(scrollregion=self.mainCanvas.bbox("all")))
##		self.scrollbarx.configure(command=self.mainCanvas.xview)
##		self.scrollbary.configure(command=self.mainCanvas.yview)


	def resize(self, window, mainCanvas):
		mainCanvas.configure(width=window.winfo_width()-20, height=window.winfo_height()-20)
		mainCanvas.configure(scrollregion=mainCanvas.bbox("all"))
		
	def newTeam(self):
		parent = self.cnvFrame
		
		teams.append(Buildings())
		
		Infrastructure("Дома А", 2, teams[-1])
		Infrastructure("Дома Б", 2, teams[-1])
		Infrastructure("Заводы", 1, teams[-1])
		Infrastructure("Больницы", 0, teams[-1])
		
		Generators("Солнце", teams[-1])
		Generators("Ветер", teams[-1])

		Extra("Подстанция", teams[-1])
		Extra("Накопитель", teams[-1])
		
		if forecast!={}:
			for team in teams:
				for building in team.getAll():
					building.updateForecast()

		graphs = []
		graphs.append(Graph(teams[-1]))
		graphs.append(Graph(teams[-1]))
		graphs.append(Graph(teams[-1]))
		graphs.append(Graph(teams[-1]))

		self.btnPlusTeam.pack_forget()
		
		frame = ttk.Frame(parent, borderwidth=0, relief="flat", padding=[2, 0], style="My.TLabel")
		lbl = Label(frame, ws.getStyle("labelTitle", text=f"Команда №{len(teams)-1}", width=23))
		self.teamLabels.append(lbl)
		lbl.pack(side='top')
		btnMinusTeam = Button(frame, ws.getStyle("buttonMain", text="-", width=47, command=lambda: self.destroyTeam(frame, teams[-1], graphs, lbl)))
		btnMinusTeam.pack(side='top')

		for graph in graphs:
			graph.createCanvasBlock(frame)
		
		frame.pack(side="left", anchor="nw")
		self.btnPlusTeam.pack(side="left")

		self.graphs.append(graphs)
		
		self.mainCanvas.configure(scrollregion=self.mainCanvas.bbox("all"))

	def activate(self):
		# create window
		window = Tk()
		self.window = window

		sw = window.winfo_screenwidth() // 2 - 20
		sh = window.winfo_screenheight()-90

		window.title("НТО аналитик")
		window.geometry(f'{sw}x{sh}')
		window.resizable(width=True, height=True)
		window.configure(bg='#1c1c1c')
		window.bind("<Return>", lambda e: mm.buildGraph())

		# frames style
		ttk.Style().configure("My.TLabel", font="Arial Bold 15", foreground="gray", padding=0, background="#1c1c1c")
		ttk.Style().configure("MyTeam.TLabel", font="Arial Bold 15", foreground="black", padding=0, background="lightgreen")
		ttk.Style().configure("EnemyTeam.TLabel", font="Arial Bold 15", foreground="black", padding=0, background="pink")
		
		# frame for mainCanvas
		frame = ttk.Frame(window, borderwidth=0, relief="flat", padding=[0, 0], style="My.TLabel")
		frame.pack(side="top", fill="y", anchor="s")

		# mainFrame and mainCanvas with Scrollbar
		mainCanvas = Canvas(frame, bg="#1c1c1c", highlightthickness=0, width=sw, height=sh)
		mainCanvas.pack(side="left", anchor="nw", fill="both")
		self.mainCanvas = mainCanvas

		scrollbary = Scrollbar(frame, orient="vertical", command=mainCanvas.yview)

		scrollbarx = Scrollbar(window, orient="horizontal", command=mainCanvas.xview)
		scrollbarx.pack(side="top", fill="x", anchor="s")
		scrollbary.pack(side="right", fill="y", anchor="e")

		self.scrollbary = scrollbary
		self.scrollbarx = scrollbarx

		mainCanvas.configure(yscrollcommand=scrollbary.set, xscrollcommand=scrollbarx.set)
		mainCanvas.configure(scrollregion=mainCanvas.bbox("all"))

		mainFrame = ttk.Frame(mainCanvas, borderwidth=0, relief="flat", padding=[0, 0], style="My.TLabel")
		mainCanvas.create_window((0, 0), window=mainFrame, anchor="nw")

		frame.bind("<Configure>", lambda e: self.resize(window,mainCanvas))
		
		# building frame
		buildingsFrame = ttk.Frame(mainFrame, borderwidth=0, relief="flat", padding=[0, 0], style="My.TLabel")

		rightFrame = ttk.Frame(buildingsFrame, borderwidth=0, relief="flat", padding=[0, 0], style="My.TLabel")
		self.InfrastBlocks["Дома А"] = InfrastBlock(rightFrame, "Дома А", "Дома А", "top")
		self.InfrastBlocks["Дома Б"] = InfrastBlock(rightFrame, "Дома Б", "Дома Б", "top")
		self.InfrastBlocks["Заводы"] = InfrastBlock(rightFrame, "Заводы", "Заводы", "top")
		self.InfrastBlocks["Больницы"] = InfrastBlock(rightFrame, "Больницы", "Больницы", "top")
		rightFrame.pack(side="left", anchor="nw")

		self.createPathBlock(rightFrame, "left")

		leftFrame = ttk.Frame(buildingsFrame, borderwidth=0, relief="flat", padding=[0, 0], style="My.TLabel")
		self.InfrastBlocks["Солнце"] = InfrastBlock(leftFrame, "Солнце", "Солнечные панели", "top")
		self.InfrastBlocks["Ветер"] = InfrastBlock(leftFrame, "Ветер", "Ветряные мельницы", "top")
		leftFrame.pack(side="left", anchor="nw")

		superLeftFrame = ttk.Frame(buildingsFrame, borderwidth=0, relief="flat", padding=[0, 0], style="My.TLabel")
		self.InfrastBlocks["Подстанция"] = InfrastBlock(leftFrame, "Подстанция", "Подстанции", "top", onlyPrice=True)
		self.InfrastBlocks["Накопитель"] = InfrastBlock(leftFrame, "Накопитель", "Накопители", "top", onlyPrice=True)
		superLeftFrame.pack(side="left", anchor="nw")

		buildingsFrame.grid(column=0, row=0, padx=1, pady=1, columnspan=1, sticky="nw")
		buildingsFrame.bind("<Configure>", lambda e: mainCanvas.configure(scrollregion=mainCanvas.bbox("all")))

		self.cnvFrame = ttk.Frame(mainFrame, borderwidth=0, relief="flat", padding=[0, 0], style="My.TLabel")

		self.btnPlusTeam = Button(self.cnvFrame, ws.getStyle("buttonMain", height=95, width=3, text="+", command=self.newTeam))
		self.btnPlusTeam.pack(side="left", anchor="w")
		self.newTeam()

		self.cnvFrame.grid(column=1, row=0, padx=1, pady=1, rowspan=20, sticky="nw")
		self.cnvFrame.bind("<Configure>", lambda e: mainCanvas.configure(scrollregion=mainCanvas.bbox("all")))

		# optionsFrame
		optionsFrame = ttk.Frame(mainFrame, borderwidth=0, relief=SOLID, padding=[0, 0], style="My.TLabel")
		self.createGraphBlock(optionsFrame)
		optionsFrame.grid(column=0, row=1, padx=1, pady=1, columnspan=1, sticky="nw")

		window.mainloop()


class BalanceWindow(Toplevel):
	def __init__(self, parent):
		super().__init__(parent)
		self.checkBoxes = {}

		self.createTeam()

		self.configure(bg='#1c1c1c')

		frameValues = ttk.Frame(self, borderwidth=0, relief="flat", padding=[0, 0], style="My.TLabel")
		frameValues.pack(side="left", anchor="nw")
		frameResult = ttk.Frame(self, borderwidth=0, relief="flat", padding=[0, 0], style="My.TLabel")
		frameResult.pack(side="left", anchor="nw")
		frameOptions = ttk.Frame(self, borderwidth=0, relief="flat", padding=[0, 0], style="My.TLabel")
		frameOptions.pack(side="left", anchor="nw")

		frameValues, canvasValues = self.newCanv(frameValues, scrollx = False, scrolly = True)
		frameValues.bind("<Configure>", lambda e: self.resize(frameValues, canvasValues, 750, 3))

		frameResult, canvasResult = self.newCanv(frameResult, scrollx = False, scrolly = True)
		frameResult.bind("<Configure>", lambda e: self.resize(frameResult, canvasResult, 750, 3))
		self.frameResult = frameResult

		frameOptions, canvasOptions = self.newCanv(frameOptions, scrollx = False, scrolly = True)
		frameOptions.bind("<Configure>", lambda e: self.resize(frameOptions, canvasOptions, 750, 3))

		for infrBlock in mm.InfrastBlocks.values():
			self.checkBoxes[infrBlock.buildingName] = IntVar()
			self.checkBoxes[infrBlock.buildingName].set(1)
			enabled_checkbutton = Checkbutton(frameOptions, text=str(infrBlock.buildingName), variable=self.checkBoxes[infrBlock.buildingName])
			enabled_checkbutton.pack(padx=6, pady=6, anchor="w")

		key = "Сорт. по валюте"
		self.checkBoxes[key] = IntVar()
		self.checkBoxes[key].set(1)
		enabled_checkbutton = Checkbutton(frameOptions, text=str(key), variable=self.checkBoxes[key])
		enabled_checkbutton.pack(padx=6, pady=6, anchor="w")

		key = "Сорт. по энергии"
		self.checkBoxes[key] = IntVar()
		self.checkBoxes[key].set(1)
		enabled_checkbutton = Checkbutton(frameOptions, text=str(key), variable=self.checkBoxes[key])
		enabled_checkbutton.pack(padx=6, pady=6, anchor="w")

		self.entries = dict()
		defaultValues = {
			"Дома":9,
			"Заводы":3,
			"Больницы":3,
			"Солнце":5,
			"Ветер":3
		}
		for infrBlock in mm.InfrastBlocks.values():
			lbl = Label(frameValues, ws.getStyle("labelTitle", text=f"Количество {infrBlock.buildingName}:"))
			lbl.pack(side="top")
			self.entries[infrBlock.buildingName] = Entry(frameValues, ws.getStyle("entryMain"))
			self.entries[infrBlock.buildingName].insert(0, defaultValues[infrBlock.buildingName])
			self.entries[infrBlock.buildingName].pack(side="top", anchor="nw", fill="x")
		lbl = Label(frameValues, ws.getStyle("labelTitle", text="Номер моей команды:"))
		lbl.pack(side="top")
		self.entries["teamID"] = Entry(frameValues, ws.getStyle("entryMain"))
		self.entries["teamID"].insert(0, 0)
		self.entries["teamID"].pack(side="top", anchor="nw", fill="x")

		lbl = Label(frameValues, ws.getStyle("labelTitle", text="Минимальная энергия"))
		lbl.pack(side="top")
		self.entries["energyMin"] = Entry(frameValues, ws.getStyle("entryMain"))
		self.entries["energyMin"].insert(0, 100)
		self.entries["energyMin"].pack(side="top", anchor="nw", fill="x")

		lbl = Label(frameValues, ws.getStyle("labelTitle", text="Минимальная сумма:"))
		lbl.pack(side="top")
		self.entries["moneyMin"] = Entry(frameValues, ws.getStyle("entryMain"))
		self.entries["moneyMin"].insert(0, 100)
		self.entries["moneyMin"].pack(side="top", anchor="nw", fill="x")

##		lbl = Label(frameValues, ws.getStyle("labelTitle", text="Ход аукциона:"))
##		lbl.pack(side="top")
##		self.entries["process"] = Entry(frameValues, ws.getStyle("entryMain"))
##		self.entries["process"].insert(0, "n")
##		self.entries["process"].pack(side="top", anchor="nw", fill="x")

		lbl = Label(frameValues, ws.getStyle("labelTitle", text="Прогноз на кол. ходов:"))
		lbl.pack(side="top")
		self.entries["maxBuildings"] = Entry(frameValues, ws.getStyle("entryMain"))
		self.entries["maxBuildings"].pack(side="top", anchor="nw", fill="x")
		
		btn = Button(frameValues, ws.getStyle("buttonMain", text="Исследовать", command=self.findBest))
		btn.pack(side='top', padx=1, pady=5)
		
		allInfrastructure = 0
		myInfrastructure =0
		for key in mm.InfrastBlocks.keys():
			data = mm.InfrastBlocks[key].updateData(False)
			allInfrastructure += int(self.entries[key].get())
			if data.get( int(self.entries["teamID"].get()) )==None:
				myInfrastructure += 0
			else:
				myInfrastructure += len(data[int(self.entries["teamID"].get())])
		#self.entries["maxBuildings"].insert(0, str(allInfrastructure-myInfrastructure))
		self.entries["maxBuildings"].insert(0, str(4))

	def newCanv(self, parent, scrollx = True, scrolly = True):
		#window
		frame = ttk.Frame(parent, borderwidth=0, relief="flat", padding=[0, 0], style="My.TLabel")
		frame.pack(side="top", fill="y", anchor="s")

		# mainFrame and mainCanvas with Scrollbar
		mainCanvas = Canvas(frame, bg="#1c1c1c", highlightthickness=0, width =200)
		mainCanvas.pack(side="left", anchor="nw", fill="both")

		if scrolly:
			scrollbary = Scrollbar(frame, orient="vertical", command=mainCanvas.yview)
			scrollbary.pack(side="right", fill="y", anchor="e")
			mainCanvas.configure(yscrollcommand=scrollbary.set)
		if scrollx:
			scrollbarx = Scrollbar(parent, orient="horizontal", command=mainCanvas.xview)
			scrollbarx.pack(side="top", fill="x", anchor="s")
			mainCanvas.configure(xscrollcommand=scrollbarx.set)

		mainFrame = ttk.Frame(mainCanvas, borderwidth=0, relief="flat", padding=[0, 0], style="My.TLabel")
		mainCanvas.create_window((0, 0), window=mainFrame, anchor="nw")

		self.mainFrame = mainFrame

		return mainFrame, mainCanvas

	def show(self, data):
		for child in self.frameResult.winfo_children():
			child.destroy()
		colors = {
			"Дома":"green",
			"Заводы":"purple",
			"Больницы":"red",
			"Ветер":"lightblue",
			"Солнце":"yellow",
			"Разность сумм":"orange",
			"Разность энергий":"#0bbdae"
		}
		num = 1
		for key in data.keys():
			frame = ttk.Frame(self.frameResult, borderwidth=0, relief="solid", padding=[2, 2], style="My.TLabel")
			frame.pack(side="top", anchor="nw", pady=2, padx=3)
			lbl = Label(frame, ws.getStyle("labelTitle", text=f"№{num}"))
			lbl.pack(side="top", anchor="nw")
			lbl = Label(frame, ws.getStyle("labelTitle", text=f"Выгода: {round(key,2)}"))
			lbl.pack(side="top", anchor="nw")
			for key1 in data[key]:
				lbl = Label(frame, ws.getStyle("labelTitle", text=f"{key1}: {data[key][key1]}", fg=colors[key1]))
				lbl.pack(side="top", anchor="nw")
			num+=1

	def createTeam(self):
		self.predictionTeam = Buildings()
		
		Infrastructure("Дома", 2, self.predictionTeam, False)
		Infrastructure("Заводы", 1, self.predictionTeam, False)
		Infrastructure("Больницы", 0, self.predictionTeam, False)
		
		Generators("Солнце", self.predictionTeam, False)
		Generators("Ветер", self.predictionTeam, False)

		Extra("Подстанция", self.predictionTeam, False)
		Extra("Накопитель", self.predictionTeam, False)

		for key in forecast.keys():
			self.predictionTeam.getByName(key).updateForecast()

	def findBest(self):
		def finding(curVal, maxBuildings, buildingCount, first):
			#print(curVal)
			results = []
			afterMoney = 0
			afterEnergy = 0
			
			if not first:
				self.clearTeamData()

				data = dict(zip(list(curVal.keys()), list(map(lambda x,y: x-y, list(allInfrastructure.values()), list(curVal.values())))))
				for key in freeInfrastructure.keys():
					self.predictionTeam.getByName(key).setData([[5,1,0]]*data[key])

				afterMoney = self.predictionTeam.dt.moneyLine(self.predictionTeam.dt.energyLine(False, True), True)[-1]
				afterEnergy = self.predictionTeam.dt.energyLine(True, True)[-1]
				k = (afterMoney-beforeMoney)*(afterEnergy-beforeEnergy)

				#print(curVal, freeInfrastructure, data, self.predictionTeam.dt.energyLine(True)[-1])
				if (afterEnergy-beforeEnergy)<float(self.entries["energyMin"].get()):
					return None
			
			if sum(list(curVal.values()))<=0 or maxBuildings<buildingCount:
				if (afterMoney-beforeMoney)>float(self.entries["moneyMin"].get()):
					return [curVal]
				else:
					return None
			
			else:
				for key in curVal.keys():
					if curVal[key]>0:
						newVal = curVal.copy()
						newVal[key] = newVal[key]-1
						res = finding(newVal, maxBuildings, buildingCount+1, False)
						if res!=None:
							for r in res:
								if r not in results:
									results.append(r)

			return results 
			
		freeInfrastructure = dict()
		myInfrastructure = dict()
		allInfrastructure = dict()
		
		for key in mm.InfrastBlocks.keys():
			data = mm.InfrastBlocks[key].updateData(False)
			allInfrastructure[key] = int(self.entries[key].get())
			
			if data.get( int(self.entries["teamID"].get()) )==None:
				myInfrastructure[key] = 0
			else:
				myInfrastructure[key] = len(data[int(self.entries["teamID"].get())])

			if len(list(data.values()))==0:
				freeInfrastructure[key] = int(self.entries[key].get())
			else:
				freeInfrastructure[key] = int(self.entries[key].get()) - len(list(data.values())[0])
			
		#res = finding(freeInfrastructure, sum(list(freeInfrastructure.values())), 1, [])

		self.clearTeamData()
		for key in myInfrastructure.keys():
			self.predictionTeam.getByName(key).setData([[5,1,0]]*myInfrastructure[key])

		beforeMoney = self.predictionTeam.dt.moneyLine(self.predictionTeam.dt.energyLine(False, True), True)[-1]
		beforeEnergy = self.predictionTeam.dt.energyLine(True, True)[-1]

		freeInfrastructureModify = freeInfrastructure.copy()
		for key in freeInfrastructureModify.keys():
			if not bool(self.checkBoxes[key].get()):
				freeInfrastructureModify[key] = 0

		allInfrastructureModify = allInfrastructure.copy()
		for key in allInfrastructureModify.keys():
			if not bool(self.checkBoxes[key].get()):
				allInfrastructureModify[key] = myInfrastructure[key]
				
		res = finding(freeInfrastructureModify, int(self.entries["maxBuildings"].get()), 1, True)
		if res==None:
			return None
		#print(res)

		result = dict()
		
		for variant in res:
			self.clearTeamData()
			variant = dict(zip(list(variant.keys()), list(map(lambda x,y,z: x-y-z, list(allInfrastructureModify.values()), list(variant.values()), list(myInfrastructure.values())))))
			for key in variant.keys():
				self.predictionTeam.getByName(key).setData([[5,1,0]]*variant[key])
			afterMoney = self.predictionTeam.dt.moneyLine(self.predictionTeam.dt.energyLine(False, True), True)[-1]
			afterEnergy = self.predictionTeam.dt.energyLine(True, True)[-1]

			f = True
			f1 = True
			if bool(self.checkBoxes["Сорт. по валюте"].get()):
				dm = (afterMoney-beforeMoney)
			else:
				dm = 1
				f = False
			if bool(self.checkBoxes["Сорт. по энергии"].get()):
				de = (afterEnergy-beforeEnergy)
			else:
				de = 1
				f1 = False
			if (dm<float(self.entries["moneyMin"].get()) and f) or (de<float(self.entries["energyMin"].get()) and f1):
				continue
			k = dm*de
			variant["Разность сумм"] = round((afterMoney-beforeMoney), 2)
			variant["Разность энергий"] = round((afterEnergy-beforeEnergy), 2)
			result[k] = variant
		self.show(dict(sorted(result.items(), reverse=True)))

	def resize(self, frame, mainCanvas, a, b):
		width = 0
		height = 0
		if frame.winfo_width()>a:
			width = a
		else:
			width=frame.winfo_width()
		if frame.winfo_height()>frame._root().winfo_screenheight()/b:
			height = frame._root().winfo_screenheight()/b
		else:
			height=frame.winfo_height()
		mainCanvas.configure(width=width, height = height)
		mainCanvas.configure(scrollregion=mainCanvas.bbox("all"))

	def clearTeamData(self):
		for build in self.predictionTeam.getAll():
			build.clearData()

	def prepare(self):
		for team in teams:
			for build in team.getAll():
				build.clearData()
				
		for block in mm.InfrastBlocks.values():
			block.updateData(False)

		for team in teams:
			team.dt.update(autoB = float(mm.autoBuy.get()),
					  autoS = float(mm.autoSell.get()),
					  capacity = float(mm.capacity.get()),
					  maxCharge = float(mm.maxCharge.get()),
					  maxDischarge = float(mm.maxDischarge.get()))
		

class InformWindow(Toplevel):
	def __init__(self, mode, parent, infrastBlock, buildingName, block=None):
		super().__init__(parent)
		self.infrastBlock = infrastBlock
		self.buildingName = buildingName
		self.block = block
		self.mode = mode
		
		self.configure(bg='#1c1c1c')

		if mode=="prediction":
			lbl = Label(self, ws.getStyle("labelMegatitle", text=f"Изменения при покупке {buildingName}"))
		elif mode=="drop":
			lbl = Label(self, ws.getStyle("labelMegatitle", text=f"Изменения при сбросе данного {buildingName}\nЦена: {block[1][0][2].get()}, Коэф: {block[1][1][2].get()}, Порог: {block[1][2][2].get()}"))
			
		lbl.pack(side='top', anchor="n")

		#window
		frame = ttk.Frame(self, borderwidth=0, relief="flat", padding=[0, 0], style="My.TLabel")
		frame.pack(side="top", fill="y", anchor="s")

		# mainFrame and mainCanvas with Scrollbar
		mainCanvas = Canvas(frame, bg="#1c1c1c", highlightthickness=0, width =200)
		mainCanvas.pack(side="left", anchor="nw", fill="both")
		self.mainCanvas = mainCanvas

		scrollbary = Scrollbar(frame, orient="vertical", command=mainCanvas.yview)

		scrollbarx = Scrollbar(self, orient="horizontal", command=mainCanvas.xview)
		scrollbarx.pack(side="top", fill="x", anchor="s")
		scrollbary.pack(side="right", fill="y", anchor="e")

		mainCanvas.configure(yscrollcommand=scrollbary.set, xscrollcommand=scrollbarx.set)

		mainFrame = ttk.Frame(mainCanvas, borderwidth=0, relief="flat", padding=[0, 0], style="My.TLabel")
		mainCanvas.create_window((0, 0), window=mainFrame, anchor="nw")

		self.mainFrame = mainFrame

		mainFrame.bind("<Configure>", lambda e: self.resize(mainFrame, mainCanvas))

		self.el = {}
		self.ml = {}
		self.pel = {}
		self.pml = {}
		self.profit = {}

		self.prepare(prediction=False)
		self.fillData()

		if mode=="prediction":
			self.prepare(prediction=True, drop=False)
		elif mode=="drop":
			self.prepare(prediction=False, drop=True)
		self.fillData()

		self.prepare(prediction=False)

		self.teamsFrame = ttk.Frame(mainFrame, borderwidth=1, relief="flat", padding=[8, 10], style="My.TLabel")
		self.teamsFrame.pack(side="top", anchor="nw")

		if mode=="prediction":
			self.predictionInfo()
		elif mode=="drop":
			self.dropInfo()

		btn = Button(mainFrame, ws.getStyle("buttonMain", text="Закрыть", command=self.destroy))
		btn.pack(side='top', padx=1, pady=5)
		
		self.grab_set()

	def predictionInfo(self):
		"""
		newForecast = list(map(lambda x: x+0.82*(self.special[self.name]["miningPrice"]-price)**2.6, forecast))
		newForecast = list(map(lambda x: x+0.24*(self.special[self.name]["miningPrice"]-price)**2.2, forecast))
		"""
		for i in range(len(teams)):
			criterions = dict()
			if self.buildingName=="Дома А" or self.buildingName=="Дома Б":
				iterations = 1
				minimalProfit = 0
				minimalProfitPerfect = 0
				newPrice = float(self.infrastBlock.prediction[0].get())
				print("Ну давай блять искать", self.buildingName)
				for j in range(iterations):
					potencialMinus = (self.ml[i][2][-1] - self.ml[i][0][-1])
					newMinProf = round(-(potencialMinus/(self.profit[i][3]-self.profit[i][1]))*newPrice+newPrice, 3)
					minimalProfit += round(newMinProf, 3)

					potencialMinusPerfect = (self.pml[i][2][-1] - self.pml[i][0][-1])
					newMinimalProfitPerfect = round(-(potencialMinusPerfect/(self.profit[i][3]-self.profit[i][1]))*newPrice+newPrice, 3)
					minimalProfitPerfect += round(newMinimalProfitPerfect, 3)

					self.el[i].clear()
					self.ml[i].clear()
					self.pel[i].clear()
					self.pml[i].clear()
					self.profit[i].clear()

					self.prepare(prediction=False, drop=False)
					self.fillData()

					newPrice = newMinProf
					self.prepare(prediction=True, drop=False, price=newMinProf)
					self.fillData()

				self.el[i].clear()
				self.ml[i].clear()
				self.pel[i].clear()
				self.pml[i].clear()
				self.profit[i].clear()
				self.prepare(prediction=False, drop=False)
				self.fillData()
				self.prepare(prediction=True, drop=False)
				self.fillData()
				self.prepare(prediction=False, drop=False)
				
				minimalProfit = minimalProfit/iterations
				minimalProfitPerfect = minimalProfitPerfect/iterations


			elif type(teams[i].getByName(self.buildingName)).__name__=="Infrastructure":
				potencialMinus = (self.ml[i][2][-1] - self.ml[i][0][-1])
				minimalProfit = round(-(potencialMinus/(self.profit[i][3]-self.profit[i][1]))*float(self.infrastBlock.prediction[0].get())+float(self.infrastBlock.prediction[0].get()), 3)

				potencialMinusPerfect = (self.pml[i][2][-1] - self.pml[i][0][-1])
				minimalProfitPerfect = round(-(potencialMinusPerfect/(self.profit[i][3]-self.profit[i][1]))*float(self.infrastBlock.prediction[0].get())+float(self.infrastBlock.prediction[0].get()), 3)
			elif type(teams[i].getByName(self.buildingName)).__name__=="Generators":
				potencialMinus = float(self.infrastBlock.prediction[0].get())*100
				minimalProfit = round(((self.ml[i][2][-1] - self.ml[i][0][-1])/potencialMinus)*float(self.infrastBlock.prediction[0].get())+float(self.infrastBlock.prediction[0].get()), 3)
				
				minimalProfitPerfect = round(((self.pml[i][2][-1] - self.pml[i][0][-1])/potencialMinus)*float(self.infrastBlock.prediction[0].get())+float(self.infrastBlock.prediction[0].get()), 3)
				
			
			averDelta = (sum(self.el[i][3])/len(self.el[i][3])) - (sum(self.el[i][1])/len(self.el[i][1]))
			summaryDelta = self.el[i][2][-1] - self.el[i][0][-1]

			name = "Энергия"
			criterions[name] = dict()
			criterions[name]["Суммарное изменение"] = round(summaryDelta, 3)
			criterions[name]["Новая сумма"] = round(self.el[i][2][-1], 3)
			criterions[name]["Среднее изменение"] = round(averDelta, 3)
			criterions[name]["Новое среднее"] = round((sum(self.el[i][3])/len(self.el[i][3])), 3)
			criterions[name]["color"] = "#0bbdae"
			
			averDelta = (sum(self.ml[i][3])/len(self.ml[i][3])) - (sum(self.ml[i][1])/len(self.ml[i][1]))
			summaryDelta = self.ml[i][2][-1] - self.ml[i][0][-1]

			name = "Доход"
			criterions[name] = dict()
			criterions[name]["Суммарное изменение"] = round(summaryDelta, 3)
			criterions[name]["Новая сумма"] = round(self.ml[i][2][-1], 3)
			criterions[name]["Среднее изменение"] = round(averDelta, 3)
			criterions[name]["Новое среднее"] = round((sum(self.ml[i][3])/len(self.ml[i][3])), 3)
			criterions[name]["color"] = "orange"
			
			averDelta = (sum(self.pel[i][3])/len(self.pel[i][3])) - (sum(self.pel[i][1])/len(self.pel[i][1]))
			summaryDelta = self.pel[i][2][-1] - self.pel[i][0][-1]

			name = "Идеальная энергия"
			criterions[name] = dict()
			criterions[name]["Суммарное изменение"] = round(summaryDelta, 3)
			criterions[name]["Новая сумма"] = round(self.pel[i][2][-1], 3)
			criterions[name]["Среднее изменение"] = round(averDelta, 3)
			criterions[name]["Новое среднее"] = round((sum(self.pel[i][3])/len(self.pel[i][3])), 3)
			criterions[name]["color"] = "#0ced97"
			
			averDelta = (sum(self.pml[i][3])/len(self.pml[i][3])) - (sum(self.pml[i][1])/len(self.pml[i][1]))
			summaryDelta = self.pml[i][2][-1] - self.pml[i][0][-1]

			name = "Идеальный доход"
			criterions[name] = dict()
			criterions[name]["Суммарное изменение"] = round(summaryDelta, 3)
			criterions[name]["Новая сумма"] = round(self.pml[i][2][-1], 3)
			criterions[name]["Среднее изменение"] = round(averDelta, 3)
			criterions[name]["Новое среднее"] = round((sum(self.pml[i][3])/len(self.pml[i][3])), 3)
			criterions[name]["color"] = "yellow"

			name = "Дополнительно"
			criterions[name] = dict()
			criterions[name]["Минимальная доходность"] = round(minimalProfit, 3)
			criterions[name]["Минимальная доходность (идеал)"] = round(minimalProfitPerfect, 3)
			criterions[name]["color"] = "white"

			self.addTeam(i, criterions)

	def dropInfo(self):
		i = int(self.block[1][3][2].get())
		
		criterions = dict()

		print(len(self.el[i]))
			
		averDelta = (sum(self.el[i][3])/len(self.el[i][3])) - (sum(self.el[i][1])/len(self.el[i][1]))
		summaryDelta = self.el[i][2][-1] - self.el[i][0][-1]

		name = "Энергия"
		criterions[name] = dict()
		criterions[name]["Суммарное изменение"] = round(summaryDelta, 3)
		criterions[name]["Новая сумма"] = round(self.el[i][2][-1], 3)
		criterions[name]["Среднее изменение"] = round(averDelta, 3)
		criterions[name]["Новое среднее"] = round((sum(self.el[i][3])/len(self.el[i][3])), 3)
		criterions[name]["color"] = "#0bbdae"
			
		averDelta = (sum(self.ml[i][3])/len(self.ml[i][3])) - (sum(self.ml[i][1])/len(self.ml[i][1]))
		summaryDelta = self.ml[i][2][-1] - self.ml[i][0][-1]

		name = "Доход"
		criterions[name] = dict()
		criterions[name]["Суммарное изменение"] = round(summaryDelta, 3)
		criterions[name]["Новая сумма"] = round(self.ml[i][2][-1], 3)
		criterions[name]["Среднее изменение"] = round(averDelta, 3)
		criterions[name]["Новое среднее"] = round((sum(self.ml[i][3])/len(self.ml[i][3])), 3)
		criterions[name]["color"] = "orange"
			
		averDelta = (sum(self.pel[i][3])/len(self.pel[i][3])) - (sum(self.pel[i][1])/len(self.pel[i][1]))
		summaryDelta = self.pel[i][2][-1] - self.pel[i][0][-1]

		name = "Идеальная энергия"
		criterions[name] = dict()
		criterions[name]["Суммарное изменение"] = round(summaryDelta, 3)
		criterions[name]["Новая сумма"] = round(self.pel[i][2][-1], 3)
		criterions[name]["Среднее изменение"] = round(averDelta, 3)
		criterions[name]["Новое среднее"] = round((sum(self.pel[i][3])/len(self.pel[i][3])), 3)
		criterions[name]["color"] = "#0ced97"
			
		averDelta = (sum(self.pml[i][3])/len(self.pml[i][3])) - (sum(self.pml[i][1])/len(self.pml[i][1]))
		summaryDelta = self.pml[i][2][-1] - self.pml[i][0][-1]

		name = "Идеальный доход"
		criterions[name] = dict()
		criterions[name]["Суммарное изменение"] = round(summaryDelta, 3)
		criterions[name]["Новая сумма"] = round(self.pml[i][2][-1], 3)
		criterions[name]["Среднее изменение"] = round(averDelta, 3)
		criterions[name]["Новое среднее"] = round((sum(self.pml[i][3])/len(self.pml[i][3])), 3)
		criterions[name]["color"] = "yellow"

		self.addTeam(i, criterions)

	def resize(self, frame, mainCanvas):
		width = 0
		height = 0
		if frame.winfo_width()>900:
			width = 900
		else:
			width=frame.winfo_width()
		if frame.winfo_height()>frame._root().winfo_screenheight()-20:
			height = frame._root().winfo_screenheight()-20
		else:
			height=frame.winfo_height()-20
			
		mainCanvas.configure(width=width, height = height)
		mainCanvas.configure(scrollregion=mainCanvas.bbox("all"))

	def fillData(self):
		for i, team in enumerate(teams):
			if self.mode == "drop":
				i = int(self.block[1][3][2].get())
				team = teams[i]

			if self.el.get(i)==None:
				self.el[i] = []
			self.el[i].append(team.dt.energyLine(True, True))
			self.el[i].append(team.dt.energyLine(False, True))

			if self.ml.get(i)==None:
				self.ml[i] = []
			self.ml[i].append(team.dt.moneyLine(team.dt.energyLine(False, True), True))
			self.ml[i].append(team.dt.moneyLine(team.dt.energyLine(False, True), False))

			if self.pel.get(i)==None:
				self.pel[i] = []
			self.pel[i].append(team.dt.energyLineBalanced(True, True))
			self.pel[i].append(team.dt.energyLineBalanced(False, True))

			if self.pml.get(i)==None:
				self.pml[i] = []
			self.pml[i].append(team.dt.moneyLine(team.dt.energyLineBalanced(False, True), True))
			self.pml[i].append(team.dt.moneyLine(team.dt.energyLineBalanced(False, True), False))

			if self.profit.get(i)==None:
				self.profit[i] = []
			self.profit[i].append(list(map(lambda x: -x, team.dt.blackLineWithLoses(False))))
			self.profit[i].append(sum(team.dt.sumLists(team.getByName(self.buildingName).getCosts())))
			
			if self.mode == "drop":
				break
			
	def addTeam(self, teamID, criterions):
		frame = ttk.Frame(self.teamsFrame, borderwidth=1, relief="solid", padding=[8, 10], style="My.TLabel")
		frame.pack(side="left", anchor="nw")

		if self.mode=="prediction":
			lbl = Label(frame, ws.getStyle("labelTitle", text=f"Команда №{teamID}"))
			lbl.pack(side='top', anchor="nw")

		for name in criterions.keys():
			if criterions[name].get("color") == None:
				criterions[name]["color"] = "white"
			lbl = Label(frame, ws.getStyle("labelTitle", text=f"{name}:", fg=criterions[name]["color"]))
			lbl.pack(side='top', anchor="nw")
			for criterion in criterions[name].keys():
				if criterion=="color":
					continue
				elif criterion[0:4] == "Line":
					lbl = Label(frame, ws.getStyle("labelTitle", text="--------------", fg=criterions[name]["color"]))
					lbl.pack(side='top', anchor="nw")
					continue
				criterionValue = criterions[name][criterion]
				prefix = None
				extraColor = "white"
				if criterionValue>0:
					prefix = "+"
					extraColor = "lightgreen"
				elif criterionValue<0:
					prefix = "-"
					extraColor = "red"
				else:
					prefix = "0"
					extraColor = "yellow"
				criterionFrame = ttk.Frame(frame, borderwidth=1, relief="flat", padding=[0, 0], style="My.TLabel")
				criterionFrame.pack(side='top', anchor="nw")
				lbl = Label(criterionFrame, ws.getStyle("labelTitle", text=f"({prefix}) {criterion}: ", fg=criterions[name]["color"]))
				lbl.pack(side='left', anchor="nw")
				lbl = Label(criterionFrame, ws.getStyle("labelTitle", text=f"{criterionValue}", fg=extraColor))
				lbl.pack(side='left', anchor="nw")

	def prepare(self, prediction=False, drop=False, price=None):
		for team in teams:
			for build in team.getAll():
				build.clearData()
				
		for block in mm.InfrastBlocks.values():
			if block == self.infrastBlock and prediction:
				block.updateData(True, False, price=price)
			elif block == self.infrastBlock and drop:
				block.updateData(False, True, self.block[0])
			else:
				block.updateData()

		for team in teams:
			team.dt.update(autoB = float(mm.autoBuy.get()),
						   autoS = float(mm.autoSell.get()),
						   capacity = float(mm.capacity.get()),
						   maxCharge = float(mm.maxCharge.get()),
						   maxDischarge = float(mm.maxDischarge.get()),
						   loseK = float(mm.loseK.get()))


# building block
class InfrastBlock():
	def __init__(self, window, buildingName, description, side, onlyPrice=False):
		self.window = window
		self.buildingName = buildingName
		self.side = side
		self.count = 0
		self.blocks = {}
		self.prediction = []
		self.framesEntries = {}
		self.onlyPrice = onlyPrice
		self.comboboxes = {}
		self.useTag = False

		if buildingName=="Ветер":
			self.useTag = True

		frame = ttk.Frame(window, borderwidth=1, relief="solid", padding=[8, 10], style="My.TLabel")
		lbl = Label(frame, ws.getStyle("labelTitle", text=description, width=23))
		lbl.pack(side='top', anchor="n")

		superBlock = ttk.Frame(frame, borderwidth=0, relief=SOLID, padding=[1, 1], style="My.TLabel")
		superBlock.pack(side="top")
		lblCount = Label(superBlock, ws.getStyle("labelTitle", text=f"Предсказание", width=23))
		lblCount.pack(side='top')
		
		block = ttk.Frame(superBlock, borderwidth=0, relief=SOLID, padding=[1, 1], style="My.TLabel")
		block.pack(side="top", anchor="n")
		
		self.prediction.append(self.addOption(block, -1, "Цена", 5, True))
		self.prediction.append(self.addOption(block, -1, "Коэффицент", 1, True))
		self.prediction.append(self.addOption(block, -1, "Порог", 0, True))
		if self.useTag:
			combobox = ttk.Combobox(block, values=TAGS.get(self.buildingName))
			combobox.pack(side="left", anchor="nw")
			self.prediction.append(combobox)

		btn = Button(superBlock, ws.getStyle("buttonMain", text="Проверить", command=self.makePrediction, width=23))
		btn.pack(side="top")

		self.superBlock = ttk.Frame(frame, borderwidth=0, relief=SOLID, padding=[1, 1], style="My.TLabel")
		lblCount = Label(self.superBlock, ws.getStyle("labelTitle", text=f"Количество: {self.count}", width=23))
		lblCount.pack(side='top')
		self.lblCount = lblCount
		self.superBlock.pack(side="top", anchor="n", pady=5, ipadx=2)

		btn = Button(frame, ws.getStyle("buttonMain", text="+", command=self.createBlock, width=30))
		btn.pack(side='top', padx=1, pady=5)

		frame.pack(side=side)
		self.plusBtn = btn
		self.frame = frame
	
	def updateTags(self):
		if self.useTag:
			self.prediction[3].configure(values = TAGS.get(self.buildingName) )

	def addOption(self, parent, blockID, name, default, prediction=False):
		if prediction:
			frame = ttk.Frame(parent, borderwidth=0, relief="flat", style="My.TLabel")
			lbl = Label(frame, ws.getStyle("labelText", text=f"{name}:"))
			entry = Entry(frame, ws.getStyle("entryMain", width=7))
		else:
			frame = Frame(parent, borderwidth=0, relief="flat", bg="lightgray")
			lbl = Label(frame, ws.getStyle("labelMyTeam", text=f"{name}:", bg="lightgray"))
			entry = Entry(frame, ws.getStyle("entryMyTeam", width=7, bg="lightgray"))
		lbl.pack(side="top")
		entry.insert(0, str(default))
		entry.pack(side="top")
		frame.pack(side="left", anchor="nw")

		if not prediction:
			self.framesEntries[blockID].append( [frame, lbl, entry] )

		return entry

	def createBlock(self):
		self.plusBtn.pack_forget()
		self.count += 1
		self.lblCount["text"] = f"Количество: {self.count}"
		block = ttk.Frame(self.superBlock, borderwidth=0, relief="flat", padding=[0, 0], style="My.TLabel")
		block.pack(side="top", anchor="n")
		if len(self.blocks.keys())>0:
				blockID = max(self.blocks.keys())+1
		else:
			blockID = 0
		self.blocks[blockID] = block
		self.framesEntries[blockID] = list()
		
		entryList = []
		entryList.append(self.addOption(block, blockID, "Цена", 5))
		if not self.onlyPrice:
			entryList.append(self.addOption(block, blockID, "Коэффицент", 1))
			entryList.append(self.addOption(block, blockID, "Порог", 0))
		entryList.append(self.addOption(block, blockID, "Команда", 0))
		
		btnMinus = Button(block, ws.getStyle("buttonMain", text="-", command=lambda: self.destroyBlock(blockID)))
		btnMinus.pack(side="left", anchor="nw")
		btnHelp = Button(block, ws.getStyle("buttonMain", text="?", command=lambda: self.makeDrop(blockID)))
		btnHelp.pack(side="left", anchor="nw")
		if self.useTag:
			combobox = ttk.Combobox(block, values=TAGS[self.buildingName])
			combobox.pack(side="left", anchor="nw")
			self.comboboxes[blockID] = combobox

		self.plusBtn.pack(side=self.side)
		
		return entryList

	def destroyBlock(self, blockID):
		block = self.blocks[blockID]
		block.destroy()
		self.count -= 1
		self.lblCount["text"] = f"Количество: {self.count}"
		self.blocks.pop(blockID)
		self.framesEntries.pop(blockID)
		if self.useTag:
			self.comboboxes.pop(blockID)

	def makePrediction(self):
		InformWindow("prediction", self.window._root(), self, self.buildingName)

	def makeDrop(self, blockID):
		InformWindow("drop", self.window._root(), self, self.buildingName, [blockID, self.framesEntries[blockID]])

	def updateData(self, prediction=False, drop=True, index=None, price=None):
		resultData = dict()
		for key in self.framesEntries.keys():
			data = []
			
			if drop and key==index:
				continue
			
			for widgets in self.framesEntries[key]:
				entry = widgets[2]
				if not entry.get().isdigit():
					if entry.get().count(".") == 1:
						entrySpl = entry.get().split(".")
						if entrySpl[0].isdigit() and entrySpl[1].isdigit():
							data.append(float(entry.get()))
							entry["fg"] = "black"
						else:
							entry["fg"] = "red"
							return
					else:
						entry["fg"] = "red"
						return
				else:
					data.append(float(entry.get()))
					entry["fg"] = "black"

			if len(data)==2:
				data[1] = int(data[1])
				if resultData.get(data[1])==None:
					resultData[data[1]] = []
				resultData[data[1]].append(data)

			else:
				data[3] = int(data[3])
				if self.useTag:
					data.append(self.comboboxes[key].get())
				if resultData.get(data[3])==None:
					resultData[data[3]] = []
				resultData[data[3]].append(data)

		if prediction:
			for i in range(len(teams)):
				if resultData.get(i)==None:
					resultData[i] = []
				resultData[i].append(list(map(lambda x: float(x.get()) if x.get().isdigit() else x.get(), self.prediction)))
				resultData[i][-1] = resultData[i][-1][:3]+[i]+resultData[i][-1][3:]
				if price!=None:
					resultData[i][-1][0] = price
		
		for key in resultData.keys():
			if key<len(teams) and key>=0:
				buildings = teams[key]
				buildings.getByName(self.buildingName).setData(resultData[key])
		  
		for l in self.framesEntries.values():
			color = None
			if self.onlyPrice:
				if TEAMCOLOR.get(int(l[1][2].get())) == None:
					color = randColor()
					while color in list(TEAMCOLOR.values()):
						color = randColor()
					TEAMCOLOR[int(l[1][2].get())] = color
				else:
					color = TEAMCOLOR.get(int(l[1][2].get()))
			else:
				if TEAMCOLOR.get(int(l[3][2].get())) == None:
					color = randColor()
					while color in list(TEAMCOLOR.values()):
						color = randColor()
					TEAMCOLOR[int(l[3][2].get())] = color
				else:
					color = TEAMCOLOR.get(int(l[3][2].get()))

			for widgets in l: 
				for widget in widgets:
					widget.configure(bg=color)
					
		return resultData

def exportOpt():
	with open("export.json", "w", encoding="utf-8") as f:
		result = dict()
		for key in mm.InfrastBlocks.keys():
			data = None
			try:
				data = list(map(lambda x: [float(x[0][2].get()), float(x[1][2].get()), float(x[2][2].get()), int(x[3][2].get())], list(mm.InfrastBlocks[key].framesEntries.values())))
			except IndexError:
				continue
			result[key] = data
		result["path"] = mm.entryPath.get()

		result["autoBuy"] = mm.autoBuy.get()
		result["autoSell"] = mm.autoSell.get()
		result["capacity"] = mm.capacity.get()
		result["maxCharge"] = mm.maxCharge.get()
		result["maxDischarge"] = mm.maxDischarge.get()
		result["loseK"] = mm.loseK.get()
		#print(result)
		js = json.dumps(result)
		f.write(js)

def importOpt(path):
	with open(path, "r", encoding="utf-8") as f:
		data = json.loads(f.read())
		for key in data.keys():
			if key=="path":
				mm.entryPath.delete(0, "end")
				mm.entryPath.insert(0, data[key])
				mm.convertCSV()
			elif key == "autoBuy":
				mm.autoBuy.delete(0, "end")
				mm.autoBuy.insert(0, data[key])
			elif key == "autoSell":
				mm.autoSell.delete(0, "end")
				mm.autoSell.insert(0, data[key])
			elif key == "capacity":
				mm.capacity.delete(0, "end")
				mm.capacity.insert(0, data[key])
			elif key == "maxCharge":
				mm.maxCharge.delete(0, "end")
				mm.maxCharge.insert(0, data[key])
			elif key == "maxDischarge":
				mm.maxDischarge.delete(0, "end")
				mm.maxDischarge.insert(0, data[key])
			elif key == "loseK":
				mm.loseK.delete(0, "end")
				mm.loseK.insert(0, data[key])
			else:
				for values in data[key]:
					l = mm.InfrastBlocks[key].createBlock()
					for e in l:
						e.delete(0, "end")
						
					l[0].insert(0, str(values[0]))
					l[1].insert(0, str(values[1]))
					l[2].insert(0, str(values[2]))
					l[3].insert(0, str(values[3]))

if __name__ == "__main__":
	mm = MainMenu()
	mm.activate()
