# from utils import read_config
# from wp_sync import wp_sync_call

# config = read_config('config.json')
# print(config)

# file1 = './data/webcam.mp4'
# file2 = './data/egocentric.mp4'

# max_offset = config["config"]["wp"]["max_offset"]
# trim = config["config"]["wp"]["trim"]
# wp_sync_call(file1, file2, max_offset, trim)


# from tkinter import *
# from tkinter.ttk import *
# import time

# ws = Tk()
# ws.title('PythonGuides')
# ws.geometry('400x250+1000+300')

# def step():
#     for i in range(10):
#         ws.update_idletasks()
#         pb1['value'] += 5
        
#         time.sleep(0.01)

# pb1 = Progressbar(ws, orient=HORIZONTAL, length=350, mode='indeterminate')
# pb1.pack(expand=True)

# Button(ws, text='Start', command=step).pack()

# ws.mainloop()

# import tkinter as tk
# r=tk.Tk()
# r.title('hello')
# ''
# l= tk.Label(r, name='lbl', text='reduce the window width', width=10)
# l.pack(fill=tk.BOTH) # or tk.X, depends; check interactive resizing now

# tk.mainloop()

from tkinter import *
import tkinter

top = tkinter.Tk()

B1 = tkinter.Button(top, text ="FLAT", relief=FLAT )
B2 = tkinter.Button(top, text ="RAISED", relief=RAISED )
B3 = tkinter.Button(top, text ="SUNKEN", relief=SUNKEN )
B4 = tkinter.Button(top, text ="GROOVE", relief=GROOVE )
B5 = tkinter.Button(top, text ="RIDGE", relief=RIDGE )

B1.pack()
B2.pack()
B3.pack()
B4.pack()
B5.pack()
top.mainloop()