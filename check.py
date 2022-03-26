try:
    import mxnet
    print("mxnet", mxnet.__version__)
except:
    print("Error {}".format("mxnet"))

try:
    import cv2
    print("cv2", cv2.__version__)
except:
    print("Error {}".format("cv2"))

try:
    import librosa
    print("librosa", librosa.__version__)
except:
    print("Error {}".format("librosa"))

try:
    import numpy
    print("numpy", numpy.__version__)
except:
    print("Error {}".format("numpy"))

try:
    import insightface
    print("insightface", insightface.__version__)
except:
    print("Error {}".format("insightface"))