import os
import subprocess
from config import DefaultConfig

# Make all the Videos to the same w:h ration
print('video resizing...')
subprocess.call('ffmpeg -i Final_syn_webcam.mp4 -vf scale=480:480 webcam_small.mp4 ', shell=True)
subprocess.call('ffmpeg -i Final_syn_screen.mp4 -vf scale=480:480 screen_small.mp4 ', shell=True)
subprocess.call('ffmpeg -i Final_syn_egocentric.mp4 -vf scale=800:960 ego_centric_small.mp4 ', shell=True)
print('video resizing complete')

# Merge all the videos together
print('merging videos...')
subprocess.call(
    'ffmpeg -i screen_small.mp4 -i webcam_small.mp4 -i ego_centric_small.mp4 -filter_complex "[0:v][1:v]vstack=inputs=2[left]; [left][2:v]hstack=inputs=2[v]" -map "[v]" -r 30.00 -c:v libx264 -crf 23 -preset veryfast initial_output.mp4',
    shell=True)
print('merging videos complete')

# Separate all the places where subject is looking outside the screen
config = DefaultConfig()
subprocess.call('mkdir temp', shell=True)
i = 1
for time_stamp in config.timestamps:
    start = time_stamp[0]
    end = time_stamp[1]

    file = " ./temp/temp_{0}.mp4".format(str(i).zfill(3))
    subprocess.call('ffmpeg -ss ' + str(start) + ' -i initial_output.mp4 -c copy -t ' + str(end - start) + file,
                    shell=True)
    i += 1

os.chdir('./temp')
a = open("videos.txt", "a")
for path, _, files in os.walk(r'./'):
    for filename in files:
        f = os.path.join(path, filename)
        if f.split(".")[-1] == "mp4":
            a.write("file '" + str(f.split("/")[1]) + "'" + '\n')
a.close()
subprocess.call(
    'ffmpeg -safe 0 -f concat -segment_time_metadata 1 -i videos.txt -vf select=concatdec_select -af aselect=concatdec_select,aresample=async=1 final_output.mp4',
    shell=True)

# Remove temporary files and cleanup
subprocess.call('move final_output.mp4 ../final_output.mp4', shell=True)
os.chdir('../')
subprocess.call('del screen_small.mp4', shell=True)
subprocess.call('del ego_centric_small.mp4', shell=True)
subprocess.call('del webcam_small.mp4', shell=True)
subprocess.call('rmdir /s temp', shell=True)
