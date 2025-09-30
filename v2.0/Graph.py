import tkinter as tk
from tkinter import *
from tkinter import filedialog as fd
from tkinter import ttk
from tkinter import messagebox

# Виджет графиков
class Graph(Canvas):

    #Инвертировать hex цвет
    @staticmethod
    def invcolor(color):
        red = 255-int(color[1:3], 16)
        green = 255-int(color[3:5], 16)
        blue = 255-int(color[5:7], 16)
        return f"#{red:02x}{green:02x}{blue:02x}"
    
    def __init__(self, parent=None, **params):
        super().__init__(parent)
        self.soptions = {
            "showTitle":True
        }
        self.configure(**params)
        self.graph_queue = []

        self.create_text(self.width/2, self.height/2+15, text="График", fill=self.invcolor(self.bg), anchor=S, font="Arial 10 bold")

    # Своя конфигурация
    # Новый параметр showTitle - показ имён графиков
    def configure(self, **params):
        if params.get("bg")==None:
            self.bg = "#FFFFFF"
            params["bg"] = "#FFFFFF"
        else:
            self.bg = params.get("bg")
        if params.get("width")==None:
            self.width = 250
            params["width"] = 250
        else:
            self.width = params.get("width")
        if params.get("height")==None:
            self.height = 250
            params["height"] = 250
        else:
            self.height = params.get("height")
        if params.get("showTitle")==None:
            self.soptions["showTitle"] = True
        else:
            self.soptions["showTitle"] = params.get("showTitle")
            params.pop("showTitle")
        super().configure(**params)

    # Добавить график
    def addGraph(self, valY=None, valX=None, title=None, color=None):
        if valY==None or len(valY)==0:
            valY = [0]
        if color==None:
            color = self.invcolor(self.bg)
        if valX==None or len(valX)==0:
            valX = list(range(0, len(valY)))
        if title==None:
            title=""

        # Данные графика
        graph = {
            "valX":valX,
            "valY":valY,
            "title":title,
            "color":color
        }
        
        self.graph_queue.append(graph)

    # Отрисовка (лучше не трогать)
    def draw(self):
        self.delete("all")
        
        maxY = 0
        minY = 0
        maxX = 0
        minX = 0
        for graph in self.graph_queue:
            graphMaxY = max(graph["valY"])
            graphMinY = min(graph["valY"])
            if graphMaxY>maxY:
                maxY = graphMaxY
            if graphMinY<minY:
                minY = graphMinY

            graphMaxX = max(graph["valX"])
            graphMinX = min(graph["valX"])
            if graphMaxX>maxX:
                maxX = graphMaxX
            if graphMinX<minX:
                minX = graphMinX

        maxY = int(maxY)+1
        minY = int(minY)-1
        maxX = int(maxX)+1
        minX = int(minX)-1
                
        dY = maxY-minY
        dX = maxX-minX
        
        GAP = 20+int(5*(len(str(max(abs(maxY), abs(minY))))-1))
        EXTENDLINE = GAP*0.7
        LINEWIDTH = 3
        STROKESIZE = 3
        STROKEGAP = 25+int(3*(len(str(max(abs(maxX), abs(minX))))-1))
        
        x0 = (abs(minX)/dX)*(self.width-2*GAP)
        y0 = (1-abs(maxY)/dY)*(self.height-2*GAP)
        
        
        self.create_line(GAP+x0, self.height-GAP+EXTENDLINE, GAP+x0, GAP-EXTENDLINE, fill=self.invcolor(self.bg), arrow="last", width=LINEWIDTH)
        self.create_line(GAP-LINEWIDTH/2-EXTENDLINE, self.height-GAP-y0, self.width-GAP+EXTENDLINE, self.height-GAP-y0, fill=self.invcolor(self.bg), arrow="last", width=LINEWIDTH)

        xParts = (self.width-2*GAP)//STROKEGAP
        if xParts>dX:
            xParts = dX
        else:
            xParts=int(1/((dX//xParts)/dX))
            
        yParts = (self.height-2*GAP)//STROKEGAP
        if yParts>dY:
            yParts = dY
        else:
            yParts=int(1/((dY//yParts)/dY))
        
            
        for xPart in range(xParts+1):
            rawNum = dX-(dX//xParts)*xPart
            num = rawNum+minX
            if num==0:
                continue
            
            x = GAP+(rawNum/dX)*(self.width-2*GAP)
            self.create_line(x, self.height-GAP-STROKESIZE-y0, x, self.height-GAP+STROKESIZE+1-y0, width=LINEWIDTH, fill=self.invcolor(self.bg))
            self.create_text(x, self.height-(GAP+STROKESIZE)*0.7-y0, text=str(num), fill=self.invcolor(self.bg), anchor=N)
                 
        for yPart in range(yParts+1):
            rawNum = dY-(dY//yParts)*yPart
            num = rawNum+minY
            if num==0:
                continue
            
            y = GAP+(self.height-2*GAP)-(rawNum/dY)*(self.height-2*GAP)
            self.create_line(GAP-STROKESIZE+x0, y, GAP+STROKESIZE+1+x0, y, width=LINEWIDTH, fill=self.invcolor(self.bg))
            self.create_text((GAP-STROKESIZE)*0.9+x0, y, text=str(num), fill=self.invcolor(self.bg), anchor=E)
        
        # ZERO
        self.create_text(GAP+x0-4, self.height-GAP-y0+4, text="0", fill=self.invcolor(self.bg), anchor=NE)
            
        titles = []
        for i, graph in enumerate(self.graph_queue):
            x0 = graph["valX"][0] + abs(minX)
            y0 = graph["valY"][0] + abs(minY)
            x0 = GAP+(x0/dX)*(self.width-2*GAP)
            y0 = GAP+(self.height-2*GAP)-(y0/dY)*(self.height-2*GAP)
            for x1, y1 in zip(graph["valX"][1:], graph["valY"][1:]):
                x1 += abs(minX)
                y1 += abs(minY)
                x1 = GAP+(x1/dX)*(self.width-2*GAP)
                y1 = GAP+(self.height-2*GAP)-(y1/dY)*(self.height-2*GAP)
                self.create_line(x0, y0, x1, y1, smooth=True, width=LINEWIDTH, fill=graph["color"])
                x0, y0 = x1, y1
            if graph["title"]!=None:
                titles.append( (i, graph["title"], graph["color"]) )

        if self.soptions["showTitle"].get():
            for i, title, color in titles:
                self.create_text(self.width-GAP+EXTENDLINE, self.height-GAP-15*(i+1), text=title, fill=color, anchor=SE, font="Arial 10 bold")
    
        self.graph_queue.clear()


