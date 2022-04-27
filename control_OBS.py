from datetime import datetime
from obswebsocket import obsws, requests
import time

class OBS():
    def __init__(self, config):
        host, port, password = config["host"], config["port"], config["password"]
        self.ws = obsws(host, port, password)
        self.logger = None

    def set_logger(self, logger):
        self.logger = logger

    def connect(self):
        try:
            self.ws.connect()
            return True
        except Exception as e:
            self.logger.exception("Unexpected exception in OBS_connect.")
            return False

    def getCurrentFps(self):
        out = self.ws.call(requests.GetVideoInfo())
        if not out.status:
            self.logger.exception("Failed to get video info.")
            return False, -1
        return True, out.getFps()

    def setOutFolder(self, path):
        out = self.ws.call(requests.SetRecordingFolder(path))
        if not out.status:
            self.logger.exception("Failed to set output directory in OBS. Path {}, out {}".format(path, out))
            return False
        return True        

    def startRecording(self):
        out = self.ws.call(requests.StartRecording())
        start = time.monotonic_ns()
        start_time = datetime.now()
        if not out.status:
            self.logger.exception("Failed to start recording. Out {}".format(out))
            return False, None, None
        return True, start, start_time

    def stopRecording(self):
        out = self.ws.call(requests.StopRecording())
        end = time.monotonic_ns()
        stop_time = datetime.now()
        if not out.status:
            self.logger.exception("Failed to stop recording. Out {}".format(out))
            return False, None, None
        return True, end, stop_time

if __name__ == "__main__":
    # DEBUG
    host = "localhost"
    port = 4444
    password = "sbu"

    ws = obsws(host, port, password)
    ws.connect()
    print(ws.call(requests.GetVideoInfo()).getFps())