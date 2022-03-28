from obswebsocket import obsws, requests

class OBS():
    def __init__(self, config):
        host, port, password = config["host"], config["port"], config["password"]
        self.obs = obsws(host, port, password)

    def connect(self):
        try:
            self.obs.connect()
            return True
        except Exception as e:
            print(e)
            return False


    def setOutFolder(self, path):
        out = self.obs.call(requests.SetRecordingFolder(path))
        if not out.data:
            print(out)
            print(path)
            return False
        return True        

    def startRecording(self):
        out = self.obs.call(requests.StartRecording())
        if not out.data:
            print(out)
            return False
        return True

    def stopRecording(self):
        out = self.obs.call(requests.StopRecording())
        if not out.data:
            print(out)
            return False
        return True
