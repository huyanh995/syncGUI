import subprocess
import os
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats

def process_vid(video_rec,screen_rec):
	dir_path = os.path.dirname(os.path.abspath(video_rec))
	print(dir_path)

	cmd = 'rm -r {}/screen_frames'.format(dir_path)
	subprocess.call(cmd, shell=True)
	cmd = 'rm -r {}/video_frames'.format(dir_path)
	subprocess.call(cmd, shell=True)
	cmd = 'rm {}/cropped_screen.webm'.format(dir_path)
	subprocess.call(cmd, shell=True)

	cmd = 'mkdir {}/screen_frames'.format(dir_path)
	subprocess.call(cmd, shell=True)

	cmd = 'mkdir {}/video_frames'.format(dir_path)
	subprocess.call(cmd, shell=True)

	cmd = 'ffmpeg -i {} -filter:v "crop=317:238:2:3" {}/cropped_screen.webm'.format(screen_rec, dir_path)
	subprocess.call(cmd, shell=True)

	cropped_screen = dir_path + '/cropped_screen.webm'
	cmd = 'ffmpeg -i {} -vf fps=30 {}/screen_frames/out%d.png'.format(cropped_screen, dir_path)
	subprocess.call(cmd, shell=True)

	cmd = 'ffmpeg -i {} -vf fps=30 {}/video_frames/out%d.png'.format(video_rec, dir_path)
	subprocess.call(cmd, shell=True)

	DIR = dir_path+"/video_frames"
	f_vid = len([name for name in os.listdir(DIR) if os.path.isfile(os.path.join(DIR, name))])

	DIR = dir_path+"/screen_frames"
	chk = len([name for name in os.listdir(DIR) if os.path.isfile(os.path.join(DIR, name))])

	cmd = 'cd ..'
	subprocess.call(cmd, shell=True)

	offset = chk-f_vid
	return f_vid, chk