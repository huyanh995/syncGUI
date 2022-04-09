from obswebsocket import obsws, requests

class OBS():
    def __init__(self, config):
        host, port, password = config["host"], config["port"], config["password"]
        self.obs = obsws(host, port, password)
        self.logger = None

    def set_logger(self, logger):
        self.logger = logger

    def connect(self):
        try:
            self.obs.connect()
            return True
        except Exception as e:
            self.logger.exception("Unexpected exception in OBS_connect.")
            return False


    def setOutFolder(self, path):
        out = self.obs.call(requests.SetRecordingFolder(path))
        if not out.data:
            self.logger.exception("Failed to set output directory in OBS. Path {}, out {}".format(path, out))
            return False
        return True        

    def startRecording(self):
        out = self.obs.call(requests.StartRecording())
        if not out.data:
            self.logger.exception("Failed to start recording. Out {}".format(out))
            return False
        return True

    def stopRecording(self):
        out = self.obs.call(requests.StopRecording())
        if not out.data:
            self.logger.exception("Failed to stop recording. Out {}".format(out))
            return False
        return True
