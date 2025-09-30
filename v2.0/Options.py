import tkinter as tk
from tkinter import *
from tkinter import filedialog as fd
from tkinter import ttk
from tkinter import messagebox

class Options():
    # Методы для удобства задания параметров
    # Добавить параметр
    def addParam(self, key, value, varClass=None):
        var = None
        if varClass!=None:
            var = varClass()
        elif type(value)==int:
            var = IntVar()
        elif type(value)==float:
                var = DoubleVar()
        elif type(value)==str:
            var = StringVar()
        elif type(value)==bool:
            var = BooleanVar()
        else:
            self.options[key] = None
            return
        var.set(value)
        self.options[key] = var

    # Добавить пустой параметр (заголовок)
    def addParamTitle(self, key):
        self.options[key] = None
    
    def exportOptions(self, file=None):
        exportData = {}
        for key, value in self.options.items():
            if value!=None:
                exportData[key] = value.get()

        if file==None:
            files = [('JavaScript Object Notation', '*.json')]
            with fd.asksaveasfile(filetypes = files, defaultextension = files) as file:
                json.dump(exportData, file, indent = 4, ensure_ascii=False)
        else:
            json.dump(exportData, file, indent = 4, ensure_ascii=False)
        messagebox.showinfo("Экспорт", "Настройки сохранены")

    def importOptions(self, file=None):
        importData = {}

        if file==None:
            files = [('JavaScript Object Notation', '*.json')]
            with fd.askopenfile(filetypes = files, defaultextension = files) as file:
                importData = json.load(file)
        else:
            importData = json.load(file)
        
        for key, value in importData.items():
            if self.options.get(key)!=None:
                self.options[key].set(value)
        messagebox.showinfo("Импорт", "Настройки загружены")
    


class OptionsWindow(Toplevel):
    def __init__(self, window, options, **windowParams):
        super().__init__(window, **windowParams)
        self.title("Параметры")
        
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
        self.bind("<MouseWheel>", self.on_mousewheel)

        for name, var in options.items():
            if var==None:
                ttk.Label(self.mainFrame, text=name, font="Arial 15 bold", anchor="s").pack(side="top", anchor="n")
            elif type(var)==BooleanVar:
                ttk.Checkbutton(self.mainFrame, text=name, variable=var).pack(side="top", anchor="n")
            else:
                ttk.Label(self.mainFrame, text=name, anchor="s").pack(side="top", anchor="n")
                ttk.Entry(self.mainFrame, textvariable=var).pack(side="top", anchor="n")

        ttk.Button(self, text="Закрыть", command=self.destroy).grid(row=2, column=0, sticky="we", columnspan=2, padx=10, pady=10)
        self.update_idletasks()
        
        self.geometry(f"{self.winfo_height()}x{self.winfo_width()}")

    def resize(self, event):
        region = self.canvas.bbox("all")
        self.canvas.configure(scrollregion=region)

    def on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
