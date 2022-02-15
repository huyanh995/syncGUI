import tkinter as tk
from tkinter import filedialog, messagebox
from functools import partial
from matplotlib.pyplot import text
from numpy import place, var
import torch

root = tk.Tk()
root.title("SBU Synchronization Tool")
# root.geometry("450x350") 
root.geometry("450x300") 
root.resizable(False, False) 
root.iconbitmap('icon.ico')


# def openLogWidow():
#     logWindow = tk.Toplevel(root)
#     logWindow.title("Log")
#     root_x = root.winfo_rootx() + int(450/2)
#     root_y = root.winfo_rooty()
#     logWindow.geometry("300x300+{}+{}".format(root_x, root_y))
#     logWindow.resizable(False, False)
#     doneButton = tk.Button(logWindow, text="Done", command=logWindow.destroy).pack(side=tk.BOTTOM)
def click_sync():
    file_screen = label_file_screen.cget("text")
    file_webcam = label_file_webcam.cget("text")
    file_egocentric = label_file_egocentric.cget("text")

    default = "No file choosen"
    if is_ws_sync.get():
        if file_screen != default and file_webcam != default:
            # Run script 1
            pass
        else:
            messagebox.showwarning("Warning", "Need both webcam and screen videos to run!")

    if is_wp_sync.get():
        if file_webcam != default and file_egocentric != default:
            # Run script 1
            pass
        else:
            messagebox.showwarning("Warning", "Need webcam and egocentric (POV) videos to run!")
    log = "WS {}, WP {}\nScreen {}\nWebcam {}\nEgo {}".format(is_ws_sync.get(), is_wp_sync.get(), file_screen, file_webcam, file_egocentric)
    messagebox.showwarning("Warning", log)

def openFile(label_des):
    filename = filedialog.askopenfilename(initialdir = "/",
                                          title = "Select a File",
                                        #   filetypes = (("Text files",
                                        #                 "*.txt*"),
                                        #                ("all files",
                                        #                 "*.*"))
                                                        )
    if filename != "":
        label_des.configure(text=filename) 

def selectDir(label_des):
    pass

def check_cuda():
    if not torch.cuda.is_available():
        messagebox.showwarning("Warning", "CUDA is not available!\nPlease run synchronization script on Colab")
        is_ws_sync.set(False) # Deselect checkbox

button = tk.Button(text="SYNC", bg='#54FA9B', command=click_sync)
button.place(x=330, y=235)

label_screen = tk.Label(root, text="Screen video")
label_file_screen = tk.Label(root, text="No file choosen", anchor=tk.W, width=50)
button_screen = tk.Button(text="Select", command=partial(openFile, label_file_screen))

label_webcam = tk.Label(root, text="Webcam video")
label_file_webcam = tk.Label(root, text="No file choosen")
button_webcam = tk.Button(text="Select", command=partial(openFile, label_file_webcam))

label_egocentric = tk.Label(root, text="Egocentric (POV)")
label_file_egocentric = tk.Label(root, text="No file choosen")
button_egocentric = tk.Button(text="Select", command=partial(openFile, label_file_egocentric))

is_ws_sync = tk.BooleanVar()
is_wp_sync = tk.BooleanVar()
ws_sync_button = tk.Checkbutton(root, text ='Sync Webcam and Screen', variable=is_ws_sync, onvalue=True, offvalue=False, command=check_cuda)
wp_sync_button = tk.Checkbutton(root, text ='Sync Webcam and POV', variable=is_wp_sync, onvalue=True, offvalue=False)

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

# label_default_output.place(x=20, y = 280)
# text_default_output.place(x=20, y = 310)
# button_default_output.place(x=330, y = 310)

root.mainloop()