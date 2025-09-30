import numpy as np

# Объекты строений, которые используют погоду
# Особенности:
# Результат через getEnegry
# Возвращает только свой график энергии
class Building():
    def __init__(self):
        self.forecast = None
        self.energy = None
        self.overEnergy = None # Это энергия которая не идёт в доход
        self.team = None
        self.k = None
        self.b = None
        self.price = None
        self.forecastNames = None
        self.forecastName = None
        self.priority = None

    def setParams(self, team, price, k, b):
        self.team = team
        self.price = price
        self.k = k
        self.b = b

    def setForecast(self, forecast):
        self.forecast = forecast
        self.energy = self.getEnegry()
        self.overEnergy = self.getOverEnergy()

    def update(self):
        self.energy = self.getEnegry()
        self.overEnergy = self.getOverEnergy()

    def setForecastName(self, forecastName):
        self.forecastName = forecastName

    def getEnegry(self):
        energy = []
        for v in self.forecast:
            energy.append(v*float(self.k.get()) if v>=float(self.b.get()) else 0)
        return self.smooth(energy)

    def getOverEnergy(self):
        return 0
        
    def smooth(self, y_data, win=3):
        filt = np.ones(win)/win
        return list(np.convolve(y_data, filt, mode='same'))
    
# Графики потребления
class Infrastructure(Building):
    def __init__(self):
        super().__init__()

    def getEnegry(self):
        energy = []
        for v in self.forecast:
            energy.append(-v*float(self.k.get()) if v>=float(self.b.get()) else 0)
        return self.smooth(energy)

# Графики генерации
class Generator(Building):
    def __init__(self):
        super().__init__()

    def getEnergy(self):
        energy = []
        for v in self.forecast:
            energy.append(v*float(self.k.get()) if v>=float(self.b.get()) else 0)
        return self.smooth(energy)

# Объекты строений, которые изменяют график энергии
# Особенности:
# Результат через changeEnergy
# Возвращает словарь: {"energy":новый дизбаланс энергии, "money":доход(может быть отрицательный)}
class Extra():
    def __init__(self):
        self.team = None
        self.price = None
        self.energyPrice = None
        self.limit = None
        self.maxCharge = None
        self.minCharge = None
        self.autobuyPrice = None
        self.autosellPrice = None

    def setParams(self, team, price, params):
        self.team = team
        self.price = price
        self.energyPrice = params["Цена доп производства"]
        self.limit = params["Ёмкость аккумулятора"]
        self.maxCharge = params["Макс заряд аккумулятора"]
        self.minCharge = params["Мин заряд аккумулятора"]
        self.autobuyPrice = params["Цена автопокупки"]
        self.autosellPrice = params["Цена автопродажи"]

    def changeEnergy(self, disbalanceEnergy):
        return {"energy":disbalanceEnergy, "money":0}

    def update(self):
        pass


class SubStantion(Extra):
    def __init__(self):
        super().__init__()

    def changeEnergy(self, disbalanceEnergy):
        return {"energy":disbalanceEnergy, "money":0}


class Accumulator(Extra):
    def __init__(self):
        super().__init__()

    def changeEnergy(self, disbalanceEnergy):
        battery = 0
        newEnergy = []
        for v in disbalanceEnergy:
            if v>0:
                if v>self.maxCharge.get():
                    if battery+self.maxCharge.get()>self.limit.get():
                        delta = self.limit.get()-battery
                        v -= delta
                        battery += delta
                    else:
                        battery+=self.maxCharge.get()
                        v -= self.maxCharge.get()
                else:
                    if battery+v>self.limit.get():
                        delta = self.limit.get()-battery
                        v -= delta
                        battery += delta
                    else:
                        battery+=v
                        v = 0
            else:
                if v<-self.minCharge.get():
                    if battery-self.minCharge.get()<0:
                        delta = battery
                        v += delta
                        battery -= delta
                    else:
                        battery -= self.minCharge.get()
                        v += self.minCharge.get()
                else:
                    if battery+v<0:
                        delta = battery
                        v += delta
                        battery -= delta
                    else:
                        battery += v
                        v = 0
            newEnergy.append(v)
        return {"energy":newEnergy, "money":battery*self.autosellPrice.get()}


class House(Infrastructure):
    def __init__(self):
        super().__init__()
        self.forecastNames = ("Дома",)
        self.priority = 2


class HouseA(Infrastructure):
    def __init__(self):
        super().__init__()
        self.forecastNames = ("Дома А",)
        self.priority = 2

    def getOverEnergy(self):
        return -0.82*(5-float(self.price.get()))**2.6 if float(self.price.get())<=5 else 0


class HouseB(Infrastructure):
    def __init__(self):
        super().__init__()
        self.forecastNames = ("Дома Б",)
        self.priority = 2

    def getOverEnergy(self):
        return -0.24*(9-float(self.price.get()))**2.2 if float(self.price.get())<=9 else 0


class Factory(Infrastructure):
    def __init__(self):
        super().__init__()
        self.forecastNames = ("Заводы",)
        self.priority = 1


class Hospital(Infrastructure):
    def __init__(self):
        super().__init__()
        self.forecastNames = ("Больницы",)
        self.priority = 0
    

class Wind(Generator):
    def __init__(self):
        super().__init__()
        self.forecastNames = ('Ветер','Ветер:А','Ветер:Б','Ветер:В','Ветер:Г','Ветер:Д','Ветер:Е','Ветер:Ж')
        self.priority = -1

class Sun(Generator):
    def __init__(self):
        super().__init__()
        self.forecastNames = ("Солнце",)
        self.priority = -1

# Названия строений
BUILDINGCLASSES = {
    #"Дома":House,
    "Дома A":HouseA,
    "Дома Б":HouseB,
    "Заводы":Factory,
    "Больницы":Hospital,
    "Ветер":Wind,
    "Солнце":Sun,
    "Подстанция":SubStantion,
    "Аккумулятор":Accumulator
}
