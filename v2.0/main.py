import math
import csv
import random
import json

from MyImport import *

# Класс основного окна
class Window(Tk, Options):
    @staticmethod
    def randColor():
        return "#{:02x}{:02x}{:02x}".format(random.randint(0,66), random.randint(0,66), random.randint(0,66))

    @staticmethod
    def changeStyle(styleObject, wdg, color, ID):
        ID = str(ID)
        try:
            styleName = f'team{type(wdg).__name__}{ID}.T{type(wdg).__name__}'
            styleObject.configure(styleName, background=color)
            wdg.configure(style=styleName)
        except:
            styleName = f'teamFrame{ID}.TFrame'
            styleObject.configure(styleName, background=color)
            wdg.configure(style=styleName)
        for wdgChild in wdg.winfo_children():
            Window.changeStyle(styleObject, wdgChild, color, ID)

    @staticmethod
    def changeReadyStyle(wdg, ID):
        ID = str(ID)
        try:
            styleName = f'team{type(wdg).__name__}{ID}.T{type(wdg).__name__}'
            wdg.configure(style=styleName)
        except:
            styleName = f'teamFrame{ID}.TFrame'
            wdg.configure(style=styleName)
        for wdgChild in wdg.winfo_children():
            Window.changeReadyStyle(wdgChild, ID)
    
    def __init__(self, **params):
        super().__init__(**params)
        #self.overrideredirect(True)
        self.geometry(f"1060x940")
        
        self.teams = {}
        self.options = {}
        self.forecast = None
        self.dt = DataTransformer(self)
        self.shopFragments = []
        self.privateParams = {"teamColors":{}}
        with open("OptionsList.json", "r") as file:
            for key, value in (json.load(file)).items():
                self.addParam(key, value)
        
        self.initMenu()
        try:
            with open("fast_params.json", "r") as file:
                self.importOptions(file)
        except:
            pass

        # Скроллы
        self.scroll_x = Scrollbar(self, orient="horizontal")
        self.scroll_y = Scrollbar(self, orient="vertical")
        self.canvas = Canvas(self, width=300, height=100,
                                xscrollcommand=self.scroll_x.set,
                                yscrollcommand=self.scroll_y.set, background = '#333333')
        self.scroll_x.config(command=self.canvas.xview)
        self.scroll_y.config(command=self.canvas.yview)

        # Рамка со скроллами
        self.mainFrame = ttk.Frame(self.canvas)

        self.canvas.create_window((0, 0), window=self.mainFrame, anchor="nw")
        self.canvas.grid(row=0, column=0, sticky="nswe")
        self.scroll_x.grid(row=1, column=0, sticky="we")
        self.scroll_y.grid(row=0, column=1, sticky="ns")
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        self.bind("<Return>", lambda e: self.drawGraphs())
        self.bind("<Configure>", self.resize)
        self.bind("<MouseWheel>", self.on_mousewheel)
        self.bind('<Left>', self.on_left)
        self.bind('<Right>', self.on_right)
        self.update_idletasks()
        
        self.title("НТО аналитик")
        
        inputFrame = ttk.Frame(self.mainFrame)

        inputFrame.grid(column=0, row=0, sticky="NS", ipady=2,ipadx=2)

        sfFrame = ttk.Frame(inputFrame, borderwidth=1, relief=SOLID)
        sfFrame.pack(anchor="n")

        for name, cls in BUILDINGCLASSES.items():
            self.shopFragments.append(ShopFragment(self, cls, sfFrame, name, borderwidth=1, relief=SOLID))
            
        c = 0
        r = 0
        for sf in self.shopFragments:
            sf.grid(column=c, row=r, sticky="nesw")
            c+=1
            if c==2:
                r+=1
                c = 0

        pathFrame = ttk.Frame(inputFrame)
        pathLabel = ttk.Label(pathFrame, text="Путь прогноза")
        self.path = StringVar()
        pathEntry = ttk.Entry(pathFrame, textvariable=self.path)
        pathButton = ttk.Button(pathFrame, text="Указать", command=self.chooseFilePath)

        pathFrame.pack(anchor="n")
        pathLabel.pack(anchor="n")
        pathEntry.pack(anchor="n")
        pathButton.pack(anchor="n")
        
        drawButton = ttk.Button(inputFrame, text="Построить графики", command=self.drawGraphs)
        drawButton.pack(anchor="n")
        
        self.graphsFrame = ttk.Frame(self.mainFrame, borderwidth=1, relief=SOLID)
        self.graphsFrame.grid(column=1, row=0, sticky="NS")
        ttk.Button(self.mainFrame, text="+", command=self.addTeam, width=2).grid(column=2, row=0, sticky="NS")
        self.addTeam()

    def resize(self, event):
        region = self.canvas.bbox("all")
        self.canvas.configure(scrollregion=region)

    def on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def on_left(self, event):
        self.canvas.xview_scroll(-1, "units")

    def on_right(self, event):
        self.canvas.xview_scroll(1, "units")

    def initMenu(self):
        self.option_add("*tearOff", False)
        
        main_menu = Menu()
 
        session_menu = Menu()
        session_menu.add_command(label="Сохранить", command=self.exportSession)
        session_menu.add_command(label="Загрузить", command=self.importSession)
        session_menu.add_separator()
        session_menu.add_command(label="Выход")

        params_menu = Menu()
        params_menu.add_command(label="Открыть", command=lambda: OptionsWindow(self, self.options, bg="#333333"))
        params_menu.add_separator()
        params_menu.add_command(label="Сохранить", command=self.exportOptions)
        params_menu.add_command(label="Загрузить", command=self.importOptions)
        
        main_menu.add_cascade(label="Сессия", menu=session_menu)
        main_menu.add_cascade(label="Параметры", menu=params_menu)
        main_menu.add_cascade(label="Инструменты")
         
        self.config(menu=main_menu)
        
    def exportSession(self):
        exportData = {}
        for sf in self.shopFragments:
            exportData[sf.title] = []
            for building in sf.buildings.values():
                building = building["object"]
                buildingClass = {}
                buildingClass["team"] = building.team.get()
                buildingClass["price"] = building.price.get()
                if not isinstance(building, Extra):
                    buildingClass["type"] = building.forecastName.get()
                    buildingClass["k"] = building.k.get()
                    buildingClass["b"] = building.b.get()
                
                exportData[sf.title].append(buildingClass)

        files = [('JavaScript Object Notation', '*.json')]
        with fd.asksaveasfile(filetypes = files, defaultextension = files) as file:
            json.dump(exportData, file, indent = 4, ensure_ascii=False)
        messagebox.showinfo("Экспорт", "Сессия сохранена")
        
    def importSession(self):
        importData = {}
        
        files = [('JavaScript Object Notation', '*.json')]
        with fd.askopenfile(filetypes = files, defaultextension = files) as file:
            importData = json.load(file)
        
        for sf in self.shopFragments:
            for buildingID in sf.buildings.copy().keys():
                sf.delBuilding(buildingID)
            for buildingClass in importData[sf.title]:
                sf.addBuilding(**buildingClass)
        messagebox.showinfo("Импорт", "Сессия загружена")

    def openForecast(self):
        delimiter = self.options["Разделитель в csv"].get()
        if delimiter=="\\t":
            delimiter = "\t"
        path = self.path.get()
        
        values = []
        keys = []

        with open(path, newline='', encoding="utf-8") as f:
            fl = True
            rows = csv.reader(f, delimiter=delimiter)
            for row in rows:
                if fl:
                    keys = row
                    fl = False
                    for _ in range(len(keys)):
                        values.append([0])
                else:
                    for i, v in enumerate(row):
                        try:
                            values[i].append(float(v))
                        except ValueError:
                            values[i].append(0)
            
        self.forecast = dict(zip(keys, values))
        self.dt.setupForecast()
        print(self.forecast.keys())
        messagebox.showinfo("Погода", "Погода загружена")

        
    def chooseFilePath(self):
        path = fd.askopenfilename()
        if path[-3:] == "csv":
            self.path.set(path)
            self.openForecast()
        else:
            self.path.set("Не верный файл")

    def addTeam(self):
        i = max(self.teams.keys())+1 if len(self.teams.keys())>0 else 0
        frame = ttk.Frame(self.graphsFrame)
        frame.pack(side="left", anchor="n")
        
        self.teams[i] = {}
        self.teams[i]["frame"]=frame
        self.teams[i]["weatherGraph"] = Graph(frame, width=300, height=300, bg="#1F1F1F", showTitle=self.options["Заголовки графика погоды"])
        self.teams[i]["energyGraph"] = Graph(frame, width=300, height=300, bg="#1F1F1F", showTitle=self.options["Заголовки графика энергии"])
        self.teams[i]["moneyGraph"] = Graph(frame, width=300, height=300, bg="#1F1F1F", showTitle=self.options["Заголовки графика дохода"])
        self.teams[i]["textvar"] = StringVar()
        
        self.teams[i]["textvar"].set("Команда №"+str(len(self.teams.keys())-1))
        ttk.Label(frame, textvariable=self.teams[i]["textvar"]).pack(anchor="n")
        ttk.Button(frame, text="-", command=lambda: self.delTeam(i)).pack(anchor="n", fill="x")
        self.teams[i]["weatherGraph"].pack(anchor="n")
        self.teams[i]["energyGraph"].pack(anchor="n")
        self.teams[i]["moneyGraph"].pack(anchor="n")

    def delTeam(self, i):
        self.teams[i]["frame"].destroy()
        self.teams.pop(i)
        for teamnum, team in enumerate(self.teams.keys()):
            self.teams[team]["textvar"].set("Команда №"+str(teamnum))
    
    def drawGraphs(self):
        self.dt.clear()
        for sf in self.shopFragments:
            sf.shortPredict()
            for building in sf.buildings.values():
                self.dt.append(building["object"])
                team = building["object"].team.get()
                if self.privateParams["teamColors"].get(team)==None:
                    color = "#666666"
                    for _ in range(10):
                        color = self.randColor()
                        if color not in self.privateParams["teamColors"].values():
                            break
                    self.privateParams["teamColors"][team] = color
                    styleObject = ttk.Style()
                    self.changeStyle(styleObject, building["frame"], color, team)
                else:
                    self.changeReadyStyle(building["frame"], team)
                

        for teamnum, team in enumerate(self.teams.keys()):
            graphs = self.dt.getForecastGraph(teamnum)
            for graph in graphs.values():
                self.teams[team]["weatherGraph"].addGraph(**graph)
            self.teams[team]["weatherGraph"].draw()

            graphs = self.dt.getEnergyGraph(teamnum)
            for graph in graphs.values():
                self.teams[team]["energyGraph"].addGraph(**graph)
            self.teams[team]["energyGraph"].draw()
            
            graphs = self.dt.getMoneyGraph(teamnum)
            for graph in graphs.values():
                self.teams[team]["moneyGraph"].addGraph(**graph)
            self.teams[team]["moneyGraph"].draw()
        

# Рамка с покупкой и предсказанием
class ShopFragment(ttk.Frame):
    def __init__(self, window, BuildingClass, parent=None, title=None, **params):
        super().__init__(parent, **params)

        self.window = window

        self.title = title
        
        if title!=None:
            ttk.Label(self, text=title, anchor="s", font="Arial 15 bold").pack(anchor="n")
            self.shortPredictText = StringVar()
            self.shortPredictText.set("Минимальный доход: None")
            ttk.Label(self, textvariable=self.shortPredictText, anchor="s", font="Arial 10 bold").pack(anchor="n")

        self.BuildingClass = BuildingClass
        self.predictBuilding = self.createPredictFrame()
        
        self.buildings = {}
        
        self.shopFrame = ttk.Frame(self)
        self.shopTitle = StringVar()
        self.shopTitle.set("Всего строений: 0")
        shopLabel = ttk.Label(self.shopFrame, textvariable=self.shopTitle)
        self.buyButton = ttk.Button(self, text="Добавить строение", command=self.addBuilding)
        self.shopFrame.pack(anchor="n", fill="both")
        shopLabel.pack(anchor="n")
        self.buyButton.pack(anchor="s", fill="both")

    def addBuilding(self, **loadParams):
        frame = ttk.Frame(self.shopFrame, borderwidth=1, relief=SOLID)
        frame.pack(anchor="n", fill="both", pady=2)

        gridFrame = ttk.Frame(frame)
        gridFrame.pack(anchor="ne", fill="y")

        buildingClass = self.BuildingClass()

        if isinstance(buildingClass, Building):
            if len(buildingClass.forecastNames)>1:
                tcp = ComboParam(gridFrame, buildingClass.forecastNames, titleParams={"text":"Тип"})
                tcp.grid(column=0, row=0, rowspan=2, padx=3)
                if loadParams.get("type")!=None:
                    tcp.value.set(loadParams["type"])
                else:
                    tcp.value.set(self.predictBuilding.forecastName.get())
                buildingClass.setForecastName(tcp.value)
            else:
                staticTypeParam = StringVar()
                staticTypeParam.set(buildingClass.forecastNames[0])
                buildingClass.setForecastName(staticTypeParam)

            team = EntryParam(gridFrame, IntVar, titleParams={"text":"Команда"})
            pep = EntryParam(gridFrame, IntVar, titleParams={"text":"Цена"})
            kep = EntryParam(gridFrame, IntVar, titleParams={"text":"Коэффицент"})
            bep = EntryParam(gridFrame, IntVar, titleParams={"text":"Порог"})

            team.grid(column=1, row=0, padx=3)
            pep.grid(column=2, row=0, padx=3)
            kep.grid(column=1, row=1, padx=3)
            bep.grid(column=2, row=1, padx=3)

            team.value.set(self.window.options["Номер моей команды"].get() if loadParams.get("team")==None else loadParams["team"])
            pep.value.set(5 if loadParams.get("price")==None else loadParams["price"])
            kep.value.set(self.predictBuilding.k.get() if loadParams.get("k")==None else loadParams["k"])
            bep.value.set(self.predictBuilding.b.get() if loadParams.get("b")==None else loadParams["b"])
        
            buildingClass.setParams(team.value, pep.value, kep.value, bep.value)

        elif isinstance(buildingClass, Extra):
            team = EntryParam(gridFrame, IntVar, titleParams={"text":"Команда"})
            pep = EntryParam(gridFrame, IntVar, titleParams={"text":"Цена"})

            team.grid(column=1, row=0, padx=3)
            pep.grid(column=2, row=0, padx=3)

            team.value.set(self.window.options["Номер моей команды"].get() if loadParams.get("team")==None else loadParams["team"])
            pep.value.set(5 if loadParams.get("price")==None else loadParams["price"])
            
            buildingClass.setParams(team.value, pep.value, self.window.options)

        building = {
            "frame":frame,
            "object":buildingClass}
        
        """
        styleObject = ttk.Style()
        self.window.changeStyle(styleObject, frame, "#000000", 123456)
        """
        
        lastID = max(self.buildings.keys()) if len(self.buildings)>0 else -1
        myID = lastID+1

        self.buildings[myID] = building

        delButton = ttk.Button(gridFrame, text="-", command=lambda: self.delBuilding(myID), width=2)
        delButton.grid(column=3, row=0, sticky="ns", rowspan=2)
        delPredictButton = ttk.Button(gridFrame, text="?", width=2, command=lambda: self.dropPredict(myID))
        delPredictButton.grid(column=4, row=0, sticky="ns", rowspan=2)

        shopTitle = self.shopTitle.get()
        i = shopTitle.rfind("/d+")
        num = int(shopTitle[i:])+1
        self.shopTitle.set("Всего строений: "+str(num))

    def delBuilding(self, buildingID):
        self.buildings[buildingID]["frame"].destroy()
        self.buildings.pop(buildingID)

        shopTitle = self.shopTitle.get()
        i = shopTitle.rfind("/d+")
        num = int(shopTitle[i:])-1
        self.shopTitle.set("Всего строений: "+str(num))

    def createPredictFrame(self, **frameParams):
        buildingPredict = self.BuildingClass()
        
        predictFrame = ttk.Frame(self, **frameParams)
        predictTitle = ttk.Label(self, text="Изменения при покупке")
        predictParamsFrame = ttk.Frame(predictFrame, **frameParams)

        if isinstance(buildingPredict, Building):
            if len(buildingPredict.forecastNames)>1:
                tcp = ComboParam(predictParamsFrame, buildingPredict.forecastNames, titleParams={"text":"Тип"})
                tcp.grid(column=0, row=0, padx=3)
                buildingPredict.setForecastName(tcp.value)
            else:
                staticTypeParam = StringVar()
                staticTypeParam.set(buildingPredict.forecastNames[0])
                buildingPredict.setForecastName(staticTypeParam)
                
            kep = EntryParam(predictParamsFrame, IntVar, titleParams={"text":"Коэффицент"})
            bep = EntryParam(predictParamsFrame, IntVar, titleParams={"text":"Порог"})
            kep.value.set(1)
            bep.value.set(0)

            team = self.window.options["Номер моей команды"]

            pep = IntVar()
            pep.set(5)

            buildingPredict.setParams(team, pep, kep.value, bep.value)

            kep.grid(column=1, row=0, padx=3)
            bep.grid(column=2, row=0, padx=3)
            
        elif isinstance(buildingPredict, Extra):
            team = IntVar()
            team.set(0)
            pep = IntVar()
            pep.set(5)
            buildingPredict.setParams(team, pep, self.window.options)
            
        
        predictButton = ttk.Button(predictFrame, text="Расчитать", command=self.callPredictWindow)
        
        predictFrame.pack()
        predictTitle.pack()
        predictParamsFrame.pack()
        predictButton.pack()

        return buildingPredict

    def shortPredict(self):
        team = self.window.options["Номер моей команды"].get()
        report = PredictWindow.predict(self.window, self.predictBuilding, teams=[team])[team]
        self.shortPredictText.set(f"Минимальный доход: {report['minIncomePrice']}\nДизбаланс: {report['energySumBefore']} => {report['energySumAfter']}")

    def callPredictWindow(self):
        PredictWindow(self.window, self, background = '#333333')

    def dropPredict(self, buildingID):
        DropPredictWindow(self.window, self, buildingID, background = '#333333')
        

# Запуск программы, инициализация стилей
if __name__=="__main__":
    window = Window()
    window['bg']="#333333"
    style = ttk.Style()
    style.theme_use('alt')
    
    style.configure('TLabel', font="Arial 10", background = '#333333', foreground = '#DDDDDD', fieldbackground="#000000", selectbackground="#666666")
    style.configure('TFrame', font="Arial 10", background = '#333333', foreground = '#DDDDDD', fieldbackground="#000000", selectbackground="#666666")
    style.configure('TCombobox', font="Arial 10", background = '#333333', foreground = '#DDDDDD', fieldbackground="#000000", selectbackground="#666666")
    style.map('TCombobox', fieldbackground=[('readonly','black')])
    style.configure('TButton', font="Arial 10", background = '#333333', foreground = '#DDDDDD', fieldbackground="#000000", selectbackground="#666666")
    style.map("TButton", background=[("active", "#666666")])
    style.configure('TEntry', font="Arial 10", background = '#333333', foreground = '#DDDDDD', fieldbackground="#000000", selectbackground="#666666")
    style.configure('TCheckbutton', font="Arial 10", background = '#333333', foreground = '#DDDDDD', fieldbackground="#000000", selectbackground="#666666")
    style.map("TCheckbutton", background=[("active", "#666666")])
    window.mainloop()
