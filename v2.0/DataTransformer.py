from MyImport import *

# Класс который считает всё
class DataTransformer():
    def __init__(self, window):
        self.window = window
        self.buildings = []
        self.teams = []
        self.teamsProperty = {}
        self.graphParams = {
            "Ветер":{"name":"Ветер", "color":"#00FFFF"},
            "Ветер:А":{"name":"Ветер", "color":"#00FFFF"},
            "Ветер:Б":{"name":"Ветер", "color":"#00FFFF"},
            "Ветер:В":{"name":"Ветер", "color":"#00FFFF"},
            "Ветер:Г":{"name":"Ветер", "color":"#00FFFF"},
            "Ветер:Д":{"name":"Ветер", "color":"#00FFFF"},
            "Ветер:E":{"name":"Ветер", "color":"#00FFFF"},
            "Ветер:Ж":{"name":"Ветер", "color":"#00FFFF"},
            "Солнце":{"name":"Солнце", "color":"#FFFF00"},
            "Дома":{"name":"Дома А", "color":"#00FF00"},
            "Дома А":{"name":"Дома А", "color":"#00FF00"},
            "Дома Б":{"name":"Дома Б", "color":"#007A00"},
            "Заводы":{"name":"Заводы", "color":"#7A00FF"},
            "Больницы":{"name":"Больницы", "color":"#FF0000"}}

    def clear(self):
        self.buildings = []
        self.teams = []
        self.teamsProperty = {}

    @staticmethod
    def sumLists(a,b):
        if a==None:
            a = []
        if b==None:
            b = []

        i = min(len(a), len(b))
        return list(map(lambda x,y: x+y, a[:i], b[:i]))+a[i:]+b[i:]

    def append(self, buildingObject):
        self.buildings.append(buildingObject)
        team = buildingObject.team.get()
        if self.teamsProperty.get(team)==None:
            self.teamsProperty[team] = []
            self.teams.append(team)
        self.teamsProperty[team].append(buildingObject)

    def update(self):
        self.teams = []
        self.teamsProperty = {}
        for buildingObject in self.buildings:
            team = buildingObject.team.get()
            if self.teamsProperty.get(team)==None:
                self.teamsProperty[team] = []
                self.teams.append(team)
            self.teamsProperty[team].append(buildingObject)

    def setupForecast(self):
        for team in self.teams:
            for building in self.teamsProperty[team]:
                if not isinstance(building, Extra):
                    forecastName = building.forecastName.get()
                    building.setForecast(self.window.forecast[forecastName])

    # Прогноз погоды, ничего необычного
    def getForecastGraph(self, team):
        graphs = {}
        if self.teamsProperty.get(team)==None:
            return graphs
        
        for building in self.teamsProperty[team]:
            if isinstance(building, Extra):
                continue
            graphParam = self.graphParams.get(building.forecastName.get())
            energy = list(map(lambda x: x+building.overEnergy, building.energy))
            if graphParam!=None:
                if graphs.get(graphParam["name"])==None:
                    graphs[graphParam["name"]] = {"valY":energy, "valX":None, "title":graphParam["name"], "color":graphParam["color"]}
                else:
                    graphs[graphParam["name"]]["valY"] = self.sumLists(graphs[graphParam["name"]]["valY"], energy)
            else:
                if graphs.get(forecastName)==None:
                    graphs[forecastName] = {"valY":energy, "valX":None, "title":forecastName}
                else:
                    graphs[forecastName]["valY"] = self.sumLists(graphs[forecastName]["valY"], energy)

        return graphs

    # График генерации и потребления
    def getEnergyGraph(self, team, moneyInfo=False):
        graphs = {}
        defaultValues = [0]*len(list(self.window.forecast.values())[0])

        graphs["Потребление"] = {"valY":defaultValues, "valX":None, "title":"Потребление", "color":"#00FFAA"}
        graphs["Производство"] = {"valY":defaultValues, "valX":None, "title":"Производство", "color":"#00FFFF"}
        graphs["Дизбаланс"] = {"valY":defaultValues, "valX":None, "title":"Дизбаланс", "color":"#000000"}
        graphs["Потери"] = {"valY":defaultValues, "valX":None, "title":"Потери", "color":"#FF0000"}
        extras = []

        if self.teamsProperty.get(team)==None:
            return graphs
        
        lossK = self.window.options["Процент потерь"].get()
        for building in self.teamsProperty[team]:
            energy = list(map(lambda x: x+building.overEnergy, building.energy)) if not isinstance(building, Extra) else None
            if isinstance(building, Infrastructure):
                if graphs["Потребление"]["valY"]==[]:
                    graphs["Потребление"]["valY"] = energy
                else:
                    graphs["Потребление"]["valY"] = self.sumLists(graphs["Потребление"]["valY"], energy)
            elif isinstance(building, Generator):
                losses = list(map(lambda x: x*lossK, energy))
                energy = list(map(lambda x: x*(1-lossK), energy))
                if graphs["Производство"]["valY"]==[]:
                    graphs["Производство"]["valY"] = energy
                    graphs["Потери"]["valY"] = losses
                else:
                    graphs["Производство"]["valY"] = self.sumLists(graphs["Производство"]["valY"], energy)
                    graphs["Потери"]["valY"] = self.sumLists(graphs["Потери"]["valY"], losses)
            elif isinstance(building, Extra):
                extras.append(building)
            
        disbalance = self.sumLists(graphs["Производство"]["valY"], graphs["Потребление"]["valY"])

        smoney = 0
        for extra in extras:
            info = extra.changeEnergy(disbalance)
            disbalance = info["energy"]
            smoney += info["money"]
        graphs["Дизбаланс"]["valY"] = disbalance
        graphs["Потребление"]["valY"] = list(map(lambda x: -x, graphs["Потребление"]["valY"]))

        if moneyInfo:
            return graphs, smoney
        else:
            return graphs
        
    def getMoneyGraph(self, team):
        graphs = {}
        graphs["Доход"] = {"valY":[], "valX":None, "title":"Доход", "color":"#FFFF00"}
        graphs["ЭкстаДоход"] = {"valY":[], "valX":None, "title":"ЭкстаДоход", "color":"#FFD700"}
        
        autoBuyPrice = self.window.options["Цена автопокупки"].get()
        autoSellPrice = self.window.options["Цена автопродажи"].get()
        
        buildingsCount = {}
        averIncome = {}
        buildingsConsume = {}
        rentGenerators = 0
        overConsume = {}
        if self.teamsProperty.get(team)==None:
            graphs["Доход"]["valY"] = [0]
            return graphs
        
        for building in self.teamsProperty[team]:
            if isinstance(building, Infrastructure):
                price = float(building.price.get())
                priority = building.priority
                if averIncome.get(priority)==None:
                    averIncome[priority]=price
                    buildingsCount[priority]=1
                    buildingsConsume[priority]=building.energy
                    overConsume[priority] = building.overEnergy
                else:
                    buildingsConsume[priority]=self.sumLists(building.energy, buildingsConsume[priority])
                    averIncome[priority]+=price
                    buildingsCount[priority]+=1
                    overConsume[priority] += building.overEnergy
            elif isinstance(building, Generator):
                rentGenerators += float(building.price.get())
            elif isinstance(building, Extra):
                rentGenerators += float(building.price.get())

        priorities = sorted(buildingsCount.keys())
                    
        for key, count in buildingsCount.items():
            averIncome[key] = averIncome[key]/count

        energyGraph, extraMoney = self.getEnergyGraph(team, moneyInfo=True)
        
        for step, availableEnergy in enumerate(energyGraph["Производство"]["valY"]):
            money = 0
            money -= rentGenerators
            
            if energyGraph["Дизбаланс"]["valY"][step]>=0:
                money += self.window.options["Цена автопродажи"].get()*energyGraph["Дизбаланс"]["valY"][step]
            else:
                money += self.window.options["Цена автопокупки"].get()*energyGraph["Дизбаланс"]["valY"][step]
                
            for priority in priorities:
                if availableEnergy<abs(buildingsConsume[priority][step]):
                    money += averIncome[priority]*availableEnergy
                    consumeRemain = abs(buildingsConsume[priority][step])-availableEnergy
                else:
                    availableEnergy+=buildingsConsume[priority][step]
                    money += averIncome[priority]*abs(buildingsConsume[priority][step])

                
            if step==0:
                graphs["Доход"]["valY"].append(money)
            else:
                graphs["Доход"]["valY"].append(graphs["Доход"]["valY"][step-1]+money)

        if len(graphs["Доход"]["valY"])==0:
            graphs["Доход"]["valY"] = [0]

        graphs["Доход"]["valY"][-1] += extraMoney

        graphs["Доход"]["title"]+=": "+str(round(graphs["Доход"]["valY"][-1]))
        graphs["ЭкстаДоход"]["title"]+=f": {round(extraMoney)}"
        return graphs
