import os
import shutil
import time
import subprocess
import webbrowser
import tkinter as tk
from tkinter import filedialog, messagebox
import platform
import socket
from queue import Queue
import csv
from threading import Thread
import traceback
import pandas as pd

from utils import read_config, write_config, parse
from control_OBS import OBS

class App(tk.Tk):
    def __init__(self, machine):
        super().__init__()
        
        self.config = read_config("config.yml")
        # OBS Init
        self.obs = OBS(self.config["OBS"])
        self.first_tick = None
        self.last_tick = None
        # GP3 threading variable
        self.gp3 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.gp3.settimeout(2.0)

        self.gp3_is_connect = False # Each socket only have to connect once
        self.obs_is_connect = False

        self.path = None

        # Geometry
        self.title("Experiment Launcher")
        self.geometry("450x200") 
        self.resizable(False, False) 
        self.eval('tk::PlaceWindow . center')
        self.machine = machine
        self.iconbitmap('icon.ico') if machine == "Windows" else None

        if not self.config["output"]:
            self.output_dir = os.path.join(os.environ['USERPROFILE'], 'Documents') if machine == "Windows" else "~/"
        else:
            self.output_dir = self.config["output"]

        # Label
        
        #self.userID = tk.StringVar(value="E.g 123456") # Text var
        self.userID_label = tk.Label(self, text="Pilot ID")
        self.userID_entry = tk.Entry(self, width=33)

        # self.userName = tk.StringVar(value="E.g John Smith")
        # self.userName_label = tk.Label(self, text="Name")
        # self.userName_entry = tk.Entry(self, width=33)

        # self.userEmail = tk.StringVar(value="E.g abc@xyz.com")
        # self.userEmail_label = tk.Label(self, text="Email")
        # self.userEmail_entry = tk.Entry(self, width=33)

        self.userID_label.place(x = 20,y = 20)
        self.userID_entry.place(x = 100,y = 20)
        # self.userName_label.place(x = 20,y = 60)
        # self.userName_entry.place(x = 100,y = 60)
        # self.userEmail_label.place(x = 20,y = 100)
        # self.userEmail_entry.place(x = 100,y = 100)

        self.output_label = tk.Label(self, text="Default output directory")
        self.output_dir_label = tk.Label(self, text=self.output_dir)
        self.output_button = tk.Button(text="Change", command=self.choose_output)
        self.output_label.place(x = 20, y = 70)
        self.output_dir_label.place(x = 40, y = 100)
        self.output_button.place(x = 330, y = 100)

        self.start_button = tk.Button(text="START RECORDING", command=self.click_start_recording)
        self.stop_button = tk.Button(text="STOP RECORDING", command=self.click_stop_recording, state=tk.DISABLED)
        if machine == "Windows":
            self.start_button.place(x = 85, y = 150)
            self.start_button["bg"] = "green"
            self.start_button["width"] = 15
            self.start_button["height"] = 2
            self.start_button["relief"] = tk.GROOVE
            
            self.stop_button.place(x = 245, y = 150)
            self.stop_button["bg"] = "gray"
            self.stop_button["width"] = 15
            self.stop_button["height"] = 2
            self.stop_button["relief"] = tk.GROOVE

            self.output_button["relief"] = tk.GROOVE

        else:
            self.start_button.place(x = 60, y = 150)
            self.stop_button.place(x = 220, y = 150)            

    def choose_output(self):
        # Choose output directory
        dirname = filedialog.askdirectory(title = "Select a folder")
        disp_text = "... " + dirname[-33:] if len(dirname) >= 37 else dirname

        self.output_dir = dirname.replace(" ", "\\ ")
        self.output_dir_label.configure(text=disp_text)
        self.config["output"] = self.output_dir
        write_config(self.config)

    def control_field(self, enable=True):
        # Disable Entries, Choose output directory when hit Start
        state = tk.NORMAL if enable else tk.DISABLED

        self.userID_entry.configure(state=state)
        # self.userName_entry.configure(state=state)
        # self.userEmail_entry.configure(state=state)
        self.output_button.configure(state=state)
        # self.start_button.configure(state=state)
        # self.stop_button.configure(state=state)

    def gp3_connect(self):
        try:
            self.gp3.connect((self.config["GP3"]["host"], self.config["GP3"]["port"]))
            return True
        except Exception as e:
            return False
    
    def gp3_start_streaming(self):
        self.gp3.send(str.encode('<SET ID="ENABLE_SEND_DATA" STATE="1" />\r\n'))
        self.gp3.send(str.encode('<SET ID="ENABLE_SEND_TIME" STATE="1" />\r\n'))
        self.gp3.send(str.encode('<SET ID="ENABLE_SEND_POG_FIX" STATE="1" />\r\n'))
        self.gp3.send(str.encode('<SET ID="ENABLE_SEND_CURSOR" STATE="1" />\r\n'))
        self.gp3.send(str.encode('<SET ID="ENABLE_SEND_TIME_TICK" STATE="1" />\r\n'))
    
    def gp3_stop_streaming(self):
        self.gp3.send(str.encode('<SET ID="ENABLE_SEND_DATA" STATE="0" />\r\n'))

    def gp3_recv(self):
        # Receive data from socket until empty b" ", put to global Queue
        global gp3_buffer
        try:
            while True:
                raw = self.gp3.recv(4096)
                gp3_buffer.put(raw)
                time.sleep(0.2) # Sleep to get more data
        
        except Exception as e:
            print(e)
            print("Receive data", traceback.print_exc())
        
        print("Finished getting gazepoints")

    def gp3_process_data(self):
        # Pull data from global Queue 
        HEADER = ['TIME', 'TIME_TICK', 'FPOGX', 'FPOGY', 'FPOGV', 'CX', 'CY']
        global gp3_buffer
        with open(os.path.join(self.path, "raw_gazepoints.csv"), "w", encoding="UTF8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(HEADER)
            try:
                while True:
                    batch = gp3_buffer.get(timeout=3.0) # If not getting an item in timeout -> raise error.
                    batch = batch.decode().split('\r\n')
                    for row in batch:
                        if len(row) > 0 and "REC" in row:
                            writer.writerow(parse(row))
            
            except Exception as e:
                print("Process data", e)
                print(traceback.print_exc())

        print("Finish writing file")


    def postprocess(self, path):
        # Make raw folder
        new_path = os.path.join(path, "raw_data")
        os.mkdir(new_path)

        # Convert mkv to mp4 
        input_vid = os.path.join(path, "obs.mkv")
        output_vid = os.path.join(path, "output.mp4")
        cmd = "ffmpeg -i {} -codec copy {}".format(input_vid, output_vid)
        subprocess.run(cmd)

        # Postprocess gazepoints
        gt = pd.read_csv(os.path.join(path, "raw_gazepoints.csv"))
        gt = gt[(gt.TIME_TICK >= int(str(self.first_tick)[:11])) & (gt.TIME_TICK <= int(str(self.last_tick)[:11]))].drop(["TIME_TICK"], axis = 1)
        gt.TIME -= gt.TIME.min()
        gt.to_csv(os.path.join(path, "gazepoints.csv"), index=False, float_format='%.5f')
        
        # Move raw_gazepoints.csv and obs.mkv to raw folder
        shutil.move(os.path.join(path, "raw_gazepoints.csv"), os.path.join(new_path, "raw_gazepoints.csv"))
        shutil.move(os.path.join(path, "obs.mkv"), os.path.join(new_path, "obs.mkv"))
        shutil.move(os.path.join(path, "tick.txt"), os.path.join(new_path, "tick.txt"))


    def check_condition(self):
        mes = []
        # Check OBS connection
        if not self.obs_is_connect:
            out = self.obs.connect()
            if not out:
                mes.append("Open OBS.")
            else:
                self.obs_is_connect = True
            
        # Check GP3 connection
        if not self.gp3_is_connect:
            out = self.gp3_connect()
            if not out:
                mes.append("Open Gazepoint Control")
            else:
                self.gp3_is_connect = True

        # Check User ID (Purdue ID)
        if not self.userID_entry.get():
            mes.append("User ID is empty.")

        # Check folder exist
        path = os.path.join(self.output_dir, self.userID_entry.get())
        if self.userID_entry.get() != "" and os.path.isdir(path):
            mes.append("{} folder exists. Either choose another User ID or different output directory!".format(self.userID_entry.get()))

        return len(mes) == 0, mes

    def click_start_recording(self):
        # Check condition and start OBS, GP3 connections
        out, mes = self.check_condition()
        if not out:
            messagebox.showwarning(title="Warning", message="\n".join(mes))
            self.control_field(True)
            return
    
        # Make new directory based on userID
        self.path = os.path.join(self.output_dir, self.userID_entry.get())
        os.mkdir(self.path)
        out = self.obs.setOutFolder(self.path)
        if not out:
            messagebox.showwarning(title="Warning", message="Can not start recording. Contact SBU team!")
            self.control_field(True)
            return

        # Start GP3 streaming
        self.gp3_start_streaming()
        t1 = Thread(target=self.gp3_recv)
        t2 = Thread(target=self.gp3_process_data)
        t1.start()
        t2.start()
        
        time.sleep(0.5) # Waiting a bit for GP3 to start. Gp3 must start before OBS recording.
        # Start OBS Recording
        out = self.obs.startRecording()
        self.first_tick = time.monotonic_ns()

        if not out:
            messagebox.showwarning(title="Warning", message="Can not start recording. Contact SBU team!")
            self.control_field(True)
            return
        
        # Open Learning Material Website
        webbrowser.open_new_tab(self.config["LearningModule"])

        # Set recording button to disabled 
        self.start_button.configure(state=tk.DISABLED, text="RECORDING", bg="gray")
        self.stop_button.configure(state=tk.NORMAL, bg="red")
        self.userID_entry.configure(state=tk.DISABLED)


    def click_stop_recording(self):
        # Stop OBS Recording
        out = self.obs.stopRecording()
        self.last_tick = time.monotonic_ns()
        if not out:
            messagebox.showwarning(title="Warning", message="Can not stop recording. Do it manually and contact SBU team!")
            self.control_field(True)

        # Disable GP3 send data
        self.gp3_stop_streaming()

        self.control_field(True)
        self.stop_button.configure(state=tk.DISABLED, bg="gray")
        self.start_button.configure(state=tk.NORMAL, text="START RECORDING", bg="green")
        self.userID_entry.configure(state=tk.NORMAL)

        # Save first/last tick to csv file
        with open(os.path.join(self.path, "tick.txt"), "w") as f:
            f.write("{}\n{}".format(self.first_tick, self.last_tick))

        time.sleep(5.0) # Wait for CSV Writer finish the job
        self.postprocess(self.path) # Postprocessing gazepoints.csv and obs.mkv

if __name__ == "__main__":
    machine = platform.system()
    gp3_buffer = Queue()
    app = App(machine)
    app.mainloop()