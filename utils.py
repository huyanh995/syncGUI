import lxml.etree
import yaml
import os
import subprocess
from typing import List

def split_path(path):
    base_name = os.path.basename(path)
    dir_name = os.path.dirname(path)
    file_name, ext = os.path.splitext(base_name)

    return dir_name, file_name, ext

# Split OBS video into 3 videos using ffmpeg
def split_obs_video(path: str) -> List[str]:
    # Top left -> Screen
    # Top right -> webcam
    # Bottom left -> egocentric
    # Bottom right -> Blank
    # Expect a 4K video of 3 FullHD streams at 30fps
    dir_name, _, _ = split_path(path)

    crop_cmd = "[0]crop=w=1920:h=1080:x={}:y={}[{}]"
    crop_cmds = [crop_cmd.format(0, 0, "topleft"),
                crop_cmd.format(1920, 0, "topright"),
                crop_cmd.format(0, 1080, "bottomleft")]
    split_cmd = 'ffmpeg -y -i {} -filter_complex "{}" '.format(path, ";".join(crop_cmds))
    print("DEBUG", split_cmd)

    screen = os.path.join(dir_name, "screen.mp4")
    webcam = os.path.join(dir_name, "webcam.mp4")
    ego = os.path.join(dir_name, "egocentric.mp4")
    map_cmd = '-threads 5 -preset ultrafast -map "[topleft]" {} -map "[topright]" {} -map "[bottomleft]" {}'.format(screen, webcam, ego)
    print("DEBUG", map_cmd)

    cmd = split_cmd + map_cmd
    print("DEBUG", cmd)

    subprocess.call(cmd, shell=True)


# Fuse with audio
def merge_audio(video: str, audio: str) -> str: 

    pass

# Process GP3 data based on CPU ticks
def process_gaze(csv_file: str, tick_file: str) -> str:

    pass

def parse(row, rmv_list = ['FPOGS', 'FPOGD', 'FPOGID', 'CS']):
    row = lxml.etree.fromstring(row)
    tag, attrib = row.tag, row.attrib
    if tag == "REC":
        for key in rmv_list:
            try:
                attrib.pop(key)
            except:
                pass
    
    return attrib.values()

def read_config(path):
    with open(path, "r") as f:
        config = yaml.load(f, Loader=yaml.FullLoader)
    
    return config

def write_config(data, path="config.yml"):
    with open(path, "w") as f:
        output = yaml.dump(data, f)

if __name__ == "__main__":
    config = {"output": None, 
            "OBS": {"host": "localhost", "port": 4444, "password": "sbu"},
            "GP3": {"host": "localhost", "port": 4242},
            "LearningModule": "127.0.0.1:8000"
            }

    write_config(config)
    # split_obs_video("obs.mp4")
