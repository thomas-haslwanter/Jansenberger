import numpy as np
import pandas as pd
import os

import winsound
import time

# Get the data
sound_file = r'Resources\ding.wav'
data_dir = 'data'
in_file = '20200307_19-02_ID1_5CRT_0.dat'
df = pd.read_csv(os.path.join(data_dir, in_file), skiprows=4)
acc = df.filter(regex='Acc*')
data = acc.values[:,0]

# Set the parameters
rate = 50

thresholds = np.r_[1.2, 1.4]

hold_time = 1.1
hold_cnt_max = int(hold_time * rate)

# Initialize the loop
counts = 0
hold_cnt = 0
counting = False
threshold_reached = False
max_val_start = data[0]
max_val = max_val_start

for value in data:
    if not counting:
        if value > thresholds[0]:
            counting = True
    else:
        hold_cnt += 1
        if hold_cnt < hold_cnt_max:
            if value > max_val:
                max_val = value
            if (not threshold_reached) and (value > thresholds[1]):
                counts += 1
                winsound.PlaySound(sound_file, winsound.SND_ALIAS)
                threshold_reached = True
        else:
            max_val = max_val_start
            hold_cnt = 0
            counting = False
            threshold_reached = False
    time.sleep(1/rate)
            
            
print(f'Number of hits: {counts}')        
        
            
    