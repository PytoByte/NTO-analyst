import tkinter as tk
from tkinter import *
from tkinter import filedialog as fd
from tkinter import ttk
from tkinter import messagebox

from MyImport import *
from DataTransformer import DataTransformer
from Buildings import *
from Graph import Graph

# Предсказание для всех команд при покупке некого объекта
class PredictWindow(Toplevel):
    def __init__(self, window, sf, **windowParams):
        super().__init__(window, **windowParams)

        self.geometry("350x640")

        self.sf = sf
        self.window = window

        self.title("Изменения при покупке "+self.sf.title)

        ttk.Label(self, text="Изменения при покупке "+self.sf.title, anchor="s").grid(row=0, column=0, sticky="we", columnspan=2)
        
        self.scroll_y = Scrollbar(self, orient="vertical")
        self.scroll_x = Scrollbar(self, orient="horizontal")
        self.canvas = Canvas(self, yscrollcommand=self.scroll_y.set, background = '#333333', xscrollcommand=self.scroll_x.set)
        self.scroll_y.config(command=self.canvas.yview)
        self.scroll_x.config(command=self.canvas.xview)

        self.mainFrame = ttk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.mainFrame, anchor="center")

        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)
        
        self.canvas.grid(row=1, column=0, sticky="nswe")
        self.scroll_y.grid(row=1, column=1, sticky="ns")
        self.scroll_x.grid(row=2, column=0, sticky="we", columnspan=2)

        self.bind("<Configure>", self.resize)
        self.bind("<MouseWheel>", self.on_mousewheel)
        self.bind('<Left>', self.on_left)
        self.bind('<Right>', self.on_right)
        self.update_idletasks()

        ttk.Button(self, text="Понятно", command=self.destroy).grid(row=3, column=0, sticky="we", columnspan=2, padx=10, pady=10)
        
        reports = self.predict(self.window, sf.predictBuilding)
        for team, report in reports.items():
            showTitle = self.window.options["Заголовки графиков изменения"]
            
            reportFrame = ttk.Frame(self.mainFrame)
            reportFrame.pack(anchor="nw", side="left")
            ttk.Label(reportFrame, text="Команда №"+str(team)).pack(anchor="n")
            #ttk.Label(reportFrame, text=f"Профит: {report['profit']}").pack(anchor="n")
            ttk.Label(reportFrame, text="Дизбаланс энергии").pack(anchor="n")
            ttk.Label(reportFrame, text=f"Изменение: {report['energySumBefore']} => {report['energySumAfter']}").pack(anchor="n")
            energyGraph = Graph(reportFrame, height=150, width=300, bg="#1F1F1F", showTitle=showTitle)
            energyGraph.addGraph(**dict(list(report["energyGraph"]["before"]["Дизбаланс"].items())[0:2]), color="#AAAAAA", title="До")
            energyGraph.addGraph(**dict(list(report["energyGraph"]["after"]["Дизбаланс"].items())[0:2]), color="#FFFFFF", title="После")
            energyGraph.pack(anchor="n")
            energyGraph.draw()
            ttk.Label(reportFrame, text="Заработок с ценой минимального дохода").pack(anchor="n")
            moneyGraph = Graph(reportFrame, height=150, width=300, bg="#1F1F1F", showTitle=showTitle)
            moneyGraph.addGraph(**dict(list(report["moneyGraph"]["before"]["Доход"].items())[0:2]), color="#AAAAAA", title="До")
            moneyGraph.addGraph(**dict(list(report["moneyGraph"]["after"]["Доход"].items())[0:2]), color="#FFFFFF", title="После")
            moneyGraph.pack(anchor="n")
            moneyGraph.draw()
            ttk.Label(reportFrame, text="Доход от цены").pack(anchor="n")
            ttk.Label(reportFrame, text="Минимальная доходность при: "+str(report["minIncomePrice"])).pack(anchor="n")
            incomeGraph = Graph(reportFrame, height=150, width=300, bg="#1F1F1F", showTitle=showTitle)
            incomeGraph.addGraph(**report["incomeGraph"], color="#FFFFFF")
            incomeGraph.pack(anchor="n")
            incomeGraph.draw()

    def resize(self, event):
        region = self.canvas.bbox("all")
        self.canvas.configure(scrollregion=region)

    def on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def on_left(self, event):
        self.canvas.xview_scroll(-1, "units")

    def on_right(self, event):
        self.canvas.xview_scroll(1, "units")

    @staticmethod
    def predict(window, predictBuilding, teams=None):
        reports = {}
        
        dt = DataTransformer(window)
        for sf in window.shopFragments:
            for building in sf.buildings.values():
                dt.append(building["object"])
        if not isinstance(predictBuilding, Extra):
            dt.append(predictBuilding)
        dt.setupForecast()

        if teams==None:
            teams = range(len(window.teams))

        for team in teams:
            predictBuilding.team.set(team)
            dt.update()

            k = None
            if not isinstance(predictBuilding, Extra):
                k = predictBuilding.k.get()
                predictBuilding.k.set(0)
            predictBuilding.price.set(0)
            predictBuilding.update()
            if not isinstance(predictBuilding, Extra):
                predictBuilding.overEnergy = 0
            sumBefore = dt.getMoneyGraph(team)["Доход"]["valY"][-1]
            
            reports[team] = {
                "moneyGraph":{"before":dt.getMoneyGraph(team), "after":None},
                "energyGraph":{"before":dt.getEnergyGraph(team), "after":None},
                "minIncomePrice":None,
                "incomeGraph":None
                #"profit":None
            }
            if not isinstance(predictBuilding, Extra):
                predictBuilding.k.set(k)
            else:
                dt.append(predictBuilding)

            positive = None
            negative = None
            valY = []
            valX = []
            for x in range(0, 111):
                #print(x)
                predictBuilding.price.set(x)
                predictBuilding.update()
                income = dt.getMoneyGraph(team)["Доход"]["valY"][-1]-sumBefore
                valY.append(income)
                valX.append(x)
                if round(income,3)>0:
                    positive = x
                elif round(income,3)<0:
                    negative = x
                else:
                    reports[team]["minIncomePrice"] = x
                    predictBuilding.price.set(round(x,1))
                    break

                if positive!=None and negative!=None:
                    mid = 0
                    for _ in range(100):
                        mid = (positive+negative)/2
                        predictBuilding.price.set(mid)
                        predictBuilding.update()
                        income = dt.getMoneyGraph(team)["Доход"]["valY"][-1]-sumBefore
                        valY.append(income)
                        valX.append(mid)
                        #print(positive, negative, mid, income, dt.getMoneyGraph(team)["Доход"]["valY"][-1], sumBefore)
                        if round(income,3)>0:
                            positive = mid
                        elif round(income,3)<0:
                            negative = mid
                        else:
                            break
                    predictBuilding.price.set(round(mid,1))
                    reports[team]["minIncomePrice"] = round(mid,1)
                    break
            reports[team]["moneyGraph"]["after"] = dt.getMoneyGraph(team)
            reports[team]["energyGraph"]["after"] = dt.getEnergyGraph(team)
            reports[team]["energySumBefore"] = round(sum(reports[team]["energyGraph"]["before"]["Дизбаланс"]["valY"]), 1)
            reports[team]["energySumAfter"] = round(sum(reports[team]["energyGraph"]["after"]["Дизбаланс"]["valY"]), 1)
            """
            profit = None
            if isinstance(predictBuilding, Infrastructure):
                if reports[team]['minIncomePrice']!=0 and reports[team]["energySumAfter"]!=0:
                    profit = round(100/(reports[team]['minIncomePrice']*abs(reports[team]["energySumAfter"])), 1) if reports[team]['minIncomePrice']!=None else None
                else:
                    profit = "∞"
            elif isinstance(predictBuilding, Generator):
                profit = round(100*reports[team]['minIncomePrice']/abs(reports[team]["energySumAfter"]), 1) if reports[team]['minIncomePrice']!=None else None

            reports[team]["profit"] = profit
            """
            reports[team]["incomeGraph"] = {"valY":valY, "valX":valX, "title":"Поиск цены"}
        return reports

# Предсказание для одной команды при сбросе некого объекта
class DropPredictWindow(Toplevel):
    def __init__(self, window, sf, buildingID, **windowParams):
        super().__init__(window, **windowParams)

        self.geometry("350x640")

        self.sf = sf
        self.window = window

        self.title("Изменения при бросе "+self.sf.title)

        ttk.Label(self, text="Изменения при бросе "+self.sf.title, anchor="s").grid(row=0, column=0, sticky="we", columnspan=2)
        
        self.scroll_y = Scrollbar(self, orient="vertical")
        self.canvas = Canvas(self, yscrollcommand=self.scroll_y.set, background = '#333333')
        self.scroll_y.config(command=self.canvas.yview)

        self.mainFrame = ttk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.mainFrame, anchor="center")

        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)
        
        self.canvas.grid(row=1, column=0, sticky="nswe")
        self.scroll_y.grid(row=1, column=1, sticky="ns")

        self.bind("<Configure>", self.resize)
        self.canvas.bind("<MouseWheel>", self.on_mousewheel)
        self.update_idletasks()

        ttk.Button(self, text="Понятно", command=self.destroy).grid(row=3, column=0, sticky="we", columnspan=2, padx=10, pady=10)
        
        report = self.simplePredict(self.window, sf, buildingID)
        showTitle = self.window.options["Заголовки графиков изменения"]
            
        reportFrame = ttk.Frame(self.mainFrame)
        reportFrame.pack(anchor="nw", side="left")
        ttk.Label(reportFrame, text="Команда №"+str(sf.buildings[buildingID]["object"].team.get())).pack(anchor="n")
        ttk.Label(reportFrame, text="Дизбаланс энергии").pack(anchor="n")
        ttk.Label(reportFrame, text=f"Изменение: {report['energySumBefore']} => {report['energySumAfter']}").pack(anchor="n")
        energyGraph = Graph(reportFrame, height=150, width=300, bg="#1F1F1F", showTitle=showTitle)
        energyGraph.addGraph(**dict(list(report["energyGraph"]["before"]["Дизбаланс"].items())[0:2]), color="#AAAAAA", title="До")
        energyGraph.addGraph(**dict(list(report["energyGraph"]["after"]["Дизбаланс"].items())[0:2]), color="#FFFFFF", title="После")
        energyGraph.pack(anchor="n")
        energyGraph.draw()
        ttk.Label(reportFrame, text="Доход").pack(anchor="n")
        ttk.Label(reportFrame, text=f"Изменение: {report['moneyBefore']} => {report['moneyAfter']}").pack(anchor="n")
        moneyGraph = Graph(reportFrame, height=150, width=300, bg="#1F1F1F", showTitle=showTitle)
        moneyGraph.addGraph(**dict(list(report["moneyGraph"]["before"]["Доход"].items())[0:2]), color="#AAAAAA", title="До")
        moneyGraph.addGraph(**dict(list(report["moneyGraph"]["after"]["Доход"].items())[0:2]), color="#FFFFFF", title="После")
        moneyGraph.pack(anchor="n")
        moneyGraph.draw()

    def resize(self, event):
        region = self.canvas.bbox("all")
        self.canvas.configure(scrollregion=region)

    def on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    @staticmethod
    def simplePredict(window, sfPredict, buildingID):
        report = {}
        
        dt = DataTransformer(window)
        hiddenBuilding = None
        for sf in window.shopFragments:
            for key, building in sf.buildings.items():
                if sf==sfPredict and key==buildingID:
                    hiddenBuilding = building["object"]
                else:
                    dt.append(building["object"])
        dt.setupForecast()

        team = hiddenBuilding.team.get()
            
        report = {
            "moneyGraph":{"after":dt.getMoneyGraph(team), "before":None},
            "energyGraph":{"after":dt.getEnergyGraph(team), "before":None},
            "minIncomePrice":None,
            "incomeGraph":None
        }

        dt.append(hiddenBuilding)
        report["moneyGraph"]["before"] = dt.getMoneyGraph(team)
        report["energyGraph"]["before"] = dt.getEnergyGraph(team)
        report["energySumBefore"] = round(sum(report["energyGraph"]["before"]["Дизбаланс"]["valY"]), 1)
        report["energySumAfter"] = round(sum(report["energyGraph"]["after"]["Дизбаланс"]["valY"]), 1)
        if len(report["moneyGraph"]["before"]["Доход"]["valY"])==0:
            report["moneyBefore"] = 0
        else:
            report["moneyBefore"] = round(report["moneyGraph"]["before"]["Доход"]["valY"][-1], 1)
        if len(report["moneyGraph"]["after"]["Доход"]["valY"])==0:
            report["moneyAfter"] = 0
        else:
            report["moneyAfter"] = round(report["moneyGraph"]["after"]["Доход"]["valY"][-1], 1)
        
        return report
