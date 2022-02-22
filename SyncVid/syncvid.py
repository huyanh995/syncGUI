# import coordreg
from FramePrepare import process_vid
import argparse
from offset_util import getoffset_random,getdim
from coordreg import prepare_dir, Handler

parser = argparse.ArgumentParser(description='Synchronize Video in the wild')
# general
parser.add_argument('--ctx', default=0, type=int, help='ctx id, <0 means using cpu')
parser.add_argument('--det-size', default=640, type=int, help='detection size')
parser.add_argument('--ref-vid', default='vid_rec.webm', type=str, help='small video')
parser.add_argument('--subject-vid', default='screen_rec.webm', type=str, help='big video')
args = parser.parse_args()

size_ref, size_sub = process_vid(args.ref_vid, args.subject_vid)


print(size_ref, size_sub)
print("Frame Difference",size_sub-size_ref)

prepare_dir()
dim = getdim(size_sub)
handler = Handler('/root/.insightface/models/2d106det', 0, ctx_id=0, det_size=640)
Offset = getoffset_random(handler, frame_count = 20,f_vid = size_ref,chk =size_sub,  dim = dim)
print("predicted Offset:", Offset)