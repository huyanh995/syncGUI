import cv2
egocentric_path = "./Fps/ego_centric.mp4"
webcam_path = "./Fps/webcam.mp4"
screen_path = "./Fps/screen.avi"

ego_cap = cv2.VideoCapture(egocentric_path)
print('ego', ego_cap.get(cv2.CAP_PROP_FPS))

webcam_cap = cv2.VideoCapture(webcam_path)
print('webcam', webcam_cap.get(cv2.CAP_PROP_FPS))

screen_cap = cv2.VideoCapture(screen_path)
print('screen', screen_cap.get(cv2.CAP_PROP_FPS))