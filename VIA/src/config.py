import pandas as pd

csv = pd.read_csv('./gazepoints.csv')
csv = csv.to_numpy()
time_stamps = []

start = 0
i = 0
while i < len(csv):
    if csv[i][1] < 0 or csv[i][2] < 0:
        start = int(csv[i][0])
        while (csv[i][1] < 0 or csv[i][2] < 0) and i < len(csv):
            i += 1
        if csv[i][0] - start > 1:
            time_stamps.append([start, int(csv[i][0])])
    else:
        i += 1


class DefaultConfig(object):
    screen = True
    face = True
    ergo_centric_view = True
    blank_screen = True

    timestamps = time_stamps
    transition_duration = 2

    __instance = None

    # Make this a singleton class
    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
            cls.__immutable = True
        return cls.__instance
