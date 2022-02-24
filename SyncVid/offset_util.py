import cv2
import numpy as np

def ssd(A,B):
  A = np.array(A)
  B = np.array(B)
  dif = A.ravel() - B.ravel()
  return np.dot( dif, dif )
def NCC(src, dst):
  src = np.array(src)
  dst = np.array(dst)
  # print(src.shape, dst.shape)
  src = src.astype(np.float32)
  dst = dst.astype(np.float32)
  src=  src - np.mean(src)#translate
  dst = dst - np.mean(dst)
  ncc = (np.sum(src * dst))/((np.linalg.norm(src)*(np.linalg.norm(dst)))+1e-12)
  return ncc
def normalize(img):
    #this function is used to normalise a image to adjust pixel range
    return cv2.normalize(img, None, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX)
def getTime(image_num, fps):
    num_seconds = image_num//fps
    time_point = str(num_seconds//60) + ':' + str(num_seconds%60) + ':' + str(1000/30 * (image_num%fps))
    return time_point

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
        # preds_t = preds_t.ravel()
        ret.append(preds_t)
    return ret

def getOffset(handler, path1, path2, start, m, diff): #path2 is smaller images(screen cropped)
    infile = path1 + '/out1.png'
    img = cv2.imread(infile, cv2.cv2.IMREAD_GRAYSCALE)
    width = img.shape[1]
    height = img.shape[0]
    dim = (width, height)

    DMmatrix1 =  getDMMatrix(handler, path2, start, m, diff, True,  dim)
    maxNCC = -1
    bestT = -np.inf
    for t in range(0, start):
        
        DMmatrix2 = getDMMatrix(handler, path1, start + t, m, diff, False,  dim)
        ncc = NCC(DMmatrix1, DMmatrix2)
        # print(ncc)
        if(ncc > maxNCC):
            print(start + t, start)
            maxNCC = ncc
            bestT = t
    print(bestT)
    print(maxNCC)
    return bestT
def getOffset_ssd(handler, path1, path2, start, m, diff): #path2 is smaller images(screen cropped)
    infile = path2 + '/out1.png'
    img = cv2.imread(infile, cv2.cv2.IMREAD_GRAYSCALE)
    width = img.shape[1]
    height = img.shape[0]
    dim = (width, height)

    DMmatrix1 =  getDMMatrix(handler, path2, start, m, diff, True,  dim)
    minssd = np.inf
    bestT = -np.inf
    for t in range(0, start):
        # print(start + t)
        DMmatrix2 = getDMMatrix(handler, path1, start + t, m, diff, False,  dim)
        ss = ssd(DMmatrix1, DMmatrix2)
        # print(ncc)
        if(ss < minssd):
            minssd = ss
            bestT = t
    print(bestT)
    print(minssd)
    return bestT

def getdim(infile):
  #infile = 'screen_frames/out' + str(chk) + '.png'
  img_last = cv2.imread(infile)

  width = img_last.shape[1]
  height = img_last.shape[0]
  dim = (width, height)
  return dim
def getoffset_random(handler, frame_count, f_vid,chk, dim):
  maxs = []
  mxNCCs = []
  A = np.random.permutation(f_vid)
  A = A + 1
  A = A[:frame_count]
  for j in range(frame_count):  
    outfile = 'video_frames/out' + str(A[j]) + '.png'
    bigImg = cv2.imread(outfile)
    resized = cv2.resize(bigImg, dim, interpolation=cv2.INTER_AREA)
    resized = cv2.flip(resized, 1)
    preds = handler.get(resized, get_all=True)
    preds = np.array(preds)
    maxNCC = 0
    for i in range(1, chk+1):
      infile = 'screen_frames/out' + str(i) + '.png'
      img = cv2.imread(infile)
      preds_t = handler.get(img, get_all=True)
      preds_t = np.array(preds_t)
      if preds.size != 0 and preds_t.size!=0:
        x = NCC(preds_t,preds)
        if x > maxNCC:
          maxNCC = x
          maxIndex = i
      else:
        x = 0
    mxNCCs.append(maxNCC)
    maxs.append(maxIndex)
    print(maxIndex - A[j])
  maxs = np.array(maxs)
  mxNCCs = np.array(mxNCCs)
  offset = maxs - A
  offset = round(np.mean(offset))
  return offset