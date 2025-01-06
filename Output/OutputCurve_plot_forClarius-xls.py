# Last modified 20241212

# Copyright (c) Yi, Dong-Joon. All rights reserved.
# iver.ydj@gmail.com
# This code is free for personal and educational use only.
# Commercial use, distribution, or modification of this code is strictly prohibited without explicit permission from the copyright holder.
#
# DISCLAIMER:
# This code is provided "AS IS", without warranty of any kind. The author is not liable for any damages or issues arising from its use.


import xlrd
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
plt.rcParams['figure.dpi'] = 120
import os
import re
from datetime import datetime
now = datetime.now().strftime("%H-%M-%S_%Y%m%d")
current_filename = os.path.basename(__file__)

#######################################################################
data_file = 'OP_ex1.xls'

ApplyAbsolute = True  # for absolute value of current
ApplyLogScale = True  # for log scale of current

mannual_plot = False  # for transfer curve plot (True or False)
if mannual_plot:
    Vd_min = -10
    Vd_max = +10
    Id_min = 1e-12
    Id_max = 1e-3
    figure_size_h = 8
    figure_size_v = 6

Calculate_Symmetry = False 
############################### user input end #################################

directory = f'./result/OutputCurve/{data_file}_{current_filename}_{now}/'
# directory = f'./test/'
print('directory:',directory)
os.makedirs(directory, exist_ok=True)
with open(__file__, 'r', encoding="utf-8") as src, open(f'{directory}wholecode.py', 'w', encoding="utf-8") as dst:
    dst.write(src.read())

data_file = './' + data_file

workbook = xlrd.open_workbook(data_file)
sheet_names = workbook.sheet_names()
data_names = sheet_names[:1]+sheet_names[3:]
settings_sheet = workbook.sheet_by_name('Settings')
settings_df = pd.DataFrame([settings_sheet.row_values(i) for i in range(settings_sheet.nrows)])
data_name_indicies = settings_df[settings_df[0].isin(sheet_names)].index
dividing_indicies = settings_df[settings_df[0].isin(['=================================='])].index
start_dividing_index = dividing_indicies[0::2]
name_dividing_index = dividing_indicies[1::2]

settings_list = []
for i in range(len(data_names)):
    if data_names[i] == settings_df.iloc[data_name_indicies[i], 0]:
        if i < len(data_names)-1:
            selected_data = settings_df.iloc[start_dividing_index[i]:start_dividing_index[i+1], 0:4].values
        else:
            selected_data = settings_df.iloc[start_dividing_index[i]:, 0:4].values
    else:
        raise ValueError('data name not matching')
    settings_list.append(selected_data)
    # print('\n\n\nselected data:',selected_data)
    del selected_data

if len(settings_list) != len(data_names):
    raise ValueError('some data missing')


drainI_list = []
drainV_list = []
gateV_list = []

for i in range(len(data_names)):
    sheet_i = workbook.sheet_by_name(data_names[i])
    data_i = []
    for row_idx in range(sheet_i.nrows):
        row = sheet_i.row_values(row_idx)
        data_i.append(row)
    data_i = np.array(data_i)
    
    match = re.search(r'\((\d+)\)',data_i[0][-1])
    if match:
        num_meas = int(match.group(1))
    else:
        raise ValueError('no number in the last cell of the first row')
    
    drainI_list_j=[]
    drainV_list_j=[]
    gateV_list_j=[]
    for j in range(num_meas):
        idx_drainI_j=np.where(data_i[0]==f'DrainI({j+1})')[0]
        idx_drainV_j=np.where(data_i[0]==f'DrainV({j+1})')[0]
        idx_gateV_j=np.where(data_i[0]==f'GateV({j+1})')[0]
        drainI_list_j.append(np.array(data_i[1:, idx_drainI_j].T,dtype=float))
        drainV_list_j.append(np.array(data_i[1:, idx_drainV_j].T,dtype=float))
        gateV_list_j.append(np.mean(np.array(data_i[1:, idx_gateV_j].T,dtype=float)))
    
    drainI_list.append(drainI_list_j)
    drainV_list.append(drainV_list_j)
    gateV_list.append(gateV_list_j)

for i in range (len(data_names)):
    data_name=data_names[i]
    drainIs =drainI_list[i]
    drainVs =drainV_list[i]
    gateVs = gateV_list[i]
    
    if Calculate_Symmetry:
        def cal_symmetry_score(x, y, x_center=0):
            left_mask = x < x_center
            right_mask = x > x_center
            left_y = y[left_mask]
            right_y = y[right_mask][::-1]
            min_length = min(len(left_y), len(right_y))
            left_y = left_y[:min_length]
            right_y = right_y[:min_length]
            differences = np.square(np.abs(left_y - right_y))
            score = 100 * (1 - np.sqrt(np.mean(differences)) / np.std(y))
            return score
        for j in range(len(gateVs)):
            symm_score_j_list=[]
            symm_score_j = cal_symmetry_score(drainVs[j][0],np.log(np.abs(drainIs[j][0])))
            symm_score_j_list.append(symm_score_j)
        symm_score=np.mean(symm_score_j_list)
    
    plt.figure(figsize=(figure_size_h if mannual_plot else 8, figure_size_v if mannual_plot else 6))
    for j in range(len(gateVs)):
        if ApplyLogScale:
            drainIs[j][0] = np.abs(drainIs[j][0])
            plt.yscale('log')
        # print('drainIs[j]:',drainIs[j][0])
        plt.plot(drainVs[j][0], drainIs[j][0], label=f'$V_g$={gateVs[j]}V')
    plt.legend()
    plt.grid(True)
    if Calculate_Symmetry:
        plt.title(f'Output Characteristics: {data_name} -Symmetry:{np.round(symm_score,2)}%')
    else:
        plt.title(f'Output Characteristics: {data_name}')
    plt.xlabel("Drain Voltage ($V_d$)")
    plt.ylabel("Drain Current ($I_d$)")
    if mannual_plot:
        plt.xlim(Vd_min, Vd_max)
        plt.ylim(Id_min, Id_max)
    plt.ylim(bottom=1e-12)
    plt.tight_layout()
    # plt.show()
    plt.savefig(directory+f'OutputCurve_{data_name}.png', transparent=True)
    plt.cla()   # clear the current axes
    plt.clf()   # clear the current figure
    plt.close() # closes the current figure