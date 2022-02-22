import tkinter as tk
from tkinter import ttk
from threading import Thread
import subprocess

class Script(Thread):
    def __init__(self):
        super().__init__()

    def run(self):
        for i in range(10**9):
            print(i)
            if i % 10**5 == 0:
                subprocess.call("ls", shell=True)

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.geometry("450x300")
        self.resizable(0, 0)

        self.start = tk.Button(self, text="START", command=self.click)
        self.start.pack()
        self.stop = tk.Button(self, text="STOP", command=self.click_stop)
        self.stop.pack()

        self.pbar = ttk.Progressbar(self, orient=tk.HORIZONTAL, length=410, mode='indeterminate')
        self.pbar.pack(side=tk.TOP)

    def click(self):
        self.click_start()
        thread = Script()
        thread.start()
        self.monitor(thread)

    def click_start(self):
        self.pbar.start(20)

    def click_stop(self):
        self.pbar.stop()

    def monitor(self, thread):
        if thread.is_alive():
            self.after(100, lambda: self.monitor(thread))
        else:
            self.stop_sync()

if __name__ == "__main__":
    app = App()
    app.mainloop()
    