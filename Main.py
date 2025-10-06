from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)
from tkinter import *
from Calculator import Cycle

# Setup tkinter window
root = Tk()

cycle = Cycle(root)
cycle.grid(column=0, row=0)

root.mainloop()