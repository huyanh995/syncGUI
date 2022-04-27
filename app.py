import os
import shutil
import time
import subprocess
from collections import deque
import logging
import tkinter as tk
from tkinter import filedialog, messagebox
from queue import Queue, Empty
import csv
from threading import Thread
import traceback
from datetime import datetime

import platform
import socket
import webbrowser
import pandas as pd
import yaml

from utils import read_config, write_config, parse
from control_OBS import OBS

class AnnotationWindow(tk.Toplevel):
    def __init__(self, master, path):
        super().__init__(master = master)
        self.path = path # Store current pilot ID path
        self.title("Experiment Launcher")
        self.geometry("450x200") 
        self.length_label = tk.Label(text="Choose min clips length (ms)")
        self.length_label.place(x = 20, y = 20)

        self.scale = tk.Scale(from_ = 50, to = 10000, resolution = 50, orient = tk.HORIZONTAL, length = 400, command=self.calculate_number_clips)
        self.scale.set(2000)

        self.scale.place(x = 25, y = 45)

        self.result_label = tk.Label(text = "Number of clips: ")
        self.result_label.place(x = 20, y = 100)

        self.result = tk.Label(text = "-1")
        self.result.place(x = 140, y = 100)

        self.create_playlist_button = tk.Button(text = "CREATE PLAYLIST", command = self.create_playlist_button)
        self.create_mindwander_button = tk.Button(text = "MIND WANDERING", command = self.create_mindwander_button)

        machine = platform.system()
        if machine == "Windows":
            self.create_playlist_button.place(x = 85, y = 140)
            self.create_playlist_button["width"] = 15
            self.create_playlist_button["height"] = 2
            self.create_playlist_button["relief"] = tk.GROOVE
            
            self.create_mindwander_button.place(x = 245, y = 140)
            self.create_mindwander_button["width"] = 15
            self.create_mindwander_button["height"] = 2
            self.create_mindwander_button["relief"] = tk.GROOVE

        else:
            self.create_playlist_button.place(x = 60, y = 135)
            self.create_mindwander_button.place(x = 220, y = 135) 


    # For Yifeng
    def create_mindwand_playlist(self):
        # To get current value of scaler
        clip_len = self.scale.get()
        pass

    def create_playlist(self):
        clip_len = self.scale.get()
        pass

    def calculate_number_clips(self, scale_var):

        self.result.configure(text = int(scale_var) / 50)


class App(tk.Tk):
    def __init__(self, machine):
        super().__init__()
        self.config = read_config("config.yml")
        self.path = None
        self.calibration_results = deque(maxlen=500)

        # Logging system
        self.logger = None # For logging, init when  recording.

        # OBS Init
        self.obs = OBS(self.config["OBS"])
        self.first_tick = None
        self.start_time = None
        self.last_tick = None
        self.stop_time = None
        self.obs_is_connect = False

        # GP3 threading variable
        self.gp3 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.gp3.settimeout(2.0)
        self.gp3_is_connect = False # Each socket only have to connect once
        
        # Geometry
        self.title("Experiment Launcher")
        self.geometry("450x260") 
        # self.geometry("450x400") 
        self.resizable(False, False) 
        self.eval('tk::PlaceWindow . center')
        self.machine = machine
        self.iconbitmap('icon.ico') if machine == "Windows" else None

        if not self.config["output"]:
            self.output_dir = os.path.join(os.environ['USERPROFILE'], 'Documents') if machine == "Windows" else "~/"
        else:
            self.output_dir = self.config["output"]

        # Label
        self.userID_label = tk.Label(self, text="Pilot ID")
        self.userID_entry = tk.Entry(self, width=33)

        self.userID_label.place(x = 20,y = 20)
        self.userID_entry.place(x = 100,y = 20)

        self.is_calibration = tk.BooleanVar()
        self.is_calibration.set(self.config["calibration"])
        self.calibration_checkbutton = tk.Checkbutton(self, text = "Force calibration", variable = self.is_calibration, onvalue = True, offvalue = False)
        self.calibration_checkbutton.place(x = 20, y = 65)
        # self.calibrate_button = tk.Button(text="Calibrate", width = 6, command=self.start_calibration)
        # self.calibrate_button.place(x = 320, y = 65)

        # self.is_precise_matching = tk.BooleanVar()
        # self.is_precise_matching.set(self.config["preciseMatching"])
        # self.precise_matching_button = tk.Checkbutton(self, text = "Precise matching (for SBU team)", variable = self.is_precise_matching,onvalue = True, offvalue = False)
        # self.precise_matching_button.place(x = 20, y = 90)

        

        self.output_label = tk.Label(self, text="Default output directory")
        self.output_dir_label = tk.Label(self, text=self.output_dir)
        self.output_button = tk.Button(text="Change", width = 6, command=self.choose_output)
        self.output_label.place(x = 20, y = 120)
        self.output_dir_label.place(x = 40, y = 150)
        self.output_button.place(x = 320, y = 150)

        self.start_button = tk.Button(text="START RECORDING", command=self.click_start_recording)
        self.stop_button = tk.Button(text="STOP RECORDING", command=self.click_stop_recording, state=tk.DISABLED)
        if machine == "Windows":
            self.start_button.place(x = 85, y = 200)
            self.start_button["bg"] = "green"
            self.start_button["width"] = 15
            self.start_button["height"] = 2
            self.start_button["relief"] = tk.GROOVE
            
            self.stop_button.place(x = 245, y = 200)
            self.stop_button["bg"] = "gray"
            self.stop_button["width"] = 15
            self.stop_button["height"] = 2
            self.stop_button["relief"] = tk.GROOVE

            self.output_button["relief"] = tk.GROOVE
        else:
            self.start_button.place(x = 60, y = 200)
            self.stop_button.place(x = 220, y = 200)  

    def create_logger(self):
        # Config logger
        formatter = logging.Formatter("%(asctime)s:%(levelname)s:%(funcName)s:%(message)s")
        log_file = os.path.join(self.path, '{}.log'.format(datetime.now().strftime("%Y_%m_%d-%I_%M_%S_%p")))
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)

        # Setup and assign logger to class
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(file_handler)

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
        self.output_button.configure(state=state)

    def start_calibration(self, recalibrate=False):
        # Start calibration
        # If calibration fails -> show a messagebox to do it again
        # If yes, do it again
        
        # Clear calibration result
        self.gp3.send(str.encode('<GET ID="CALIBRATE_CLEAR" />\r\n'))
        # Show calibration screen
        self.gp3.send(str.encode('<GET ID="CALIBRATE_SHOW" />\r\n'))
        # During calibration, server will send <CAL tag 
        # Catch it until there is no <CAL tag in the stream
        self.gp3.send(str.encode('GET ID="CALIBRATE_RESULT_SUMMARY" />\r\n'))
        # Hide the calibration window
        self.gp3.send(str.encode('<SET ID="ENABLE_SEND_DATA" STATE="1" />\r\n'))
        # Get the summary result <ACK tag
        self.gp3.send(str.encode('GET ID="CALIBRATE_RESULT_SUMMARY" />\r\n'))

        result = None
        avg_error = None
        # Add to log
        self.logger.info("CALIBRATION: Result {}. Average Error {}.".format(result, avg_error))
        # Message box shows the result
        # If pass 4/5 points -> Info box with Okay button, function returns True
        # Else: Warning box with Yes/No question to retry. If yes -> Call start_calibration again, else returns False
        if result < 4:
            # Show Retry Cancel box
            message = "{}/5 points passed. Average error {}.\nDo you want to redo the calibration?".format(result, avg_error)
            answer = messagebox.askretrycancel(title="Calibration", message = message)
            if answer:
                self.start_calibration()
            else:
                return False
        else:
            # Show Info box
            message = "{}/5 points passed. Average error {}.".format(result, avg_error)
            messagebox.showinfo(title="Calibration", message = message)
            return True
        
    def check_fps(self):
        pass

    def gp3_connect(self):
        try:
            self.gp3.connect((self.config["GP3"]["host"], self.config["GP3"]["port"]))
            return True
        except TimeoutError as e:
            self.logger.warning("Timeout when connecting to GP3")
            return False
        except Exception as e:
            # If any unexpected exceptions raised
            self.logger.exception("Unexpected exception in gp3_connect")
            return False
    
    def gp3_start_streaming(self):
        self.gp3.send(str.encode('<SET ID="ENABLE_SEND_DATA" STATE="1" />\r\n'))
        self.gp3.send(str.encode('<SET ID="ENABLE_SEND_COUNTER" STATE="1" />\r\n'))
        self.gp3.send(str.encode('<SET ID="ENABLE_SEND_TIME" STATE="1" />\r\n'))
        self.gp3.send(str.encode('<SET ID="ENABLE_SEND_TIME_TICK" STATE="1" />\r\n'))
        self.gp3.send(str.encode('<SET ID="ENABLE_SEND_POG_FIX" STATE="1" />\r\n'))
        self.gp3.send(str.encode('<SET ID="ENABLE_SEND_POG_LEFT" STATE="1" />\r\n'))
        self.gp3.send(str.encode('<SET ID="ENABLE_SEND_POG_RIGHT" STATE="1" />\r\n'))
        self.gp3.send(str.encode('<SET ID="ENABLE_SEND_POG_BEST" STATE="1" />\r\n'))
        self.gp3.send(str.encode('<SET ID="ENABLE_SEND_PUPIL_LEFT" STATE="1" />\r\n'))
        self.gp3.send(str.encode('<SET ID="ENABLE_SEND_PUPIL_RIGHT" STATE="1" />\r\n'))
        self.gp3.send(str.encode('<SET ID="ENABLE_SEND_EYE_LEFT" STATE="1" />\r\n'))
        self.gp3.send(str.encode('<SET ID="ENABLE_SEND_EYE_RIGHT" STATE="1" />\r\n'))
        self.gp3.send(str.encode('<SET ID="ENABLE_SEND_CURSOR" STATE="1" />\r\n'))

    
    def gp3_stop_streaming(self):
        self.gp3.send(str.encode('<SET ID="ENABLE_SEND_DATA" STATE="0" />\r\n'))

    def gp3_recv(self):
        # Receive data from socket until empty b" ", put to global Queue
        global gp3_buffer
        try:
            while True:
                raw = self.gp3.recv(4096)
                gp3_buffer.put(raw)
                time.sleep(0.2) # Sleep to wait more data
        
        except socket.timeout as e:
            self.logger.info("Finished getting gazepoints")

        except Exception as e:
            self.log.exception("Unexpected exception in gp3_stop_streaming")


    def gp3_process_data(self):
        # Pull data from global Queue 
        # HEADER = ['TIME', 'TIME_TICK', 'FPOGX', 'FPOGY', 'FPOGV', 'CX', 'CY']
        HEADER = ['TIME', 'TIME_TICK', 'FPOGX', 'FPOGY', 'FPOGV', 'CX', 'CY']
        global gp3_buffer
        with open(os.path.join(self.path, "raw_gazepoints.csv"), "w", encoding="UTF8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(HEADER)
            try:
                while True:
                    batch = gp3_buffer.get(timeout=1.5) # If not getting an item in timeout -> raise error.
                    batch = batch.decode().split('\r\n')
                    for row in batch:
                        if len(row) > 0 and "REC" in row:
                            # TODO: [] modify parse function
                            writer.writerow(parse(row))
            
            except Empty as e:
                self.logger.info("Finished writing file")

            except Exception as e:
                self.logger.exception("Unexpected exception in gp3_process_data")


    def postprocess(self, path):
        # Make raw folder
        new_path = os.path.join(path, "raw_data")
        os.mkdir(new_path)
        self.logger.info("Done making raw_data directory.")

        # Convert mkv to mp4 
        input_vid = os.path.join(path, "obs.mkv")
        output_vid = os.path.join(path, "output.mp4")
        cmd = "ffmpeg -i {} -codec copy {}".format(input_vid, output_vid)
        subprocess.run(cmd)
        self.logger.info("Done convert to mp4. Cmd {}".format(cmd))

        # Postprocess gazepoints
        gt = pd.read_csv(os.path.join(path, "raw_gazepoints.csv"))
        gt = gt[(gt.TIME_TICK >= self.first_tick/100) & (gt.TIME_TICK <= self.last_tick/100)].drop(["TIME_TICK"], axis = 1)
        gt.TIME -= gt.TIME.min()
        gt.to_csv(os.path.join(path, "gazepoints.csv"), index=False, float_format='%.5f')
        self.logger.info("Done post processing gazepoints csv file, start tick {}, end tick {}".format(self.first_tick/100, self.last_tick/100))
        
        # Move raw_gazepoints.csv and obs.mkv to raw folder
        shutil.move(os.path.join(path, "raw_gazepoints.csv"), os.path.join(new_path, "raw_gazepoints.csv"))
        shutil.move(os.path.join(path, "obs.mkv"), os.path.join(new_path, "obs.mkv"))
        shutil.move(os.path.join(path, "tick.yml"), os.path.join(new_path, "tick.yml"))


    def check_condition(self):
        mes = []
        # Check OBS connection
        if not self.obs_is_connect:
            out = self.obs.connect()
            if not out:
                mes.append("Open OBS.")
            else:
                self.obs_is_connect = True
        
        # Check Precise Matching
        if self.is_precise_matching.get():
            status, fps = self.obs.getCurrentFps()
            if fps != 61:
                mes.append("Set OBS output video to 61fps to enable precise matching!")
                self.is_precise_matching.set(False)

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
        # Write is_calibration, precise_matching to config file for later uses
        self.config["calibration"] = self.is_calibration.get()
        # self.config["preciseMatching"] = self.is_precise_matching.get()
        write_config(self.config)

        # Check condition and start OBS, GP3 connections
        out, mes = self.check_condition()
        if not out:
            messagebox.showwarning(title="Warning", message="\n".join(mes))
            self.control_field(True)
            return
    
        # Make new directory based on userID
        self.path = os.path.join(self.output_dir, self.userID_entry.get())
        os.mkdir(self.path)

        # Create logger
        self.create_logger()
        self.obs.set_logger(self.logger)

        # Config OBS output to pilot ID path
        out = self.obs.setOutFolder(self.path)
        if not out:
            messagebox.showwarning(title="Warning", message="Can not create pilot folder. Contact SBU team!")
            self.control_field(True)
            return

        # Start GP3 streaming
        self.gp3_start_streaming()
        t1 = Thread(target=self.gp3_recv)
        t2 = Thread(target=self.gp3_process_data)
        t1.start()
        t2.start()
        
        # Set recording button to disabled 
        self.start_button.configure(state=tk.DISABLED, text="RECORDING", bg="gray")
        self.stop_button.configure(state=tk.NORMAL, bg="red")
        self.userID_entry.configure(state=tk.DISABLED)

        #time.sleep(2.0) # Waiting a bit for GP3 to start. Gp3 must start before OBS recording.
        self.after(5000) # 10s
        # Start OBS Recording
        out, first_tick, start_time = self.obs.startRecording()
        #self.first_tick = time.monotonic_ns()

        if not out:
            messagebox.showwarning(title="Warning", message="Can not start recording. Contact SBU team!")
            self.control_field(True)
            return
        
        self.first_tick = first_tick
        self.start_time = start_time
        
        # Open Learning Material Website
        #webbrowser.open_new_tab(self.config["LearningModule"])


    def click_stop_recording(self):
        
        # Stop OBS Recording
        out, last_tick, stop_time = self.obs.stopRecording()
        self.last_tick = last_tick
        self.stop_time = stop_time
        if not out:
            messagebox.showwarning(title="Warning", message="Can not stop recording. Do it manually and contact SBU team!")
            self.control_field(True)

        #time.sleep(2.0) # Wait awhile before stop GP3.
        self.after(2000)

        # Disable GP3 send data
        self.gp3_stop_streaming()

        self.control_field(True)
        self.stop_button.configure(state=tk.DISABLED, bg="gray")
        self.start_button.configure(state=tk.NORMAL, text="START RECORDING", bg="green")
        self.userID_entry.configure(state=tk.NORMAL)

        # Save first/last tick to csv file
        with open(os.path.join(self.path, "tick.yml"), "w") as f:
            time_data = {"CPUTick": {"Start": self.first_tick, "Stop": self.last_tick}, 
                        "SysTime": {"Start": self.start_time, "Stop": self.stop_time}}
            #f.write("{}\n{}".format(self.first_tick, self.last_tick))
            output = yaml.dump(time_data, f)

        #time.sleep(5) # Wait for CSV Writer finish the job
        self.after(5000)

        self.postprocess(self.path) # Postprocessing gazepoints.csv and obs.mkv

        # Open Postprocessing tool
        AnnotationWindow(self, self.path)

        self.logger = None # Avoid uncontrolled log

if __name__ == "__main__":
    machine = platform.system()
    gp3_buffer = Queue()
    app = App(machine)
    app.mainloop()
