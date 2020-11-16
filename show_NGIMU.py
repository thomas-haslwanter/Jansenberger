"""
This is a demonstration of how to stream data with the NGIMU
Note that you may have to disable the firewall on the computer to see the sensor!
"""

# author:   Thomas Haslwanter
# date:     Dec-2019

from pyqtgraph.Qt import QtGui, QtCore
import numpy as np
import pyqtgraph as pg
import sys
import ngimu
import time
import PySimpleGUI as sg
import pandas as pd


def update(sensor):
    """Update the data in the streaming plot"""
    
    if sensor.streaming:
        # Get the data from the NGIMU
        new_data = sensor.get_data(sensor.channel)
        #print(new_data)
    else:
        new_data = sensor.raw_data[sensor.current, 4:7]
        sensor.current += 1
        if sensor.current == len(sensor.raw_data):
            sys.exit()
            time.sleep(0.001)
                
    # Update the 'data' for the plot, and put them into the corresponding plot-lines
    sensor.data = np.hstack((sensor.data[:,1:], np.c_[new_data]))
    
    for curve, data in zip(sensor.curves, sensor.data):
        curve.setData(data)

        
def load_data():
    """Decide if you want to record or load data"""
    
    layout = [[sg.Text('Do you want to stream sensor data?')],      
                     [sg.Yes(), sg.No()]]    
    window = sg.Window('Input Selection', layout)
    
    event, values = window.read()
    window.close()
    
    streaming = True
    if event == 'No':
        streaming = False
        data_file = sg.popup_get_file('Select your data-file', no_window=True)
        print(data_file)
        data = pd.read_csv(data_file, sep=',', skiprows=3)
        print(data.head())
        
    return (data, streaming)


if __name__=='__main__':
    df, streaming_flag = load_data()
    num_data = 800      # for the display
    
    if streaming_flag:
        # Establish the UDP connection
        # Note that those numbers can change - this has yet to be automated, so that we can select the sensor!
        sensor = ngimu.Sensor(port=8015)
        print(f'IP-address: {sensor.address[0]}')
        print(f'Port: {sensor.address[1]}')
    
    else:
        class Sensor():
            def __init__(self, data, ptr):
                self.raw_data = data
                self.current = 1
        
        sensor = Sensor(df.values, num_data)                
        
    # Set up the PyQtGraph GUI
    app = QtGui.QApplication([])
    win = pg.GraphicsLayoutWidget(show=True, title='NGIMU')

    win.resize(1000, 600)
    win.setWindowTitle('Data Viewer')

    # Enable antialiasing for prettier plots
    pg.setConfigOptions(antialias=False)

    ph = win.addPlot(title='Streaming Plot')
    ph.enableAutoRange('xy', True)
    
    # Initialize the plot
    curves = [ ph.plot(pen='y', label='x'),
              ph.plot(pen='r', label='y'),
              ph.plot(pen='g', label='z') ]
    
    sensor.curves = curves
    sensor.ptr = num_data
    sensor.data = np.zeros( (3, num_data) )
    sensor.channel = 'acc'
    sensor.streaming = streaming_flag
    
    # Timer for updating the display
    timer = QtCore.QTimer()
    timer.timeout.connect(lambda: update(sensor))
    timer.start(10)                  

    # Eventloop
    QtGui.QApplication.instance().exec_()

