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

def update(sensor):
    """Update the data in the streaming plot"""
    
    # Get the data from the NGIMU
    new_data = sensor.get_data(sensor.channel)
    #print(new_data)
                
    # Update the 'data' for the plot, and put them into the corresponding plot-lines
    sensor.data = np.hstack((sensor.data[:,1:], np.c_[new_data]))
    
    for curve, data in zip(sensor.curves, sensor.data):
        curve.setData(data)


if __name__=='__main__':
    # Establish the UDP connection
    # Note that those numbers can change - this has yet to be automated, so that we can select the sensor!
    sensor = ngimu.Sensor()
    print(f'IP-address: {sensor.address[0]}')
    print(f'Port: {sensor.address[1]}')

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
    num_data = 800
    sensor.data = np.zeros( (3, num_data) )
    sensor.channel = 'acc'
    
    curves = [ ph.plot(pen='y', label='x'),
              ph.plot(pen='r', label='y'),
              ph.plot(pen='g', label='z') ]
    
    sensor.curves = curves

    # Timer for updating the display
    timer = QtCore.QTimer()
    timer.timeout.connect(lambda: update(sensor))
    timer.start(10)                  

    # Eventloop
    QtGui.QApplication.instance().exec_()

