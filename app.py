import subprocess
from glob import glob
import os
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox
import platform
from tkinter.ttk import Progressbar
from functools import partial
from threading import Thread

from utils import convert_to_30fps, read_config, recover_GP3_webcam, video_align, combine_audio_video, convert_to_30fps, split_path
from audio_sync import sync


class Sync(Thread):
    def __init__(self, is_upsampling, is_keepfiles, webcam, screen, audio, ego):
        super().__init__()
        # 4 sources of data
        self.webcam = webcam
        self.screen = screen
        self.screen_audio = audio
        self.ego = ego

        self.dir_name, _, _ = split_path(screen)

        # Boolean variables to control the flow
        self.is_upsampling = is_upsampling
        self.is_keepfiles = is_keepfiles
        self.config = read_config('config.json')

    def run(self):
        """
        Main function to run (both) scripts.
        Take inputs from globals() -> is_keepfiles_sync and is_upsampling_sync
        Return log and messages (for displaying)
        """
        message = ""
        log = ""
        global storage # Use to store data across many classes/objects
        # If I use thread.join(), it works but make GUI frozen.

        # Recover webcam from 10fps -> 30fps, algin with audio duration
        # webcam.avi -> re_webcam.avi
        self.webcam = recover_GP3_webcam(self.screen_audio, self.webcam)
        storage["inter_files"].append(self.webcam)
        # Align screen video to screen audio, then combine them
        self.screen = video_align(self.screen, self.screen_audio) # screen.avi -> align_screen.avi
        storage["inter_files"].append(self.screen)
        self.screen = combine_audio_video(self.screen, self.screen_audio) # align_screen.avi -> align_screen.mp4
        storage["inter_files"].append(self.screen)
        
        # Combine webcam and screen video
        self.webcam = combine_audio_video(self.webcam, self.screen_audio) # re_webcam.avi -> re_webcam.mp4
        storage["inter_files"].append(self.webcam)
        if self.is_upsampling:
            self.screen = convert_to_30fps(self.screen) # align_screen.mp4 -> align_screen_30fps.mp4
            storage["inter_files"].append(self.screen)
        # Sync egocentric and screen video
        self.ego, _ = sync(self.screen, self.ego) # egocentric.MP4 -> egocentric_sync.mp4

        # Save synced videos to new folder
        if os.path.isdir(self.dir_name):
            out_dir = os.path.join(self.dir_name, "synced_data")
            if os.path.exists(out_dir):
                shutil.rmtree(out_dir)
            os.mkdir(out_dir)

            _, _, ext = split_path(self.screen)
            shutil.copy(self.screen, os.path.join(out_dir, "synced_screen" + ext))

            _, _, ext = split_path(self.webcam)
            shutil.copy(self.webcam, os.path.join(out_dir, "synced_webcam" + ext))

            _, _, ext = split_path(self.ego)
            shutil.copy(self.ego, os.path.join(out_dir, "synced_egocentric" + ext))

            storage["out"] = out_dir
            storage["message"] = "Synced videos saved in {}".format(out_dir) + "\nDo you want to open it?"
            storage["inter_files"].append(self.ego)

        else:
            print("Something wrong!", print(self.dir_name))
            raise Exception

class App(tk.Tk):
    def __init__(self, machine):
        super().__init__()
        # Store file path
        self.webcam = None
        self.screen = None
        self.audio = None
        self.ego = None

        self.message = ""
        self.log = []

        self.title("SBU Synchronization Tool")

        # Geometry config
        self.geometry("450x340") 
        self.resizable(False, False) 
        self.eval('tk::PlaceWindow . center')
        self.machine = machine
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
        self.is_upsampling = tk.BooleanVar()
        self.is_upsampling.set(True)
        self.is_keepfiles = tk.BooleanVar()
        self.is_keepfiles.set(True)
        self.is_show_log = tk.BooleanVar()

        self.upsampling_button = tk.Checkbutton(self, text ='Upsampling screen video', variable=self.is_upsampling, onvalue=True, offvalue=False)
        self.keepfiles_button = tk.Checkbutton(self, text ='Remain intermediate files', variable=self.is_keepfiles, onvalue=True, offvalue=False)
        self.show_log_button = tk.Checkbutton(self, text = 'Show log', variable=self.is_show_log, onvalue=True, offvalue=False)
        
        self.upsampling_button.place(x = 20, y = 210)
        self.keepfiles_button.place(x = 20, y = 240)
        self.show_log_button.place(x= 20, y=270)

        # Progress Bar
        self.pbar = Progressbar(self, orient=tk.HORIZONTAL, length=410, mode='indeterminate')
        self.pbar.place(x=20, y=310)

        
    def open_file(self, file_type):
        filename = filedialog.askopenfilename(title = "Select a File")
        disp_text = "... " + filename[-33:] if len(filename) >= 37 else filename
        if filename != "":
            if file_type == 'webcam':
                self.webcam = filename
                self.label_file_webcam.configure(text=disp_text)
            elif file_type == "screen":
                self.screen = filename
                dir_name, file_name, ext = split_path(filename)
                self.audio = os.path.join(dir_name, file_name + ".mp3")
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
        warning = []
        res = True
        if not (self.webcam and self.screen and self.ego):
            warning.append("Need all webcam, screen, and egocentric videos to run.")
            res = False
        
        if self.audio and not os.path.isfile(self.audio):
            warning.append("Screen audio file is not found.")
            res = False

        return res, warning

        
    def click_sync(self):
        res, warning = self.check_condition()
        
        if res:
            # Disable button and run progress bar
            self.start_sync()

            # Create Sync thread and run it
            sync_thread = Sync(self.is_upsampling.get(), self.is_keepfiles.get(), self.webcam, self.screen, self.audio, self.ego)
            sync_thread.start()
            self.monitor(sync_thread)

        else:
            messagebox.showwarning(title = "Warning", message = "\n".join(warning))


    def start_sync(self):
        self.pbar.start(20)
        self.control_button("disabled")

    def stop_sync(self):
        self.pbar.stop()
        self.control_button("normal")
        global storage

        
        # Delete intermediate files 
        if not self.is_keepfiles.get():
            for f in storage["inter_files"]:
                if os.path.exists(f):
                    os.remove(f)
                else:
                    print("DEBUG >>", f, "does not exist!")

        if self.is_show_log.get():
            # Save log to file
            pass

        # messagebox.showinfo(message=storage["message"])

        answer = messagebox.askokcancel(title="", message=storage["message"])

        if answer:
            # Open folder
            if self.machine == "Windows":
                os.startfile(storage["out"])
            else:
                subprocess.call(["open", storage["out"]])

    
    def monitor(self, sync_thread):
        if sync_thread.is_alive():
            self.after(100, lambda: self.monitor(sync_thread))
        else:
            self.stop_sync()

if __name__ == "__main__":
    storage = {"message": "", "inter_files": [], "log": [], "out": ""}
    machine = platform.system()
    app = App(machine)
    app.mainloop()