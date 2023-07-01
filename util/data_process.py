import numpy as np
import csv

class data_processor():
    def __init__(self):
        self.type_table = self.load_type_table()

    def load_type_table(self):
        csv_file = "./data/type.csv"
        type_table=None
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            type_table = [row for row in reader]
        return type_table

    def calc_type_res(self, type1 = "Neutral", type2 = None):

        type1_idx = self.type_table[0].index(type1)
        type1_res = [row[type1_idx] for row in self.type_table][1:]
        type1_res_float = [float(i) for i in type1_res]
        out_res_float = np.array(type1_res_float)
        if type2 is not None:
            type2_idx = self.type_table[0].index(type2)
            type2_res = [row[type2_idx] for row in self.type_table][1:]
            type2_res_float = [float(i) for i in type2_res]
            out_res_float *= np.array(type2_res_float)
        
        out_res = [str(int(i)) if i >= 1. else str(i) for i in out_res_float]
        return out_res\
    
    def get_type_name(self):
        return self.type_table[0][1:]

def get_setting_init():
    ofst_x = 0
    ofst_y = 0
    dump_flag = False
    link_var = "official"
    with open("./data/ofst.ini", "r") as f:
        line = f.readlines()
        ofst_x = line[0].replace('\n', "")
        ofst_y = line[1].replace('\n', "")
        dump_flag = True if line[2].replace('\n', "") == "True" else False
        link_var = line[3].replace('\n', "")
    return [int(ofst_x), int(ofst_y), dump_flag, link_var]
    
def save_setting_init(tmp_list):
    with open("./data/ofst.ini", "w") as f:
        for i in tmp_list:
            f.write(i+'\n')
    return 
