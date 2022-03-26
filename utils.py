"""
Helper functions
"""
import json
import os
import cv2
import subprocess
from cv2 import split
import ffmpeg

def read_config(json_file):
    with open(json_file, "r") as f:
        config = json.load(f)

    return config

def split_path(path):
    base_name = os.path.basename(path)
    dir_name = os.path.dirname(path)
    file_name, ext = os.path.splitext(base_name)

    return dir_name, file_name, ext

def get_video_info(video_path):
    cap = cv2.VideoCapture(video_path)
    frame_num = cap.get(7)
    fps = cap.get(5)
    WIDTH = cap.get(3)
    HEIGHT = cap.get(4)

    return cap, frame_num, WIDTH, HEIGHT

def convert_to_30fps(video_path):
    #Have to make all videos/audio/csv the same path
    dir_name, file_name, ext = split_path(video_path)
    new_file_name = file_name + "_30fps" + ext
    output_path = os.path.join(dir_name, new_file_name)
    
    cmd = 'ffmpeg -y -i {} -qscale 0 -r 30 -y {}'.format(video_path, output_path)
    subprocess.call(cmd, shell=True)

    return output_path

def combine_audio_video(video_path, audio_path):
    #Assert the same name
    output_path = video_path.replace(".avi", ".mp4")

    cmd = 'ffmpeg -y -i {} -i {} -c:v copy -c:a aac {}'.format(video_path, audio_path, output_path)
    subprocess.call(cmd, shell=True)

    return output_path

def recover_GP3_webcam(screen_audio, gp3webcam_vid):
    """
    Recover fps of raw data from GP3 tracker.
    """
    cap = cv2.VideoCapture(gp3webcam_vid)
    gpe_webcam_frames_num = cap.get(7)
    time = get_duration(screen_audio)
    new_fps = gpe_webcam_frames_num / time

    dir_name, file_name, ext = split_path(gp3webcam_vid)
    new_gp3webcam_path = os.path.join(dir_name, "re_" + file_name + ext)
    print("DEBUG >>>>>", new_gp3webcam_path)
    print(new_fps)
    cmd = 'ffmpeg -y -i {} -filter:v "setpts=PTS/{},fps={}" {}'.format(gp3webcam_vid,
                                                                    new_fps / 10,
                                                                    new_fps,
                                                                    new_gp3webcam_path)

    subprocess.call(cmd, shell=True)

    return new_gp3webcam_path

def get_duration(path):
    probe = ffmpeg.probe(path)
    format = probe['format']
    duration = float(format['duration'])

    return duration

def video_align(video, audio):
    dir_name, file_name, ext = split_path(video)
    output_path = os.path.join(dir_name, "align_" + file_name + ext)

    video_duration = get_duration(video)
    audio_duration = get_duration(audio)
    speed = video_duration / audio_duration

    cmd = 'ffmpeg -y -i {} -filter:v "setpts=PTS/{}" {}'.format(video, speed, output_path)
    subprocess.call(cmd, shell=True)

    return output_path

def save_first_last_frame(video):
    #Used to verify the time of the video
    cap = cv2.VideoCapture(video)
    numframes = int(cap.get(7))
    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
    _, frame = cap.read()
    cv2.imwrite('First.jpg', frame)
    cap.set(cv2.CAP_PROP_POS_FRAMES, numframes - 1)
    _, frame = cap.read()
    cv2.imwrite('Last.jpg', frame)


'''
screen_path = 'screen.avi'
audio_path = 'screen.mp3'
webcam_path = 'webcam.avi'
get_video_info(screen_path)
get_video_info(webcam_path)
recover_GP3_webcam(screen_path, webcam_path)
new_webcam_path = 're_webcam.avi'
combine_audio_video(screen_path, audio_path)
combine_audio_video(new_webcam_path, audio_path)
new_webcam_path = 're_webcam.mp4'
new_screen_path = 'screen.mp4'
convert_to_30fps(new_webcam_path)
convert_to_30fps(new_screen_path)
#new_video = 'rwebcam.mp4'
#convert_to_30fps(new_video)

screenvid = 'screen.avi'
webcamvid = 'webcam.avi'
oriwebcamvid = 'rwebcam.avi'
recover_GP3_webcam(screenvid, webcamvid)
NEW_FPS = 13.184357541899443
cmd = 'ffmpeg -i {} -filter:v "setpts=PTS/{},fps={}" {}'.format(webcamvid, NEW_FPS / 10, NEW_FPS,  oriwebcamvid)
#subprocess.call(cmd)
get_video_info(webcamvid)
get_video_info(oriwebcamvid)
'''
