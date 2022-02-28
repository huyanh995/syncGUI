"""
Webcam & egocentric syn
Only crop the egocentric video
Assume egocentric is earlier
Modified by:Yifeng Huang(yifehuang@cs.stonybrook.edu)
Based on: Minh Hoai Nguyen (v.hoainm@vinai.io)
Last modified: 02-Feb-2022
"""

import subprocess
from scipy.io import wavfile
from librosa.feature import mfcc
import os, tempfile, warnings
import numpy as np
from scipy.signal import correlate2d
import time
from math import pi, sqrt, exp

def gauss1d(n=21,sigma=1):
    r = range(-int(n/2),int(n/2)+1)
    return [1 / (sigma * sqrt(2*pi)) * exp(-float(x)**2/(2*sigma**2)) for x in r]


# Find the offset in seconds between two files
# returns:
#   offset: offset in seconds
#       A positive value means file1 start earliers than file2 and the beginning of file1 should be trimmed.
#       A negative value means file2 start earliers than file1 and the beginning of file2 should be trimmed.
#   score: a score to indicate the matching of the two sync files.
#       The higher score, the more confidence the sync program is
#       For statistically reliable, score should be at least 3 or higher


import datetime
def find_offset(file1, file2, trim, max_offset_in_seconds=60):
    fs = 22050 # audio sampling rate
    #hop_length = 512 # for mfcc
    #corr_win = 10 # size of the window for correlation (in seconds)
    hop_length = 64  # for mfcc
    corr_win = 10 # size of the window for correlation (in seconds)
    log = ""

    #print("Extract/convert wav files ... ")
    log += "Extract/convert wav files ... "
    start = time.time()
    tmp1 = extract_wav_file(file1, fs, trim)
    tmp2 = extract_wav_file(file2, fs, trim)
    stop = time.time()
    log += "{:0.2f}s\n".format(stop-start)
    #print("   Done. This took {:0.2f}s".format(stop-start))

    #print("Computing MFCC features ...")
    log += "Computing MFCC features ..."
    start = time.time()
    # Removing warnings because of 18 bits block size
    # outputted by ffmpeg https://trac.ffmpeg.org/ticket/1843
    warnings.simplefilter("ignore", wavfile.WavFileWarning)
    a1 = wavfile.read(tmp1, mmap=True)[1] / (2.0 ** 15)
    a2 = wavfile.read(tmp2, mmap=True)[1] / (2.0 ** 15)


    #Gaussian Smooth
    #2.13
    #G = gauss1d(11)
    #a1 = np.convolve(a1, G, 'same')
    #a2 = np.convolve(a2, G, 'same')

    #print('For smmmmmmmmmmmmmmmmmmmmmm', a1)
    #print(a1.shape)
    os.remove(tmp1)
    os.remove(tmp2)

    a1 = ensure_non_zero(a1)
    a2 = ensure_non_zero(a2)
    #print('a1', a1)
    #print(a1.shape)
    mfcc1 = mfcc(a1, hop_length=hop_length, sr=fs)
    #print('mmmmmmmmmmfffffff1', mfcc1)
    #print(mfcc1.shape)
    mfcc2 = mfcc(a2, hop_length=hop_length, sr=fs)
    mfcc1 = std_mfcc(mfcc1).T
    mfcc2 = std_mfcc(mfcc2).T
    # length of mfcc feature is: avfile_duration*fs/hop_length
    stop = time.time()
    #print("   Done. This took {:0.2f}s".format(stop - start))
    log += "{:0.2f}s\n".format(stop - start)
    #print("Finding offset using cross correlation ...")
    log += "Finding offset using cross correlation ..."
    start = time.time()
    max_offset = int(max_offset_in_seconds*fs/hop_length)
    correl_nframes = int(corr_win * fs / hop_length)
    #print('corrrrrrrr', correl_nframes)
    '''
    mfcc1 is the mfcc feature of webcam video
    mfcc2 is the mfcc feature of egocentric video
    '''

    max_k_index1, score1 = find_offset_index(mfcc1, mfcc2, nframes=correl_nframes, max_offset=max_offset)
    max_k_index2, score2 = find_offset_index(mfcc2, mfcc1, nframes=correl_nframes, max_offset=max_offset)
    stop = time.time()
    #print("   Done. This took {:0.2f}s".format(stop - start))
    log += "{:0.2f}s\n".format(stop - start)
    '''
    if score1 > score2:
        max_k_index = max_k_index1
        score = score1
    else:
        max_k_index = - max_k_index2
        score = score2
    '''

    #egocentric will be earlier, so the offset is negative
    max_k_index = - max_k_index2
    score = score2
    offset = max_k_index * hop_length / float(fs) # * over / sample rate


    return offset, score, log


def ensure_non_zero(signal):
    # We add a little bit of static to avoid
    # 'divide by zero encountered in log'
    # during MFCC computation
    signal += np.random.random(len(signal)) * 10**-10
    return signal


def std_mfcc(mfcc):
    return (mfcc - np.mean(mfcc, axis=0)) / np.std(mfcc, axis=0)


# Find offset index using cross corelation
# Assume mfcc1 starts before mfcc2, find the positive offset to trim the beginning of mfcc1
# Return:
#   offset_idx: offset index for mfcc1 to align with mfcc2
#        mfcc2[0:duration] is aligned with mfcc1[ofset_idx:offset_idx+duration]
#   score: the score of the matching
def find_offset_index(mfcc1, mfcc2, nframes, max_offset):

    n1, mdim1 = mfcc1.shape
    n2, mdim2 = mfcc2.shape
    nframes = int(min(nframes, 0.2 * n2 - 1))
    max_offset = min(max_offset, n1 - nframes - 1)

    min_idx = int(np.floor(0.1*n2))
    max_idx = int(np.floor(min([0.9*n2 - nframes, n1 - nframes - max_offset]))) - 1
    if min_idx > max_idx:
        min_idx = 0

    idxs = np.linspace(min_idx, max_idx, num=10)

    c = np.zeros(shape=(len(idxs), max_offset+1))
    for i in range(len(idxs)):
        idx = int(idxs[i])
        c_i = correlate2d(mfcc1[idx:idx+nframes+max_offset], mfcc2[idx:idx+nframes], mode='valid')

        c[i,:] = c_i[:,0]
    c = np.sum(c, axis=0)

    offset_idx = np.argmax(c)
    score = (c[offset_idx] - np.mean(c)) / np.std(c)  # standard score of peak

    return offset_idx, score

# Extract a temporary wav file
def extract_wav_file(afile, fs, trim):
    tmp = tempfile.NamedTemporaryFile(mode='r+b', prefix='offset_', suffix='.wav')
    tmp_name = tmp.name
    tmp.close()
    if trim == -1:
        psox = subprocess.Popen([
            'ffmpeg', '-loglevel', 'panic', '-i', afile,
            '-ac', '1', '-ar', str(fs), '-acodec', 'pcm_s16le', tmp_name
        ], stderr=subprocess.PIPE)
    else:
        psox = subprocess.Popen([
            'ffmpeg', '-loglevel', 'panic', '-i', afile,
            '-ac', '1', '-ar', str(fs), '-t', str(trim), '-acodec', 'pcm_s16le', tmp_name
        ], stderr=subprocess.PIPE)
    psox.communicate()
    if not psox.returncode == 0:
        raise Exception("FFMpeg failed")
    return tmp_name


def create_sync_file(in_file, ss, duration):
    base_name = os.path.basename(in_file)
    dir_name = os.path.dirname(in_file)
    file_name = os.path.splitext(base_name)[0]
    file_ext = os.path.splitext(base_name)[1]
    out_file = "{}/{}_sync{}".format(dir_name, file_name, file_ext)
    print(out_file)
    cmd = ' '.join(['ffmpeg', '-y', '-loglevel', 'panic', '-i', in_file, '-ss', str(ss), '-t', str(duration), '-c copy', out_file])
    print("   " + cmd)
    subprocess.call(cmd, shell=True)
    return out_file


def get_length(filename):
    result = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                             "format=duration", "-of",
                             "default=noprint_wrappers=1:nokey=1", filename],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT)
    return float(result.stdout)



def wp_sync_call(file1, file2, max_offset, trim):
    print("DEBUG: >>>>>", file1, file2)

    if trim == 0:
        trim = 2*max_offset

    offset, score, log = find_offset(file1, file2, trim=trim, max_offset_in_seconds=max_offset)

    if score < 3:
        log += "WARNING: Low sync score. Manually check the output files carefully.\n"
        # print("============> WARNING: Low sync score. Manually check the output files carefully.")

    len1 = get_length(file1)
    len2 = get_length(file2)


    '''
    offset < 0, since egocentric video will starts earlier
    '''
    if offset > 0:
        # print("File1 starts earlier than File2 by {:0.3f} seconds. Sync score: {:0.2f}".format(offset, score))
        ss1 = offset
        ss2 = 0
        duration = min(len2, len1 - offset)
    else:
        offset = -offset
        # print("File2 starts earlier than File1 by {:0.3f} seconds. Sync score: {:0.2f}".format(offset, score))
        ss1 = 0
        ss2 = offset
        duration = min(len1, len2 - offset)

    # print("   Shared duration: {}".format(duration))

    # print("Create sync egocentric video ...")
    start = time.time()

    out_file2 = create_sync_file(file2, ss2, duration)
    # stop = time.time()
    # #print("   File {} was created".format(out_file1))
    # print("   File {} was created".format(out_file2))
    # print("   Done. This took {:0.2f}s".format(stop - start))
    return out_file2, log
