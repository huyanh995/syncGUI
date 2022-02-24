import subprocess
import sys
import os
import shutil
import numpy as np
import cv2

#from offset_util import getoffset_random,getdim,getOffset
#from coordreg import prepare_dir, Handler
from SyncVid.offset_util import getdim, getOffset
from SyncVid.coordreg import Handler

def delete_dir(dir_name):
    try:
        shutil.rmtree('{}/screen_frames'.format(dir_name), ignore_errors=True) 
        print("Delete screen_frames")
    except Exception:
        # File not found
        pass
    try:
        shutil.rmtree('{}/video_frames'.format(dir_name), ignore_errors=True)
        print("Delete video_frames")
    except Exception:
        pass
    try:
        os.remove('{}/cropped_screen.webm'.format(dir_name))
        print("Delete cropped_screen")
    except Exception:
        pass


def process_vid(webcam, screen):
	#dir_path = os.path.dirname(os.path.abspath(webcam))
    dir_path = os.path.dirname(webcam)
    t_vid = cv2.VideoCapture(screen)
    height = t_vid.get(cv2.CAP_PROP_FRAME_HEIGHT)
    width = t_vid.get(cv2.CAP_PROP_FRAME_WIDTH)
    croph = height*(360/1600)
    cropw = width*(480/2560)

    delete_dir(dir_path)
    os.mkdir('{}/screen_frames'.format(dir_path))
    os.mkdir('{}/video_frames'.format(dir_path))

    cmd = 'ffmpeg -i {} -filter:v "crop={}:{}:0:0" {}/cropped_screen.webm'.format(screen,str(cropw),str(croph), dir_path)
    subprocess.call(cmd, shell=True)

    cropped_screen = dir_path + '/cropped_screen.webm'
    cmd = 'ffmpeg -i {} -vf fps=30 {}/screen_frames/out%d.png'.format(cropped_screen, dir_path)
    subprocess.call(cmd, shell=True)

    cmd = 'ffmpeg -i {} -vf fps=30 {}/video_frames/out%d.png'.format(webcam, dir_path)
    subprocess.call(cmd, shell=True)

    DIR = dir_path+"/video_frames"
    f_vid = len([name for name in os.listdir(DIR) if os.path.isfile(os.path.join(DIR, name))])

    DIR = dir_path+"/screen_frames"
    chk = len([name for name in os.listdir(DIR) if os.path.isfile(os.path.join(DIR, name))])

    # cmd = 'cd ..'
    # subprocess.call(cmd, shell=True)
    chk = dir_path + '/screen_frames/out' + str(chk) + '.png'
    # offset = chk-f_vid
    return f_vid, chk

def NCC(src, dst):
    src = np.array(src)
    dst = np.array(dst)
    # print(src.shape, dst.shape)
    src = src.astype(np.float32)
    dst = dst.astype(np.float32)
    # print(src.shape)
    # print(dst.shape)
    src=  src - np.mean(src)#translate
    dst = dst - np.mean(dst)
    ncc = (np.sum(src * dst))/((np.linalg.norm(src)*(np.linalg.norm(dst)))+1e-12)
    return ncc

def getDMMatrix(handler, path, start, m, diff, flag, dim):
    ret = []
    for i in range(m):
        image_num = start + i * diff
        
        infile = path + '/out' + str(image_num) + '.png'
        # print(infile)
        img = cv2.imread(infile)
        if(flag):
            img = cv2.resize(img, dim, interpolation=cv2.INTER_AREA)
        preds_t = handler.get(img, get_all=True)
        preds_t = np.array(preds_t)
        # print(preds_t.shape)
        # preds_t = preds_t.ravel()
        ret.append(preds_t)
    return ret

def getOffset(handler, path1, path2, start, m, diff): #path2 is smaller images(screen cropped)
    infile = path1 + '/out1.png'
    img = cv2.imread(infile, cv2.cv2.IMREAD_GRAYSCALE)
    width = img.shape[1]
    height = img.shape[0]
    dim = (width, height)

    DMmatrix1 =  getDMMatrix(handler, path2, 1, m, diff, True,  dim)
    for x in range(len(DMmatrix1)):
        print(DMmatrix1[x].shape)
    maxNCC = -1
    bestT = -np.inf
    for t in range(0, start):
        DMmatrix2 = getDMMatrix(handler, path1, start + t, m, diff, False,  dim)
        for x in range(len(DMmatrix1)):
            if DMmatrix1[x] == []:
                DMmatrix2[x] = []
        # print(len(DMmatrix1))
        # print(len(DMmatrix2))
        ncc = NCC(DMmatrix1, DMmatrix2)
        # print(ncc)
        if(ncc > maxNCC):
            # print(start + t, start)
            maxNCC = ncc
            bestT = t
            
    # print(bestT)
    # print(maxNCC)
    return bestT

def ws_sync_call(webcam, screen):
    size_face_vid, size_screen_vid = process_vid(webcam, screen)

    base_name = os.path.basename(webcam)
    dir_name = os.path.dirname(webcam)
    file_name = os.path.splitext(base_name)[0]
    file_ext = os.path.splitext(base_name)[1]
    out_file = "{}/{}_sync{}".format(dir_name, file_name, file_ext)
    model_path = "./SyncVid/models/scrfd_10g_bnkps.onnx"

    #prepare_dir()
    dim = getdim(size_screen_vid)
    handler = Handler('./SyncVid/models/2d106det', 0, model_path, ctx_id=-1, det_size=640)
    Offset = getOffset(handler, dir_name + '/video_frames', dir_name + '/screen_frames', 150, 12 ,3)
    print("predicted Offset:", Offset)

    Offset = 45
    t1 = Offset/30
    t2 = 1494/30
    print(t1,t2)

    cmd = 'ffmpeg -i {} -c:v copy {}'.format(webcam, "webcam.mp4")
    subprocess.call(cmd, shell=True)

    cmd = 'ffmpeg -i {} -ss {} -to {} -c copy {}'.format("webcam.mp4", str(t1), str(t1+t2), out_file)

    subprocess.call(cmd, shell=True)

    delete_dir(dir_name)

    return out_file, "" # For log (add later)