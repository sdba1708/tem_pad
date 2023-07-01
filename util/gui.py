
# -*- coding: utf-8 -*-

#from sys import get_asyncgen_hooks
from tkinter import * 
from tkinter import ttk, font
#from xml.dom import NoModificationAllowedErr
#from ttkwidgets.frames import ScrolledFrame
#from tkscrolledframe import ScrolledFrame
from PIL import Image, ImageTk, ImageGrab
import numpy as np
import os
#import pygetwindow as gw
import win32gui
import time
import pandas as pd
from util.img_process import detect_tem, gen_tech_imgs, load_icon
from util.data_process import data_processor, get_setting_init, save_setting_init
from util.common import get_app_rect
import cv2
import webbrowser
import threading

DEBUG_FLAG=False

class Window():
    def __init__(self):
        self.root = Tk()
        self.root.geometry("1800x900+100+100")
        self.root.title('Tem Pick Assist Tool')
        self.root.config(bg = '#add123')
        self.root.wm_attributes('-transparentcolor','#add123')
        # load icon
        #icon = PhotoImage(file="data\\icon.png")
        self.root.iconphoto(True, PhotoImage(data=load_icon()))
        
        tmp_set_data = get_setting_init()
        self.detection_ofs = {
            "ofst_x" : tmp_set_data[0],
            "ofst_y" : tmp_set_data[1],
            "dump_flag" : BooleanVar(value=tmp_set_data[2]),
            "link_var" : StringVar(value=tmp_set_data[3])
        }
        self.url_setting={
            "official" : "https://temtem.wiki.gg/wiki",
            "temtetsu" : "https://temtetsu.pages.dev/species"
        }
        
        # Menu Window
        self.men_win = Menu(self.root, tearoff=0)
        self.root.config(menu=self.men_win)
        menu_set = Menu(self.root, tearoff=0)
        self.men_win.add_cascade(label="オプション", menu=menu_set)
        menu_set.add_command(label='検出枠位置調整', command=lambda:self.show_tuning_window())
        menu_set.add_command(label='設定', command=lambda:self.show_setting_window()) 
        #menu_set.add_separator() 
        
        # 透過
        a = ttk.Style()
        a.configure('trans.TFrame', background='#add123')

        # generate widged
        self.left_base_frame = ttk.Frame(self.root, width=100, height=900)
        self.trans_base_frame = ttk.Frame(self.root, width=1600, height=900, style='trans.TFrame')#ScrolledFrame(self.root, autohidescrollbar=False)
        self.right_base_frame = ttk.Frame(self.root, width=100, height=900)
        self.left_base_frame.propagate(False)
        self.trans_base_frame.propagate(False)
        self.right_base_frame.propagate(False)
        '''
            csv data
            tem_db.iat[NoID, Pos]
            ex) tem_db.iat[0, 1] = "Mimit", tem_db.iat[0, 2] = "Digital"
        
        '''
        csv_file=".\\data\\data.csv"
        self.tem_db = pd.read_csv(csv_file, encoding='utf-8', delimiter=',', header=None)

        # label
        # height, width, ch
        self.left_small_frame = []
        self.right_small_frame = []
        self.dummy_image = ImageTk.PhotoImage(Image.fromarray(np.zeros((64, 64, 3)), mode="RGB"))
        self.dummy_type = ImageTk.PhotoImage(Image.fromarray(np.zeros((32, 24, 4)), mode="RGBA"))
        self.left_imgs = {
            "face" : [],
            "name" : [],
            "type1" : [],
            "type2" : [],
            "stats" : []
        }
        self.right_imgs = {
            "face" : [],
            "name" : [],
            "type1" : [],
            "type2" : [],
            "stats" : []
        }
        type_dir = ".\\data\\icon"
        self.type_imgs = { 
            "Neutral"   : ImageTk.PhotoImage(Image.open(os.path.join(type_dir, "Neutral.png")).resize((24, 32))),
            "Wind"      : ImageTk.PhotoImage(Image.open(os.path.join(type_dir, "Wind.png")).resize((24, 32))),
            "Earth"     : ImageTk.PhotoImage(Image.open(os.path.join(type_dir, "Earth.png")).resize((24, 32))),
            "Water"     : ImageTk.PhotoImage(Image.open(os.path.join(type_dir, "Water.png")).resize((24, 32))),
            "Fire"      : ImageTk.PhotoImage(Image.open(os.path.join(type_dir, "Fire.png")).resize((24, 32))),
            "Nature"    : ImageTk.PhotoImage(Image.open(os.path.join(type_dir, "Nature.png")).resize((24, 32))),
            "Electric"  : ImageTk.PhotoImage(Image.open(os.path.join(type_dir, "Electric.png")).resize((24, 32))),
            "Mental"    : ImageTk.PhotoImage(Image.open(os.path.join(type_dir, "Mental.png")).resize((24, 32))),
            "Digital"   : ImageTk.PhotoImage(Image.open(os.path.join(type_dir, "Digital.png")).resize((24, 32))),
            "Melee"     : ImageTk.PhotoImage(Image.open(os.path.join(type_dir, "Melee.png")).resize((24, 32))),
            "Crystal"   : ImageTk.PhotoImage(Image.open(os.path.join(type_dir, "Crystal.png")).resize((24, 32))),
            "Toxic"     : ImageTk.PhotoImage(Image.open(os.path.join(type_dir, "Toxic.png")).resize((24, 32))),
            "Dummy"     : self.dummy_type
        }
        self.left_obj = {
            "name" : [],
            "face" : [],
            "type1" : [],
            "type2" : []
        }
        self.right_obj = {
            "name" : [],
            "face" : [],
            "type1" : [],
            "type2" : []
        }

        for i in range(8):
            # set small frames
            self.left_small_frame.append(ttk.Frame(self.left_base_frame, width=100, height=100, relief="groove"))
            self.right_small_frame.append(ttk.Frame(self.right_base_frame, width=100, height=100, relief="groove"))
            # set dummy images
            self.left_imgs["face"].append(self.dummy_image)
            self.left_imgs["name"].append("None")
            self.left_imgs["type1"].append("Dummy")
            self.left_imgs["type2"].append("Dummy")
            self.left_imgs["stats"].append([])
            self.right_imgs["face"].append(self.dummy_image)
            self.right_imgs["name"].append("None")
            self.right_imgs["type1"].append("Dummy")
            self.right_imgs["type2"].append("Dummy")
            self.right_imgs["stats"].append([])
            # set objects
            self.left_obj['name'].append(ttk.Label(self.left_small_frame[i], text="None", foreground="blue", cursor="hand1"))
            self.left_obj['type1'].append(ttk.Label(self.left_small_frame[i], image=self.type_imgs["Dummy"]))
            self.left_obj['type2'].append(ttk.Label(self.left_small_frame[i], image=self.type_imgs["Dummy"]))
            self.right_obj['name'].append(ttk.Label(self.right_small_frame[i], text="None", foreground="blue", cursor="hand1"))
            self.right_obj['type1'].append(ttk.Label(self.right_small_frame[i], image=self.type_imgs["Dummy"]))
            self.right_obj['type2'].append(ttk.Label(self.right_small_frame[i], image=self.type_imgs["Dummy"]))
            
        
        self.left_obj['face'].append(ttk.Button(self.left_small_frame[0], image=self.left_imgs["face"][0], command =lambda:self.show_tem_face_window(left_flag=True, idx=0)))
        self.left_obj['face'].append(ttk.Button(self.left_small_frame[1], image=self.left_imgs["face"][1], command =lambda:self.show_tem_face_window(left_flag=True, idx=1)))
        self.left_obj['face'].append(ttk.Button(self.left_small_frame[2], image=self.left_imgs["face"][2], command =lambda:self.show_tem_face_window(left_flag=True, idx=2)))
        self.left_obj['face'].append(ttk.Button(self.left_small_frame[3], image=self.left_imgs["face"][3], command =lambda:self.show_tem_face_window(left_flag=True, idx=3)))
        self.left_obj['face'].append(ttk.Button(self.left_small_frame[4], image=self.left_imgs["face"][4], command =lambda:self.show_tem_face_window(left_flag=True, idx=4)))
        self.left_obj['face'].append(ttk.Button(self.left_small_frame[5], image=self.left_imgs["face"][5], command =lambda:self.show_tem_face_window(left_flag=True, idx=5)))
        self.left_obj['face'].append(ttk.Button(self.left_small_frame[6], image=self.left_imgs["face"][6], command =lambda:self.show_tem_face_window(left_flag=True, idx=6)))
        self.left_obj['face'].append(ttk.Button(self.left_small_frame[7], image=self.left_imgs["face"][7], command =lambda:self.show_tem_face_window(left_flag=True, idx=7)))
        self.right_obj['face'].append(ttk.Button(self.right_small_frame[0], image=self.right_imgs["face"][0], command =lambda:self.show_tem_face_window(left_flag=False, idx=0)))
        self.right_obj['face'].append(ttk.Button(self.right_small_frame[1], image=self.right_imgs["face"][1], command =lambda:self.show_tem_face_window(left_flag=False, idx=1)))
        self.right_obj['face'].append(ttk.Button(self.right_small_frame[2], image=self.right_imgs["face"][2], command =lambda:self.show_tem_face_window(left_flag=False, idx=2)))
        self.right_obj['face'].append(ttk.Button(self.right_small_frame[3], image=self.right_imgs["face"][3], command =lambda:self.show_tem_face_window(left_flag=False, idx=3)))
        self.right_obj['face'].append(ttk.Button(self.right_small_frame[4], image=self.right_imgs["face"][4], command =lambda:self.show_tem_face_window(left_flag=False, idx=4)))
        self.right_obj['face'].append(ttk.Button(self.right_small_frame[5], image=self.right_imgs["face"][5], command =lambda:self.show_tem_face_window(left_flag=False, idx=5)))
        self.right_obj['face'].append(ttk.Button(self.right_small_frame[6], image=self.right_imgs["face"][6], command =lambda:self.show_tem_face_window(left_flag=False, idx=6)))
        self.right_obj['face'].append(ttk.Button(self.right_small_frame[7], image=self.right_imgs["face"][7], command =lambda:self.show_tem_face_window(left_flag=False, idx=7)))   

      
        self.left_button = ttk.Button(
            self.left_base_frame,
            text='認識',
            command=lambda: self.update_window(left_flag=True)
            )
        
        self.left_detail_button = ttk.Button(
            self.left_base_frame,
            text='耐性一覧',
            command=lambda: self.show_type_res(left_flag=True)
            )
        
        self.left_stats_button = ttk.Button(
            self.left_base_frame,
            text='基本能力値一覧',
            command=lambda: self.show_stats(left_flag=True)
            )

        self.right_button = ttk.Button(
            self.right_base_frame,
            text='認識',
            command=lambda: self.update_window(left_flag=False)
            )
        
        self.right_detail_button = ttk.Button(
            self.right_base_frame,
            text='耐性一覧',
            command=lambda: self.show_type_res(left_flag=False)
            )
        
        self.right_stats_button = ttk.Button(
            self.right_base_frame,
            text='基本能力値一覧',
            command=lambda: self.show_stats(left_flag=False)
            )
        

        self.left_base_frame.pack(side=LEFT)
        self.trans_base_frame.pack(side=LEFT)
        self.right_base_frame.pack(side=LEFT)       

        for i in range(8):
            self.left_small_frame[i].grid_propagate(False)
            self.right_small_frame[i].grid_propagate(False)
            self.left_small_frame[i].pack(side=TOP)
            self.right_small_frame[i].pack(side=TOP)
            self.left_obj['name'][i].grid(column=0, row=0, columnspan=2, sticky=E+W, padx=4, pady=4)
            self.left_obj['face'][i].grid(column=0, row=1, rowspan=2, sticky=N+S)
            self.left_obj['type1'][i].grid(column=1, row=1)
            self.left_obj['type2'][i].grid(column=1, row=2)
            self.right_obj['name'][i].grid(column=0, row=0, columnspan=2, sticky=E+W, padx=4, pady=4)
            self.right_obj['face'][i].grid(column=0, row=1, rowspan=2, sticky=N+S)
            self.right_obj['type1'][i].grid(column=1, row=1)
            self.right_obj['type2'][i].grid(column=1, row=2)
            
        self.left_button.pack(side=TOP)
        self.left_detail_button.pack(side=TOP)
        self.left_stats_button.pack(side=TOP)
        self.right_button.pack(side=TOP)
        self.right_detail_button.pack(side=TOP)
        self.right_stats_button.pack(side=TOP)
        self.res_win_obj = [
            None,
            None
        ]
        self.res_win_pos = [
            None,   # left
            None    # right
        ]
        self.stats_win_obj = [
            None,
            None
        ]
        self.stats_win_pos = [
            None,   # left
            None    # right
        ]
        
        self.timeEvent()
        

    def timeEvent(self):
        th = threading.Thread(target=self.update)   # スレッドインスタンス
        th.start()                                  # スレッドスタート
        self.root.after(1000, self.timeEvent)       # 再帰的な関数呼び出し。afterはもともとあるっぽい

    #
    def update(self):
        # update window pos
        _, rect = get_app_rect()
        if rect is not None:
            #print(rect)
            self.root.geometry("+"+str(rect.left-106)+"+"+str(rect.top-20))
           


    def mouse_wheel_stats(self, event):
        self.stats_window._canvas.yview_scroll(int(-1*(event.delta/120)), "units") 
    def mouse_wheel_type(self, event):
        self.type_window._canvas.yview_scroll(int(-1*(event.delta/120)), "units") 

    def run(self):
        self.root.mainloop()
    
    def get_screenshot(self, dummy=False):
        
        if dummy:
            scs = cv2.imread("dump_screenshot.png")
            return scs

        tem_window, rect = get_app_rect()
        if rect is None:
            return []
        #bb = [x1, y1, x2, y2]
        bb = [rect.left, rect.top, rect.right, rect.bottom]
        win32gui.SetForegroundWindow(tem_window)
        time.sleep(0.5)
        scs = ImageGrab.grab(bbox=bb)
        # dump
        #scs.save("dump_screenshot.png")
        return np.array(scs)
    
    def link_click(self, url):
        webbrowser.open_new(url)

    def is_num(self, s):
        try:
            float(s)
        except ValueError:
            return 0
        else:
            return int(s)
        
    def update_window(self, left_flag=False):
    
        # get screenshot
        scs = self.get_screenshot(dummy=DEBUG_FLAG)
        
        # get Entry data
        ofs_x = self.detection_ofs["ofst_x"]
        ofs_y = self.detection_ofs["ofst_y"] #self.is_num(self.tb2.get())
        tmp_flag = self.detection_ofs["dump_flag"].get()

        # もしleft, right両方ともまだ未認識だったらどちらも認識を走らせる
        run_left = left_flag
        run_right = False if left_flag else True
        if self.left_obj["name"][0].cget("text") == "None":
            run_left = True
        if self.right_obj["name"][0].cget("text") == "None":
            run_right = True

        image_dir = ".\\data\\port"
        # update image
        link_list = [[], []]
        if run_left:
            # get tem list
            tem_list = detect_tem(cv2.cvtColor(scs, cv2.COLOR_BGR2RGB),  ofs_x, ofs_y, tmp_flag, left_flag = True)
  
            for i in range(len(tem_list)):
                # update portrait
                image_name = os.path.join(image_dir, str(tem_list[i]).zfill(5)+".png")
                with Image.open(image_name) as im:
                    if im.size[0] != 64 and im.size[1] != 64:
                        self.left_imgs["face"][i] = ImageTk.PhotoImage(im.resize((64, 64)))
                    else:
                        self.left_imgs["face"][i] = ImageTk.PhotoImage(im)
                    self.left_obj['face'][i].config(image=(self.left_imgs["face"][i]))
                # update type
                tmp_type1 = self.tem_db.iat[tem_list[i], 3]
                self.left_imgs["type1"][i] = tmp_type1
                self.left_obj["type1"][i].config(image=self.type_imgs[tmp_type1])

                tmp_type2 = self.tem_db.iat[tem_list[i], 4]
                if tmp_type2 != "None":
                    self.left_imgs["type2"][i] = tmp_type2
                    self.left_obj["type2"][i].config(image=self.type_imgs[tmp_type2])
                else:
                    self.left_imgs["type2"][i] = "Dummy"
                    self.left_obj["type2"][i].config(image=self.type_imgs["Dummy"])
                
                tmp_name = self.tem_db.iat[tem_list[i], 1]
                tmp_name_jp = self.tem_db.iat[tem_list[i], 2]
                self.left_imgs["name"][i] = tmp_name
                self.left_obj["name"][i].config(text=tmp_name_jp)
                self.left_imgs["stats"][i] = [self.tem_db.iloc[tem_list[i], 5], self.tem_db.iloc[tem_list[i], 6], self.tem_db.iloc[tem_list[i], 7], self.tem_db.iloc[tem_list[i], 8], self.tem_db.iloc[tem_list[i], 9], self.tem_db.iloc[tem_list[i], 10], self.tem_db.iloc[tem_list[i], 11]]
                if self.detection_ofs["link_var"].get() == "official":
                    link_list[0].append("https://temtem.wiki.gg/wiki/" + tmp_name)
                else:
                    link_list[0].append("https://temtetsu.pages.dev/species/" + str(self.tem_db.iat[tem_list[i], 0]))

            # doesn't work in for loop?????
            self.left_obj["name"][0].bind("<Button-1>",lambda e:self.link_click(link_list[0][0]))
            self.left_obj["name"][1].bind("<Button-1>",lambda e:self.link_click(link_list[0][1]))
            self.left_obj["name"][2].bind("<Button-1>",lambda e:self.link_click(link_list[0][2]))
            self.left_obj["name"][3].bind("<Button-1>",lambda e:self.link_click(link_list[0][3]))
            self.left_obj["name"][4].bind("<Button-1>",lambda e:self.link_click(link_list[0][4]))
            self.left_obj["name"][5].bind("<Button-1>",lambda e:self.link_click(link_list[0][5]))
            self.left_obj["name"][6].bind("<Button-1>",lambda e:self.link_click(link_list[0][6]))
            self.left_obj["name"][7].bind("<Button-1>",lambda e:self.link_click(link_list[0][7]))
            
            # update sub windows if they are opend
            if self.res_win_obj[0] is not None:
                self.close_res_win(0)
                self.show_type_res(left_flag=True)
                
            if self.stats_win_obj[0] is not None:
                self.close_stats_win(0)
                self.show_stats(left_flag=True)
                
            

        if run_right:  # right side
            # get tem list
            tem_list = detect_tem(cv2.cvtColor(scs, cv2.COLOR_BGR2RGB),  ofs_x, ofs_y, tmp_flag, left_flag = False)
            for i in range(len(tem_list)):
                # update portrait
                image_name = os.path.join(image_dir, str(tem_list[i]).zfill(5)+".png")
                with Image.open(image_name) as im:
                    if im.size[0] != 64 and im.size[1] != 64:
                        self.right_imgs["face"][i] = ImageTk.PhotoImage(im.resize((64, 64)))
                    else:
                        self.right_imgs["face"][i] = ImageTk.PhotoImage(im)
                    self.right_obj["face"][i].config(image=(self.right_imgs["face"][i]))
                # update type
                tmp_type1 = self.tem_db.iat[tem_list[i], 3]
                self.right_imgs["type1"][i] = tmp_type1
                self.right_obj["type1"][i].config(image=self.type_imgs[tmp_type1])

                tmp_type2 = self.tem_db.iat[tem_list[i], 4]
                if tmp_type2 != "None":
                    self.right_imgs["type2"][i] = tmp_type2
                    self.right_obj["type2"][i].config(image=self.type_imgs[tmp_type2])
                else:
                    self.right_imgs["type2"][i] = "Dummy"
                    self.right_obj["type2"][i].config(image=self.type_imgs["Dummy"])

                tmp_name = self.tem_db.iat[tem_list[i], 1]
                tmp_name_jp = self.tem_db.iat[tem_list[i], 2]
                self.right_imgs["name"][i] = tmp_name
                self.right_obj["name"][i].config(text=tmp_name_jp)
                self.right_imgs["stats"][i] = [self.tem_db.iloc[tem_list[i], 5], self.tem_db.iloc[tem_list[i], 6], self.tem_db.iloc[tem_list[i], 7], self.tem_db.iloc[tem_list[i], 8], self.tem_db.iloc[tem_list[i], 9], self.tem_db.iloc[tem_list[i], 10], self.tem_db.iloc[tem_list[i], 11]]
                if self.detection_ofs["link_var"].get() == "official":
                    link_list[1].append("https://temtem.wiki.gg/wiki/" + tmp_name)
                else:
                    link_list[1].append("https://temtetsu.pages.dev/species/" + str(self.tem_db.iat[tem_list[i], 0]))

            # doesn't work in for loop?????
            self.right_obj["name"][0].bind("<Button-1>",lambda e:self.link_click(link_list[1][0]))
            self.right_obj["name"][1].bind("<Button-1>",lambda e:self.link_click(link_list[1][1]))
            self.right_obj["name"][2].bind("<Button-1>",lambda e:self.link_click(link_list[1][2]))
            self.right_obj["name"][3].bind("<Button-1>",lambda e:self.link_click(link_list[1][3]))
            self.right_obj["name"][4].bind("<Button-1>",lambda e:self.link_click(link_list[1][4]))
            self.right_obj["name"][5].bind("<Button-1>",lambda e:self.link_click(link_list[1][5]))
            self.right_obj["name"][6].bind("<Button-1>",lambda e:self.link_click(link_list[1][6]))
            self.right_obj["name"][7].bind("<Button-1>",lambda e:self.link_click(link_list[1][7]))
            
            # update sub windows if they are opend
            if self.res_win_obj[1] is not None:
                self.close_res_win(1)
                self.show_type_res(left_flag=False)
                
            if self.stats_win_obj[1] is not None:
                self.close_stats_win(1)
                self.show_stats(left_flag=False)
                

         
    def show_type_res(self, left_flag=False):
        flag_idx = 0 if left_flag else 1
       
        if self.res_win_obj[flag_idx] is not None:
            return
        
        self.res_win_obj[flag_idx] = Toplevel()
        tmp_x, tmp_y = 0, 0
        if left_flag:
            if self.res_win_pos[0] is None:
                tmp_x = str(self.left_detail_button.winfo_rootx())
                tmp_y = str(self.left_detail_button.winfo_rooty()-400)
                self.res_win_pos[0] = [tmp_x, tmp_y]
            else:
                tmp_x = str(self.res_win_pos[0][0] - 8)
                tmp_y = str(self.res_win_pos[0][1] - 31)
        else:
            if self.res_win_pos[1] is None:
                tmp_x = str(self.right_detail_button.winfo_rootx())
                tmp_y = str(self.right_detail_button.winfo_rooty()-400)
                self.res_win_pos[1] = [tmp_x, tmp_y]
            else:
                tmp_x = str(self.res_win_pos[1][0] - 8)
                tmp_y = str(self.res_win_pos[1][1] - 31)
        
        self.res_win_obj[flag_idx].geometry("500x400+"+tmp_x+"+"+tmp_y)
        self.res_win_obj[flag_idx].title('Team Resistances')
        type_window = Frame(self.res_win_obj[flag_idx], width = 500, height=400)
        type_window.pack(fill='both', expand=True)

            
        # Obj for get type info
        dp = data_processor()
        type_list = dp.get_type_name()

        tmp_label = Label(type_window, text="", height = 2, width=1)
        tmp_label.grid(column=0, row=0)
        for idx in range(len(type_list)):
            tmp_label = Label(type_window, image=self.type_imgs[type_list[idx]], height = 32, width=24)
            tmp_label.grid(column=idx+1, row=0)
                   
        for i in range(8):
            # get tem type info
            tmp_name = self.right_obj["name"][i].cget("text")
            if tmp_name != "None":
                if left_flag:
                    tmp_type1= self.left_imgs["type1"][i] if self.left_imgs["type1"][i] is not "Dummy" else None
                    tmp_type2= self.left_imgs["type2"][i] if self.left_imgs["type2"][i] is not "Dummy" else None
                    face = Label(type_window,image=self.left_imgs["face"][i], height = 32, width=32)
                else:
                    tmp_type1= self.right_imgs["type1"][i] if self.right_imgs["type1"][i] is not "Dummy" else None
                    tmp_type2= self.right_imgs["type2"][i] if self.right_imgs["type2"][i] is not "Dummy" else None
                    face = Label(type_window,image=self.right_imgs["face"][i], height = 32, width=32)

                res_summary = dp.calc_type_res(type1=tmp_type1, type2=tmp_type2)
                face.grid(column=0, row=i+1)
                for j in range(len(res_summary)):
                    tmp_color="azure"
                    if res_summary[j] == "2":
                        tmp_color="pale green"
                    elif res_summary[j] == "4":
                        tmp_color="lime green"
                    elif res_summary[j] == "0.5":
                        tmp_color="light coral"
                    elif res_summary[j] == "0.25":
                        tmp_color="red"
                    res_num = Label(type_window, text="x"+res_summary[j], height = 2, width=4, relief=SOLID, bg=tmp_color)
                    res_num.grid(column=j+1, row=i+1)        
        self.res_win_obj[flag_idx].protocol("WM_DELETE_WINDOW", lambda : self.close_res_win(flag_idx))
        
        
    def close_res_win(self, idx):
        pos_x = self.res_win_obj[idx].winfo_rootx()
        pos_y = self.res_win_obj[idx].winfo_rooty()
        self.res_win_pos[idx] = [pos_x, pos_y]
        self.res_win_obj[idx].destroy()
        self.res_win_obj[idx] = None
        

    def show_stats(self, left_flag=False):
        
        flag_idx = 0 if left_flag else 1
        if self.stats_win_obj[flag_idx] is not None:
            return
        
        self.stats_win_obj[flag_idx] = Toplevel()
        tmp_x, tmp_y = 0, 0
        if left_flag:
            if self.stats_win_pos[0] is None:
                tmp_x = str(self.left_detail_button.winfo_rootx())
                tmp_y = str(self.left_detail_button.winfo_rooty()-400)
                self.stats_win_pos[0] = [tmp_x, tmp_y]
            else:
                tmp_x = str(self.stats_win_pos[0][0] - 8)
                tmp_y = str(self.stats_win_pos[0][1] - 31)
        else:
            if self.stats_win_pos[1] is None:
                tmp_x = str(self.right_detail_button.winfo_rootx())
                tmp_y = str(self.right_detail_button.winfo_rooty()-400)
                self.stats_win_pos[1] = [tmp_x, tmp_y]
            else:
                tmp_x = str(self.stats_win_pos[1][0] - 8)
                tmp_y = str(self.stats_win_pos[1][1] - 31)
            
     
        self.stats_win_obj[flag_idx].geometry("500x400+"+tmp_x+"+"+tmp_y)
        self.stats_win_obj[flag_idx].title('Team Stats')
        stats_window = Frame(self.stats_win_obj[flag_idx], width = 500, height=400)
        stats_window.pack(fill='both', expand=True)

        # Obj for get type info
        stats_list = ["HP", "STA", "SPD", "ATK", "DEF", "SPATK", "SPDEF"]

        blank_label = Label(stats_window, text="", height = 1, width=1)
        blank_label.grid(column=0, row=0)
        for idx in range(len(stats_list)):
            tmp_label = Label(stats_window, text=stats_list[idx], height = 1, width=6)
            tmp_label.grid(column=idx+1, row=0)
                   
        for i in range(8):
            # get tem type info
            tmp_name = self.right_obj["name"][i].cget("text")
            if tmp_name is not "None":

                if left_flag:
                    tmp_stats = self.left_imgs["stats"][i]
                    face = Label(stats_window,image=self.left_imgs["face"][i], height = 32, width=32)
                else:
                    tmp_stats = self.right_imgs["stats"][i]
                    face = Label(stats_window,image=self.right_imgs["face"][i], height = 32, width=32)

                face.grid(column=0, row=i+1)
                for j in range(len(tmp_stats)):
                    tmp_color="azure"
                    if int(tmp_stats[j]) > 79:
                        tmp_color="PaleGreen1"
                    elif int(tmp_stats[j]) < 51:
                        tmp_color="tomato"
                    stats_num = Label(stats_window, text=tmp_stats[j], height =2, width=6, relief=SOLID, bg=tmp_color)
                    stats_num.grid(column=j+1, row=i+1)
        self.stats_win_obj[flag_idx].protocol("WM_DELETE_WINDOW", lambda : self.close_stats_win(flag_idx))
                    
    def close_stats_win(self, idx):
        pos_x = self.stats_win_obj[idx].winfo_rootx()
        pos_y = self.stats_win_obj[idx].winfo_rooty()
        self.stats_win_pos[idx] = [pos_x, pos_y]
        self.stats_win_obj[idx].destroy()
        self.stats_win_obj[idx] = None
                    
    def show_tuning_window(self):
        sub_win = Toplevel()
        sub_win.geometry("300x200")
        sub_win.title('Tuning Window')
        
        tmp_text0 = ttk.Label(sub_win, text="検出枠の位置調整")
        tmp_text1 = ttk.Label(sub_win, text="左右方向（左 : -100 ~ 100 : 右）")
        tmp_text2 = ttk.Label(sub_win, text="上下方向（上 : -100 ~ 100 : 下）")
        tmp_text3 = ttk.Label(sub_win, text="pixel")
        tmp_text4 = ttk.Label(sub_win, text="pixel")
        tb1 = ttk.Entry(sub_win, width=10)
        tb2 = ttk.Entry(sub_win,width=10)
        ref_bt = Button(sub_win, text="反映", command=lambda: self.update_ofst_params(self.is_num(tb1.get()), self.is_num(tb2.get())))
        dump_check = ttk.Checkbutton(sub_win, text="検出枠出力", variable=self.detection_ofs["dump_flag"], onvalue=True, offvalue=False)
        tb1.delete(0, END)
        tb2.delete(0, END)
        tb1.insert(END, str(self.detection_ofs["ofst_x"]))
        tb2.insert(END, str(self.detection_ofs["ofst_y"]))
        
        tmp_text0.grid(column=0, row=0, columnspan=2, sticky=E+W, padx=4, pady=4)
        tmp_text1.grid(column=0, row=1)
        tb1.grid(column=1, row=1)
        tmp_text3.grid(column=2, row=1)
        tmp_text2.grid(column=0, row=2)
        tb2.grid(column=1, row=2)
        tmp_text4.grid(column=2, row=2)
        dump_check.grid(column=0, row=3)
        ref_bt.grid(column=0, row=4)
           
    def update_ofst_params(self, in_x_ofst, in_y_ofst):
        self.detection_ofs["ofst_x"] = in_x_ofst
        self.detection_ofs["ofst_y"] = in_y_ofst
        save_setting_init([str(in_x_ofst), str(in_y_ofst), "True" if self.detection_ofs["dump_flag"].get() else "False", self.detection_ofs["link_var"].get()])
        
    def show_setting_window(self):
        sub_win = Toplevel()
        sub_win.geometry("300x200")
        sub_win.title('Setting Window')
        tmp_text0 = ttk.Label(sub_win, text="使用するリンク先")
        rdb0 = ttk.Radiobutton(sub_win, value="official", variable=self.detection_ofs["link_var"], text='公式Wiki')
        rdb1 = ttk.Radiobutton(sub_win, value="temtetsu", variable=self.detection_ofs["link_var"], text='テムテム対戦データベース')
        ref_bt = Button(sub_win, text="保存", command=lambda: save_setting_init([str(self.detection_ofs["ofst_x"]), str(self.detection_ofs["ofst_y"] ), "True" if self.detection_ofs["dump_flag"].get() else "False", self.detection_ofs["link_var"].get()]))
        tmp_text0.grid(column=0, row=0, columnspan=2, sticky=E+W, padx=4, pady=4)
        rdb0.grid(column=2, row=0)
        rdb1.grid(column=4, row=0)
        
        ref_bt.grid(column=0, row=10,columnspan=6, sticky=E+W, padx=4, pady=4 )

        
    def show_tem_face_window(self, left_flag=True, idx=0):
        return  # 使用不可
        sub_win = Toplevel()
        # get position
        if left_flag:
            tmp_x = str(self.left_obj['face'][idx].winfo_rootx()-300)
            tmp_y = str(self.left_obj['face'][idx].winfo_rooty())
            tmp_name = str(self.left_obj['name'][idx].cget("text"))
        else:
            tmp_x = str(self.right_obj['face'][idx].winfo_rootx())
            tmp_y = str(self.right_obj['face'][idx].winfo_rooty())
            tmp_name = str(self.right_obj['name'][idx].cget("text"))
        
        sub_win.geometry("400x300+"+tmp_x+"+"+tmp_y)
        sub_win.title(tmp_name)
        tem_face_window = Frame(sub_win,width = 400, height=300)
        tem_face_window.pack(fill='both', expand=True)
        
        
        if left_flag:
            tmp_stats = self.left_imgs["stats"][idx]
            face = Label(tem_face_window,image=self.left_imgs["face"][idx], height = 64, width=64)
        else:
            tmp_stats = self.right_imgs["stats"][idx]
            face = Label(tem_face_window,image=self.right_imgs["face"][idx], height = 64, width=64)
        face.grid(column=0, row=0, columnspan=2, rowspan=2, padx=6, pady=6)
        
        # status 
        status_font = font.Font(family='normal', size=9, weight="bold")
        stats_list = ["HP", "STA", "SPD", "ATK", "DEF", "SPATK", "SPDEF"]
        for i in range(len(stats_list)):
            tmp_label = Label(tem_face_window, text=stats_list[i], font=status_font, height = 1, width=5)
            tmp_label.grid(column=i+3, row=0)
        for j in range(len(tmp_stats)):
            tmp_color="azure"
            if int(tmp_stats[j]) > 79:
                tmp_color="PaleGreen1"
            elif int(tmp_stats[j]) < 51:
                tmp_color="tomato"
            stats_num = Label(tem_face_window, text=tmp_stats[j], font=status_font, height = 2, width=5, relief=SOLID, bg=tmp_color)
            stats_num.grid(column=j+3, row=1)
        
        # Trait
        name_font = font.Font(family='normal', size=12, weight="bold")
        disc_font = font.Font(family='normal', size=8)
        trait_name = ['Trait 1', 'Trait 2']
        trait_disc = ['ここは個性1の説明だよ～～～～～～～～～～～～～～～～～～～～～～', 'ここは個性2の説明だよぉぉぉぉぉぉぉぉぉぉぉぉぉぉぉぉぉぉぉ']
        for i in range(len(trait_name)):
            tmp_label = Label(tem_face_window, text=trait_name[i], font=name_font, anchor="w", justify='left', relief=RAISED)
            tmp_label.grid(column=0, row=2+i*6, columnspan=4, sticky=E+W)
            tmp_label = Message(tem_face_window, text=trait_disc[i], font=disc_font, anchor="w", justify='left', relief=SUNKEN)
            tmp_label.grid(column=0, row=4+i*6, columnspan=4, rowspan=2, sticky=E+W)
        
        # Techniques
        
        
        




    
    
