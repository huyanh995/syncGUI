from utils import read_config
from wp_sync import wp_sync_call

config = read_config('config.json')
print(config)

file1 = './data/webcam.mp4'
file2 = './data/screen.avi'

max_offset = config["config"]["wp"]["max_offset"]
trim = config["config"]["wp"]["trim"]
wp_sync_call(file1, file2, max_offset, trim)