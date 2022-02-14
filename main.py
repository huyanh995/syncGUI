import tkinter as tk

from matplotlib.pyplot import text
from numpy import place

root = tk.Tk()
root.title("SBU Synchronization Tool")
root.geometry("450x300") 
root.resizable(False, False) 
button = tk.Button(text="SYNC", bg='#54FA9B').place(x=330, y=235)


# label_webcam = tk.Label(root, text="Face video").place(x=20, y=30)
# label_file_webcam = tk.Label(root, text="No file choosen").place(x=150, y=30)
# button_webcam = tk.Button(text="Select").place(x=330, y=30)

label_screen = tk.Label(root, text="Screen video").place(x=20, y=30)
label_file_screen = tk.Label(root, text="No file choosen").place(x=80, y=60)
button_screen = tk.Button(text="Select").place(x=330, y=60)

label_gazepoint = tk.Label(root, text="Webcam video").place(x=20, y=90)
label_file_gazepoint = tk.Label(root, text="No file choosen").place(x=80, y=120)
button_gazepoint = tk.Button(text="Select").place(x=330, y=120)

label_egocentric = tk.Label(root, text="Egocentric (POV)").place(x=20, y=150)
label_file_egocentric = tk.Label(root, text="No file choosen").place(x=80, y=180)
button_egocentric = tk.Button(text="Select").place(x=330, y=180)



# Create check button for sync options
java = tk.Checkbutton(root, text ='Webcam + Gazepoint').place(x = 20, y = 220)
java = tk.Checkbutton(root, text ='Webcam + Egocentric').place(x = 20, y = 250)

root.mainloop()