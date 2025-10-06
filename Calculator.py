import numpy as np
import CoolProp.CoolProp as CP
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg,
                                               NavigationToolbar2Tk)
from tkinter import *
from tkinter import ttk
import math

round_to_n = lambda x, n: int(0) if x == 0 else round(x, -int(math.floor(math.log10(abs(x)))) + (n - 1))

class Value(ttk.Frame):
  def __init__(self, parent, label, units, onChange):
    Frame.__init__(self, parent, pady=5, padx=5)

    # variables
    if units != "K" and units != "C" and units != "F":
      self.conversionTexts = [f"{units}", f"{units}", f"K{units}",f"M{units}",f"G{units}"]
    else:
      self.conversionTexts = [f"{units}","K","C","F"]
    self.units = StringVar(self, value=f"{units}")
    self.value = NONE
    self.valueText = StringVar(self, value="")
    self.container = ttk.Frame(parent)
    self.selected = BooleanVar(self, value=False)
    self.copied = BooleanVar(self, value=False)
    self.driven = False
    self.OnChange = onChange

    # tkinter setup
    ttk.Label(self, text=label).grid(row=0,column=0)
    self.txt = ttk.Entry(self,textvariable = self.valueText)
    if units != "":
      ttk.OptionMenu(self, self.units, *self.conversionTexts).grid(row=0,column=1)
    self.txt.grid(row=1,column=0,columnspan=2)
    
    #add traces
    self.units.trace_add('write', self.Write)
    self.trace = self.valueText.trace_add('write', self.Write)
  
  def Write(self,a,b,c):
    if not self.driven:
      self.selected.set(len(self.valueText.get()) > 0)
    self.OnChange()

  
  def SetSelected(self, value):
    self.selected = value
  
  def SetDriven(self, value):
    self.driven = value
    if value:
      self.txt.config(state="disabled")
    else:
      self.txt.config(state="enabled")
      if not self.selected.get():
        self.SetValue("")
  
  def ConvertToSI(self,value):
    match self.units.get():
      case "C":
        return value + 273
      case "F":
        return (value - 32)*(5/9)+273
      case "":
        return value
      case "K":
        return value
    match self.units.get()[0]:
      case "K":
        return value*1e3
      case "M":
        return value*1e6
      case "G":
        return value*1e9
    return value
  
  def ConvertFromSI(self,value):
    match self.units.get():
      case "C":
        return value - 273
      case "F":
        return (value - 273)/(5/9)+32
      case "":
        return value
      case "K":
        return value
    match self.units.get()[0]:
      case "K":
        return value/1e3
      case "M":
        return value/1e6
      case "G":
        return value/1e9
    return value
  
  def GetValue(self):
    if self.driven:
      return self.value
    try:
      return self.ConvertToSI(float(self.valueText.get()))
    except ValueError:
      self.SetValue("0")
      return 0
  
  def SetValue(self, value=NONE):
    self.valueText.trace_remove('write', self.trace)
    try:
      self.value = value
      self.valueText.set(round_to_n(self.ConvertFromSI(float(value)),4))
    except ValueError:
      self.value = 0
      self.valueText.set("")
    self.trace = self.valueText.trace_add('write', self.Write)

class Cycle(ttk.Frame):
  def __init__(self, parent):
    Frame.__init__(self, parent)

    self.states = []
    for i in range(0,6):
      s = Value(self,f"s{i+1}","S",lambda i=i :self.OnChange(i,0))
      s.grid(row=i,column=0,sticky="S")
      h = Value(self,f"h{i+1}","J/KG",lambda i=i :self.OnChange(i,1))
      h.grid(row=i,column=1,sticky="S")
      t = Value(self,f"t{i+1}","C",lambda i=i :self.OnChange(i,2))
      t.grid(row=i,column=2,sticky="S")
      p = Value(self,f"p{i+1}","Pa",lambda i=i :self.OnChange(i,3))
      p.grid(row=i,column=3,sticky="S")
      x = Value(self,f"X{i+1}","",lambda i=i :self.OnChange(i,4))
      x.grid(row=i,column=4,sticky="S")
      self.states.append([s,h,t,p,x])
    
    # vertical links
    self.links = [[1,NONE,NONE,5,NONE],[0,NONE,NONE,2,NONE],[3,NONE,NONE,1,NONE],[2,NONE,NONE,4,NONE],[5,NONE,NONE,3,NONE],[4,NONE,NONE,0,NONE]]

    # coolprop text
    self.cpt = ["S","H","T","P","Q"]

    # solution textbox
    ttk.Label(self, text="Solution").grid(row=6)
    self.solutionText = Text(self, height=7, padx=10, state='disabled')
    self.solutionText.grid(row=7,columnspan=5)

    #calculate button
    self.calcButton = ttk.Button(self, text="Calculate", command=self.CalculateSolution, state='disabled')
    self.calcButton.grid(row=8,column=3)

    #graph button
    self.graphButton = ttk.Button(self, text="T-s Graph", command=self.ShowTsGraph, state='disabled')
    self.graphButton.grid(row=8,column=4)

    # graph stuff
    self.fig = plt.Figure(figsize=(6, 5), dpi=100)
    self.ts = self.fig.add_subplot()
    self.canvas = FigureCanvasTkAgg(self.fig, master=self)  # A tk.DrawingArea.
    self.canvas.draw()
    self.toolbar = NavigationToolbar2Tk(self.canvas, self, pack_toolbar=False)
    self.toolbar.update()

    self.toolbar.grid(row=8,column=5,sticky="sw")
    self.canvas.get_tk_widget().grid(row=0,rowspan=8,column=5)

    self.ts.set_xlabel("Entropy (S)")
    self.ts.set_ylabel("Temperature (K)")
    self.ts.set_title("T-s Graph")
  
  def OnChange(self,state,value):
    thisValue = self.states[state][value]

    selectedInState = self.GetSelectedInState(state)
    
    #update this states UI state
    for i in range(0,5):
      x = self.states[state][i]
      x.SetDriven((not x.selected.get() and selectedInState == 2) or x.copied.get())

    #update values in this state
    if selectedInState == 2:
      knowns = self.GetKnownInState(state)
      for i in range(0,5):
        if i == knowns[0][0] or i == knowns[1][0]:
          continue
        x = self.states[state][i]
        try:
          x.SetValue(CP.PropsSI(self.cpt[i], self.cpt[knowns[0][0]], knowns[0][1], self.cpt[knowns[1][0]], knowns[1][1], 'water'))
        except ValueError:
          x.SetValue()

    # check links with other states
    for i in range(0,5):
      x = self.states[state][i]
      self.Link(state,i)
    
    #check if it is now solvable or not
    if self.IsSolvable():
      self.calcButton.config(state='enabled')
      self.graphButton.config(state='enabled')
    else: 
      self.calcButton.config(state='disabled')
      self.graphButton.config(state='disabled')
    
    self.solutionText.config(state="normal")
    self.solutionText.delete("1.0", END)
    self.solutionText.config(state="disabled")

  
  #cross state link
  def Link(self, state, value):
    thisValue = self.states[state][value]
    otherState = self.links[state][value]

    if otherState != NONE:
      other = self.states[otherState][value]
      selectedInOtherState = self.GetSelectedInState(otherState)
      
      #update other state's UI state
      if other.copied.get() != ((thisValue.driven or thisValue.selected.get()) and not (thisValue.copied.get())) and (selectedInOtherState < 2 or other.copied.get()):
        other.copied.set(not other.copied.get())
        other.OnChange()
      
      # update other state's value
      if other.copied.get() and other.GetValue() != thisValue.GetValue():
        other.SetValue(thisValue.GetValue())
        other.OnChange()
        
  
  #returns the number of values in that state that are selected
  def GetSelectedInState(self, state):
    selectedInState = 0
    for x in self.states[state]:
      if x.selected.get() or x.copied.get():
        selectedInState += 1
    return selectedInState

  # returns the 2 known values for a state:
  def GetKnownInState(self, state):
    known = []
    for i in range(0,5):
      x = self.states[state][i]
      if x.selected.get():
        known.append([i,x.GetValue()])
      if x.copied.get():
        otherState = self.links[state][i]
        other = self.states[otherState][i]
        known.append([i,other.GetValue()])
    
    return known
  
  def IsSolvable(self):
    solveable = True
    for i in range (0,6):
      solveable = solveable and self.GetSelectedInState(i) == 2
    
    return solveable
  
  # calculates final values and displays them
  def CalculateSolution(self):

    #enthalpy values
    h1 = self.states[0][1].GetValue()
    h2 = self.states[1][1].GetValue()
    h3 = self.states[2][1].GetValue()
    h4 = self.states[3][1].GetValue()
    h5 = self.states[4][1].GetValue()
    h6 = self.states[5][1].GetValue()
      
    # Energy Balace
    w_pump = h2 - h1
    q_in_1 = h3 - h2
    w_turb_1 = h3 - h4
    q_in_2 = h5 - h4
    w_turb_2 = h5 - h6
    q_out = h6 - h1

    # Required System Parameters
    w_net = w_turb_1 + w_turb_2 - w_pump # [J/kg] specific net work done
    q_total = q_in_1 + q_in_2 # [J/kg] specific total heat supplied
    eta_th = (w_net/q_total)*100 # [%] thermal efficiency in percentage


    #temperature values
    t1 = self.states[0][2].GetValue()
    t6 = self.states[5][2].GetValue()

    # print results
    self.solutionText.config(state="normal")
    self.solutionText.delete("1.0", END)
    self.solutionText.insert(1.0,f'specific work input into pump (W_p):    {w_pump/1e3:.2f} KJ/kg\n')
    self.solutionText.insert(2.0,f'specific work rejected (Q_out):         {q_out/1e6:.3f} MJ/kg\n')
    self.solutionText.insert(3.0,"\n")
    self.solutionText.insert(4.0,f'net specific work done (W_net):         {w_net/1e6:.3f} MJ/kg\n')
    self.solutionText.insert(5.0,f'specific heat input (Q_total):          {q_total/1e6:.3f} MJ/kg\n')
    self.solutionText.insert(6.0,f'thermal efficiency in percentage:       {eta_th:.2f} %\n')
    self.solutionText.config(state="disabled")
  
  def ShowTsGraph(self):
    #entropy values
    s1 = self.states[0][0].GetValue()
    s2 = self.states[1][0].GetValue()
    s3 = self.states[2][0].GetValue()
    s4 = self.states[3][0].GetValue()
    s5 = self.states[4][0].GetValue()
    s6 = self.states[5][0].GetValue()

    #temperature values
    t1 = self.states[0][2].GetValue()
    t2 = self.states[1][2].GetValue()
    t3 = self.states[2][2].GetValue()
    t4 = self.states[3][2].GetValue()
    t5 = self.states[4][2].GetValue()
    t6 = self.states[5][2].GetValue()

    #pressure value
    p2 = self.states[1][3].GetValue()

    # setup T-s graph
    self.ts.cla()
    self.ts.set_xlabel("Entropy (S)")
    self.ts.set_ylabel("Temperature (K)")
    self.ts.set_title("T-s Graph")
    # saturation line
    t_min = CP.PropsSI('Ttriple', 'water')
    t_crit = CP.PropsSI('Tcrit', 'water')
    t_values = np.linspace(t_min, t_crit, 500)
    s_liq = [CP.PropsSI('S', 'T', t, 'Q', 0, 'water') for t in t_values]
    s_vap = [CP.PropsSI('S', 'T', t, 'Q', 1, 'water') for t in t_values]
    self.ts.plot(s_liq, t_values, '--k')
    self.ts.plot(s_vap, t_values, '--k')

    #plot points
    x_points = np.array([s3,s4,s5,s6,s1,s2])
    y_points = np.array([t3,t4,t5,t6,t1,t2])
    self.ts.plot(x_points, y_points, 'ko') # points
    self.ts.plot(x_points, y_points, 'b') # line

    # Between states for states 2-3 (non linear)
    s2_3 = np.linspace(s2, s3, 100)
    t2_3 = [CP.PropsSI('T', 'P', p2, 'S', s, 'water') for s in s2_3]
    self.ts.plot(s2_3, t2_3, 'b')

    self.canvas.draw()