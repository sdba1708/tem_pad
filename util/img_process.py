import cv2
import numpy as np
import glob 
import os
import pickle
import time

def extract_tem_region(src_img, ofs_x = 0, ofs_y = 0, dump_region=True, left_flag=False):
    img_list = []
    delta = 150
    h = 78
    w = 78
    size_ofs_x = src_img.shape[1] - 1602
    size_ofs_y = src_img.shape[0] - 932
    

    white = np.ones((h, w, 3)).astype(np.uint8)  * 255
    white[2:h-2, 2:w-2] = np.zeros((h-4, w-4, 3)).astype(np.uint8)
    bb1 = None
    bb2 = None
    if left_flag:
        bb1 = [200 + size_ofs_y + ofs_y, 98 + size_ofs_x + ofs_x]
        bb2 = [275 + size_ofs_y + ofs_y, 55 + size_ofs_x + ofs_x]
    else:
        bb1 = [199 + size_ofs_y + ofs_y, 1425 + size_ofs_x + ofs_x]
        bb2 = [275 + size_ofs_y + ofs_y, 1469 + size_ofs_x + ofs_x]
    mask_path=".\\data\\mask.npy"
    mask = np.load(mask_path)
    cp_src = src_img.astype(np.uint16)
    for i in range(4):
        y1 = bb1[0] + i * delta
        x1 = bb1[1]
        y2 = bb2[0] + i * delta
        x2 = bb2[1]
        if x1 < 0 or x2 < 0 or y1 < 0 or y2 < 0:
            return []
        tmp_img1 = src_img[y1:y1+h, x1:x1+w, :]
        tmp_img2 = src_img[y2:y2+h, x2:x2+w, :]
        if left_flag: # flip image
            tmp_img1 = cv2.flip(tmp_img1, 1)
            tmp_img2 = cv2.flip(tmp_img2, 1) 
        tmp_img1 = cv2.bitwise_and(tmp_img1,tmp_img1,mask = mask)
        tmp_img2 = cv2.bitwise_and(tmp_img2,tmp_img2,mask = mask)
        if dump_region:
            cp_src[y1:y1+h, x1:x1+w,:] += white
            cp_src[y2:y2+h, x2:x2+w,:] += white
        #cv2.imwrite("./extract_tem_"+str(2 * i)+".png", tmp_img1)
        #cv2.imwrite("./extract_tem_"+str(2 * i + 1)+".png", tmp_img2)
        img_list.append(tmp_img1)
        img_list.append(tmp_img2)
    
    if dump_region:
        cv2.imwrite("dump_region.png", np.clip(cp_src, 0, 255).astype(np.uint8))

    return img_list 

def run_img_detection(img_list):
    tem_list = []
    reg_path=".\\data\\regs2.bin"
    luma_path=".\\data\\lumas2.bin"
    
    with open(reg_path, 'rb') as p:
        reg_data = pickle.load(p)
    with open(luma_path, 'rb') as p:
        luma_data = pickle.load(p)

    loop_num = len(reg_data)
    detector = cv2.ORB_create(nfeatures=100, fastThreshold=0, edgeThreshold=0)
    bf = cv2.BFMatcher(cv2.NORM_HAMMING)

    for tgt in img_list:     
            min_dist = 1000000000
            max_idx = -100

            _, tgt_des = detector.detectAndCompute(cv2.resize(tgt, (200,200)), None)

            for i in range(loop_num):
                # reg detection
                reg_des = reg_data[i]
                luma_des = luma_data[i]
                #_, reg_des = detector.detectAndCompute(reg_data[i, :, :, :], None)
                #_, luma_des = detector.detectAndCompute(luma_data[i, :, :, :], None)
                matches = bf.match(tgt_des, reg_des)
                dist = [m.distance for m in matches]
                reg_dist = sum(dist) / len(dist)
                matches = bf.match(tgt_des, luma_des)
                dist = [m.distance for m in matches]
                luma_dist = sum(dist) / len(dist)
                
                dist = min(reg_dist, luma_dist)
                if min_dist > dist:
                    min_dist = dist
                    max_idx = i
            tem_list.append(max_idx)
    return tem_list

def detect_tem(src_img,  ofs_x = 0, ofs_y = 0, dump_region=True, left_flag=False):

    # extract temtem portrait from src_img
    img_list = extract_tem_region(src_img,  ofs_x, ofs_y, dump_region, left_flag)

    # run detection
    tem_list = run_img_detection(img_list)

    return tem_list



