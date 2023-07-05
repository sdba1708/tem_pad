import cv2
import numpy as np
import glob 
import os
import pickle
import time
from PIL import Image, ImageDraw, ImageFont

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

def IsPBWindow(image, mask):
    # ハードコーディング

    acc = 0.8   # maskと8割以上一致したらPB画面と判定
    
    
    mask_sum = mask.sum(axis=0).sum(axis=0)
    in_sum = image.sum(axis=0).sum(axis=0)   
    if in_sum > (image.shape[0] * image.shape[1]) // 2 :  # 画面の半分以上が明るい場合対象外
        #print("in_sum : ", in_sum, ", thresh : ",  (image.shape[0] * image.shape[1]) // 2)
        return False
        
    masked_img = mask * image
    masked_sum = masked_img.sum(axis=0).sum(axis=0)
    
    if masked_sum >= mask_sum * acc:
        return True
    #print("masked_sum : ", masked_sum, ", mask_sum * acc : ", mask_sum * acc)
    
    return False

def to_binary(src):
    # input : array(h, w, 3)
    # output : array(h, w) [binary]
    th=230
    bin_img = np.sum(src, axis=2) # 3ch -> 1ch
    bin_img = np.where(bin_img > th * 3, 1, 0)
    return bin_img


def expand_img(src):
    # input : array(h, w)
    # output : array(h, w)
    h, w = src.shape
    out_img = np.zeros_like(src)
    exp_src = np.pad(src, [(1, 1), (1, 1)], "constant")
    for j in range(3):
        for i in range(3):
            out_img += exp_src[j:h+j, i:w+i]
    out_img = np.clip(out_img, 0, 1)
    return out_img
    

def syn_tech_img(tech_dict, tech_name):
    
    out_img = None
    back_path = ".\\data\\back"
    icon_path = ".\\data\\icon"
    
    # load img
    tmp_hold = 2 # tech_dict[tech_name][hold]
    back_img = Image.open(os.path.join(back_path, "tech_back_hold" + str(tmp_hold)+".png"))

    # Synthesize Image
    tmp_type = "Melee"# tech_dict[tech_name][type]
    tmp_syna_type = "" # tech_dict[tech_name][syn_type]
    tmp_tech_name = "ごてんしょうばくしん" # tech_dict[tech_name][jp_name]
    tmp_prio = "VeryLow"
    tmp_cate = "Status"
    tmp_dmg = "-"
    tmp_sta = "18"
    tmp_tgt = "自分以外の1体"
    tmp_disc = "対象にはめつ5とむこう5を付与"
    
    # Syn image
    # type
    tmp_img = Image.open(os.path.join(icon_path, str(tmp_type)+".png"))
    tmp_img = tmp_img.resize((256, 256))
    #.resize((256, 256))
    back_img.paste(tmp_img, (65, 75), tmp_img)
    # Name
    
    
    return back_img

def gen_tech_imgs(tech_list):
    
    if len(tech_list) < 1:
        return None
    
    img_list = []
    
    tech_dict = None # 辞書をcsvから読み込む
    
    for tmp_tech in tech_list:
        img_list.append(syn_tech_img(tech_dict, tmp_tech))
        
    return img_list

def load_icon():
    data = "R0lGODlhAAHgAOf/ACYnJScoJisnJicpJyEqNCUqMScqLCMrNikrKCQsNyosKiwt\
KyYuOSguNS0uLC4wLS4xMywyOTAyMDI0MTczLzI2ODQ2Mzw1KDU3NTs3MTc5Nj04\
NTQ6QTg6N0I5JTc7PTk7OT87NDs9OkY8Ijw+O0Q9Mj0/PD5APUQ/Oz9BPkhAMD5C\
RUBCP0tBLUFDQFNCIkNFQkpEPkNHSUVHRE5GNkZIRUxHPFlGHVFHMkVJTEdJRkxI\
QlJILkhJR09JQ1FJPklLSFpJKUpMSUxOS2BMHlJOQk1PTGFNJU5QTVhPOlpPNFZQ\
P09RTlxQMFdQRVNRSlBST2VQG2JQLGJQMlFTUFJUUVNVU2hUK1pWSllWT1VXVGxW\
Gm9XFFdZVmhWPWlXM2FYSGRYPWdYOGxYKG5YI11ZV2NZRFlbWFxcVF1dVWBdSm5b\
MXRcEF9eUWReQXhdB2ldQmBfUmdeTWleSXZeG2NgTnJfL2ZhSnZgKm1hQHFhPGdj\
S3hhJXRhN29jSGplR3tkGXFkRH5lEoFjInJlRHpnEXdlNIFmB3RmQH1mKnlnL35p\
CHVnQXtoJH9nJHdoPHlqPXtrOX1sOohtEopuBYRvEYVwBI5tB4ZtKoBuNoluHIdu\
JINvK4RwHINzBYJwMY5xAINxMoRyM4ZyLZRyAIt1AIdzLoh3AI50KpV0Eo10MZN0\
HI91K5F2JIx7ApJ3JZN3Jo17FIl+A459AJV5IJt4GZx5DZ56AIuAAJd6IZF/AJh7\
Ipl8Gpp9HJiAAI+DAJt+HZSCEJ1/E42HAKN/FpeFA6WBGaeCDZGLBq+DAZ2IDamE\
EZSNAKyGAquFE56LAK2HBZKRAK+IB5uOEbCJCbGKC56RA7aJD6SQBpaVAriLALmM\
ALqNAbuOA5qZALyPBaSWD76QAKeZALChALGhEqyjELOpB7iuE7uxAsC5E8S9AcrE\
E83GANHKCNXOEtnRANTSGNXUAN/XD9zaEeHeAOXiCuvnGO7pAPLtDO3vCvfyGfL0\
GfX2APn6Cv7/Gf///yH+EUNyZWF0ZWQgd2l0aCBHSU1QACH5BAEKAP8ALAAAAAAA\
AeAAAAj+AP8JHEiwoMGDCBMaJMCwocOHECNKnEixosWLGDNq3EhAocePIEOKHOmR\
o8mTKFOqXBmRpMuXMGMuZEmzps2bJ2Xq3MlzJs6fQIPa7Em06EuhSJMqxWi0qdOE\
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\
Ow=="
    
    return data

