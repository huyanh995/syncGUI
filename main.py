from dis import dis
from logging import warning
import tkinter as tk
from tkinter import filedialog, messagebox
import platform
from tkinter.ttk import Progressbar
from functools import partial
from matplotlib.pyplot import text
from numpy import place, var
# import torch
import time

from utils import read_config
from wp_sync import wp_sync_call

machine = platform.system()

root = tk.Tk()
root.title("SBU Synchronization Tool")
# root.geometry("450x350") 
root.geometry("450x340") 
root.resizable(False, False) 
root.eval('tk::PlaceWindow . center')
if machine == "Windows":
    root.iconbitmap('icon.ico')

config = read_config('config.json')
default = "No file choosen"
file_screen = default
file_webcam = default
file_egocentric = default

"""
IDEA:
Show progressbar in the beginning.
If sync -> start the progressbar
When done -> stop it
Maybe need threading to start a script call
"""
def click_sync():
    # Get the config
    message = ""
    warning_mess = ""
    log = "=========\n"
    run = False
    progbar = False
    if is_ws_sync.get():
        if file_screen != default and file_webcam != default:
            
            message += "Synced webcam video: {}\n"
            run = True
            if not progbar:
                pb1 = Progressbar(root, orient=tk.HORIZONTAL, length=410, mode='indeterminate')
                for i in range(240):
                    #root.update_idletasks()
                    pb1['value'] += 5
                #time.sleep(1)
                pb1.place(x=20, y=310)
            progbar = True

            pass
        else:
            warning_mess += "webcam, screen"
            #messagebox.showwarning("Warning", "Need both webcam and screen videos to run!")

    if is_wp_sync.get():
        if file_webcam != default and file_egocentric != default:
            # Run script 1
            max_offset = config["config"]["wp"]["max_offset"]
            trim = config["config"]["wp"]["trim"]
            out_wp_sync, log_wp = wp_sync_call(file_webcam, file_egocentric, max_offset, trim)

            # Store message and log to display
            message += "Synced egocentric video: {}".format(out_wp_sync)
            log += log_wp
            run = True
            if not progbar:
                pb1 = Progressbar(root, orient=tk.HORIZONTAL, length=410, mode='indeterminate')
                for i in range(240):
                    #root.update_idletasks()
                    pb1['value'] += 5
                #time.sleep(1)
                pb1.place(x=20, y=310)
            progbar = True
        else:
            if warning_mess == "":
                warning_mess += "webcam, egocentric (POV)"
            else:
                warning_mess += ", egocentric (POV)"
        
            #messagebox.showwarning("Warning", "Need webcam and egocentric (POV) videos to run!")
    if run:
        if is_show_log:
            pb1.stop()
            messagebox.showinfo(message="{}\n{}".format(message, log))
        else:
            messagebox.showinfo(message=message)
    
    else:
        messagebox.showwarning("Warning", "No {} videos to run!".format(warning_mess))

    log = "WS {}, WP {}\nScreen {}\nWebcam {}\nEgo {}".format(is_ws_sync.get(), is_wp_sync.get(), file_screen, file_webcam, file_egocentric)

def openFile(label_des, file):
    filename = filedialog.askopenfilename(initialdir = "/",
                                          title = "Select a File",
                                        #   filetypes = (("Text files",
                                        #                 "*.txt*"),
                                        #                ("all files",
                                        #                 "*.*"))
                                                        )
    if filename != "":
        if file == 'webcam':
            global file_webcam
            file_webcam = filename
        elif file == "screen":
            global file_screen
            file_screen = filename
        elif file == "pov":
            global file_egocentric
            file_egocentric = filename

        if len(filename) >= 37:
            disp_text = "... " + filename[-33:]
        label_des.configure(text=disp_text) 

def selectDir(label_des):
    pass

def check_cuda():
    # if not torch.cuda.is_available():
    #     messagebox.showwarning("Warning", "CUDA is not available!\nPlease run synchronization script on Colab")
    #     is_ws_sync.set(False) # Deselect checkbox
    pass
if machine == "Windows":
    button = tk.Button(text="SYNC", bg='#54FA9B', command=click_sync)
    button.place(x=327, y=210)
else:
    button = tk.Button(text="SYNC", command=click_sync)
    button.place(x=330, y=235)

label_screen = tk.Label(root, text="Screen video")
label_file_screen = tk.Label(root, text=default, anchor=tk.W, width=60)
button_screen = tk.Button(text="Select", command=partial(openFile, label_file_screen, "screen"), relief=tk.GROOVE)

label_webcam = tk.Label(root, text="Webcam video")
label_file_webcam = tk.Label(root, text=default)
button_webcam = tk.Button(text="Select", command=partial(openFile, label_file_webcam, "webcam"), relief=tk.GROOVE)

label_egocentric = tk.Label(root, text="Egocentric (POV)")
label_file_egocentric = tk.Label(root, text=default)
button_egocentric = tk.Button(text="Select", command=partial(openFile, label_file_egocentric, "pov"), relief=tk.GROOVE)

is_ws_sync = tk.BooleanVar()
is_wp_sync = tk.BooleanVar()
is_show_log = tk.BooleanVar()
ws_sync_button = tk.Checkbutton(root, text ='Sync Webcam and Screen', variable=is_ws_sync, onvalue=True, offvalue=False, command=check_cuda)
wp_sync_button = tk.Checkbutton(root, text ='Sync Webcam and POV', variable=is_wp_sync, onvalue=True, offvalue=False)
show_log_button = tk.Checkbutton(root, text = 'Show log', variable=is_show_log, onvalue=True, offvalue=False)
is_ws_sync.set(True)
is_wp_sync.set(True)

# label_default_output = tk.Label(root, text="Default output")
# text_default_output = tk.Label(root, text="~")
# button_default_output = tk.Button(text="Select", command=partial(openFile, text_default_output))
# Format
label_screen.place(x=20, y=20)
label_file_screen.place(x=60, y=50)
button_screen.place(x=330, y=50)

label_webcam.place(x=20, y=80)
label_file_webcam.place(x=60, y=110)
button_webcam.place(x=330, y=110)

label_egocentric.place(x=20, y=140)
label_file_egocentric.place(x=60, y=170)
button_egocentric.place(x=330, y=170)
# Create check button for sync options

ws_sync_button.place(x = 20, y = 210)
wp_sync_button.place(x = 20, y = 240)
show_log_button.place(x= 20, y=270)

# label_default_output.place(x=20, y = 280)
# text_default_output.place(x=20, y = 310)
# button_default_output.place(x=330, y = 310)

root.mainloop()