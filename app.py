import tkinter as tk
from tkinter import filedialog, messagebox
import platform
from tkinter.ttk import Progressbar
from functools import partial
from threading import Thread


from utils import read_config
from wp_sync import wp_sync_call
from ws_sync import ws_sync_call


class Sync(Thread):
    def __init__(self, is_wp, is_ws, webcam, screen, ego):
        super().__init__()
        self.webcam = webcam
        self.screen = screen
        self.ego = ego
        self.is_wp = is_wp
        self.is_ws = is_ws
        self.config = read_config('config.json')

    def run(self):
        """
        Main function to run (both) scripts.
        Take inputs from globals() -> is_ws_sync and is_wp_sync
        Return log and messages (for displaying)
        """
        message = ""
        log = ""
        if self.is_ws:
            # Run script here  
            max_offset = self.config["config"]["wp"]["max_offset"]
            trim = self.config["config"]["wp"]["trim"]
            out_ws_sync, log_ws = ws_sync_call(self.screen, self.webcam, max_offset, trim)          
            message += "Synced webcam video: {}".format(out_ws_sync)

            log += log_ws
            
        if self.is_wp:
            # Run script 1
            if self.is_ws:
                # Rename the webcam to the new webcam file
                self.webcam = out_ws_sync
                
            max_offset = self.config["config"]["wp"]["max_offset"]
            trim = self.config["config"]["wp"]["trim"]
            out_wp_sync, log_wp = wp_sync_call(self.webcam, self.ego, max_offset, trim) # Run script

            # Store message and log to display
            if message != "":
                message += "\n"
                log += "\n"
            message += "Synced egocentric video: {}".format(out_wp_sync)
            log += log_wp

        # Save to global dictionary
        global store_message
        store_message["message"] = message
        store_message["log"] = log


class App(tk.Tk):
    def __init__(self, machine):
        super().__init__()
        # Store file path
        self.webcam = None
        self.screen = None
        self.ego = None

        self.title("SBU Synchronization Tool")

        # Geometry config
        self.geometry("450x340") 
        self.resizable(False, False) 
        self.eval('tk::PlaceWindow . center')
        if machine == "Windows":
            self.iconbitmap('icon.ico')


        # Label
        self.default = "No file chosen"
        self.label_screen = tk.Label(self, text="Screen video")
        self.label_file_screen = tk.Label(self, text=self.default, anchor=tk.W, width=60)

        self.label_webcam = tk.Label(self, text="Webcam video")
        self.label_file_webcam = tk.Label(self, text=self.default)

        self.label_egocentric = tk.Label(self, text="Egocentric (POV)")
        self.label_file_egocentric = tk.Label(self, text=self.default)

        self.label_screen.place(x=20, y=20)
        self.label_file_screen.place(x=60, y=50)
        self.label_webcam.place(x=20, y=80)
        self.label_file_webcam.place(x=60, y=110)
        self.label_egocentric.place(x=20, y=140)
        self.label_file_egocentric.place(x=60, y=170)

        # Buttons
        self.button = tk.Button(text="SYNC", command=self.click_sync)
        if machine == "Windows":
            self.button["bg"] = "green"
            self.button["width"] = 8
            self.button["height"] = 2
            self.button["relief"] = tk.GROOVE
            self.button.place(x=318, y=219)
        else:
            self.button.place(x=330, y=235)

        self.button_screen = tk.Button(text="Select", command=partial(self.open_file, "screen"), relief=tk.GROOVE)
        self.button_webcam = tk.Button(text="Select", command=partial(self.open_file, "webcam"), relief=tk.GROOVE)
        self.button_egocentric = tk.Button(text="Select", command=partial(self.open_file, "ego"), relief=tk.GROOVE)
        self.button_screen.place(x=330, y=50)
        self.button_webcam.place(x=330, y=110)
        self.button_egocentric.place(x=330, y=170)

        # Check buttons
        self.is_ws_sync = tk.BooleanVar()
        self.is_ws_sync.set(True)
        self.is_wp_sync = tk.BooleanVar()
        self.is_wp_sync.set(True)
        self.is_show_log = tk.BooleanVar()

        self.ws_sync_button = tk.Checkbutton(self, text ='Sync Webcam and Screen', variable=self.is_ws_sync, onvalue=True, offvalue=False)
        self.wp_sync_button = tk.Checkbutton(self, text ='Sync Webcam and POV', variable=self.is_wp_sync, onvalue=True, offvalue=False)
        self.show_log_button = tk.Checkbutton(self, text = 'Show log', variable=self.is_show_log, onvalue=True, offvalue=False)
        
        self.ws_sync_button.place(x = 20, y = 210)
        self.wp_sync_button.place(x = 20, y = 240)
        self.show_log_button.place(x= 20, y=270)

        # Progress Bar
        self.pbar = Progressbar(self, orient=tk.HORIZONTAL, length=410, mode='indeterminate')
        self.pbar.place(x=20, y=310)

        
    def open_file(self, file_type):
        filename = filedialog.askopenfilename(initialdir = "/", title = "Select a File")
        disp_text = "... " + filename[-33:] if len(filename) >= 37 else filename
        if filename != "":
            if file_type == 'webcam':
                self.webcam = filename
                self.label_file_webcam.configure(text=disp_text)
            elif file_type == "screen":
                self.screen = filename
                self.label_file_screen.configure(text=disp_text)
            elif file_type == "ego":
                self.ego = filename
                self.label_file_egocentric.configure(text=disp_text)


    def control_button(self, mode):
        self.button["state"] = mode
        self.button_webcam["state"] = mode
        self.button_screen["state"] = mode
        self.button_egocentric["state"] = mode


    def check_condition(self):
        warning = ""
        res = True
        if self.is_ws_sync.get():
            if not (self.webcam and self.screen):
                warning += "webcam, screen"
                res = False
        if self.is_wp_sync.get():
            if not (self.webcam and self.ego):
                if warning == "":
                    warning += "webcam, egocentric (POV)"
                else:
                    warning += ", egocentric (POV)"
                res = False

        return res, warning

        
    def click_sync(self):
        res, warning = self.check_condition()
        if res:
            if not (self.is_ws_sync.get() or self.is_wp_sync.get()):
                # Need to choose sync mode
                messagebox.showwarning("Warning", message="Choose sync mode!")
            else:
                # Run script
                self.start_sync()
                sync_thread = Sync(self.is_wp_sync.get(), self.is_ws_sync.get(), self.webcam, self.screen, self.ego)
                sync_thread.start()
                self.monitor(sync_thread)
        else:
            # Display warning
            messagebox.showwarning("Warning", "No {} videos to run!".format(warning))


    def start_sync(self):
        self.pbar.start(20)
        self.control_button("disabled")

    def stop_sync(self):
        self.pbar.stop()
        self.control_button("normal")

        global store_message
        if self.is_show_log.get():
            messagebox.showinfo(message="{}\n{}".format(store_message["message"], store_message["log"]))
        else:
            messagebox.showinfo(message=store_message["message"])
    
    def monitor(self, sync_thread):
        if sync_thread.is_alive():
            self.after(100, lambda: self.monitor(sync_thread))
        else:
            self.stop_sync()

if __name__ == "__main__":
    store_message = {"message": "", "log": ""}
    # is_wp = True
    # is_ws = False
    # webcam = "./data/webcam.mp4"
    # screen = "./data/screen.avi"
    # ego = "./data/egocentric.MP4"
    # sync = Sync(is_wp, is_ws, webcam, screen, ego)
    # sync.run()
    # print("DEBUG")
    machine = platform.system()
    app = App(machine)
    app.mainloop()