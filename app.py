import os
import shutil
import time
import webbrowser
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import platform
import socket
from queue import Queue
import csv
from threading import Thread

from utils import read_config, write_config, parse
from control_OBS import OBS

from numpy import disp

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

        # Geometry
        self.title("SBU Launcher")
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
            self.start_button.place(x = 60, y = 150)
            self.start_button["bg"] = "green"
            self.start_button["width"] = 12
            self.start_button["height"] = 2
            self.start_button["relief"] = tk.GROOVE
            
            self.stop_button.place(x = 220, y = 150)
            self.stop_button["bg"] = "red"
            self.stop_button["width"] = 12
            self.stop_button["height"] = 2
            self.stop_button["relief"] = tk.GROOVE

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
                gp3_buffer.append(raw)
                time.sleep(0.2) # Sleep to get more data
        
        except Exception as e:
            print(e)
        
        print("Finished getting gazepoints")

    def gp3_process_data(self):
        # Pull data from global Queue 
        HEADER = ['TIME', 'TIME_TICK', 'FPOGX', 'FPOGY', 'FPOGV', 'CX', 'CY']
        global gp3_buffer
        with open("gazepoints.csv", "w", encoding="UTF8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(HEADER)
        try:
            while True:
                batch = gp3_buffer.get()
                batch = batch.decode().split('\r\n')
                for row in batch:
                    if len(row) > 0 and "REC" in row:
                        writer.writerow(parse(row))
        
        except Exception as e:
            print(e)

        print("Finish writing file")

    def check_condition(self):
        mes = []
        # Check OBS connection
        out = self.obs.connect()
        if not out:
            mes.append("Open OBS.")
            
        # Check GP3 connection
        out = self.gp3_connect()
        if not out:
            mes.append("Open Gazepoint Control")

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
        path = os.path.join(self.output_dir, self.userID_entry.get())
        os.mkdir(path)
        out = self.OBS.setOutFolder(path)
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
        self.start_button.configure(state=tk.DISABLED, text="RECORDING")
        self.stop_button.configure(state=tk.NORMAL)

    def click_stop_recording(self):
        # Stop OBS Recording
        out = self.OBS.stopRecording()
        self.last_tick = time.monotonic_ns()
        if not out:
            messagebox.showwarning(title="Warning", message="Can not stop recording. Do it manually and contact SBU team!")
            self.control_field(True)

        # Disable GP3 send data
        self.gp3_stop_streaming()

        # Pull data until end

        # Save gazepoints into csv file

        # Save first/last tick to csv file
        with open("tick.txt", "w") as f:
            f.write(self.first_tick + "\n" + self.last_tick)

        self.control_field(True)
        self.stop_button.configure(state=tk.DISABLED)
        self.start_button.configure(state=tk.NORMAL, text="START RECORDING")

    def monitor(self, threads):
        pass

if __name__ == "__main__":
    machine = platform.system()
    gp3_buffer = Queue()
    app = App(machine)
    app.mainloop()