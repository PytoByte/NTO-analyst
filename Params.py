from tkinter import *
from tkinter import ttk

class EntryParam(ttk.Frame):
    def __init__(self, parent=None, varClass=StringVar, frameParams={}, titleParams={}, entryParams={}):
        super().__init__(parent, **frameParams)
        
        self.label = ttk.Label(self, **titleParams)

        self.value = varClass()
        self.entry = ttk.Entry(self, **entryParams, textvariable=self.value)
        
        self.label.pack(anchor="n")
        self.entry.pack(anchor="n")

class OptionParam(ttk.Frame):
    def __init__(self, parent=None, options=None, frameParams={}, titleParams={}, optionParams={}):
        super().__init__(parent, **frameParams)
        
        self.label = ttk.Label(self, **titleParams)

        if options==None:
            options = [None]

        self.value = StringVar()
        self.value.set(options[0])
        self.option = OptionMenu(self, self.value, *options, **optionParams)
        
        self.label.pack(anchor="n")
        self.option.pack(anchor="n")

class ComboParam(ttk.Frame):
    def __init__(self, parent=None, options=None, frameParams={}, titleParams={}, comboParams={}):
        super().__init__(parent, **frameParams)
        
        self.label = ttk.Label(self, **titleParams)

        if options==None:
            options = [None]

        self.value = StringVar()
        self.value.set(options[0])
        self.combo = ttk.Combobox(self, values=options, textvariable=self.value, **comboParams, state="readonly")
        
        self.label.pack(anchor="n")
        self.combo.pack(anchor="n")
