import numpy as np
import CoolProp.CoolProp as CP
import matplotlib.pyplot as plt
from matplotlib.backend_bases import key_press_handler
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)
from tkinter import *
from tkinter import ttk
from Calculator import Cycle

# Setup tkinter window
root = Tk()

cycle = Cycle(root)
cycle.grid(column=0, row=0)

root.mainloop()