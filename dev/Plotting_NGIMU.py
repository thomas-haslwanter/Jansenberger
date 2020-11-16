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
import osc_decoder
import socket

def update(selection='quat'):
    """Update the data in the streaming plot"""
    global curve, data, ph, udp_sockets, quat
    
    # Get the data from the NGIMU
    try:
        UDP_data, addr = udp_socket.recvfrom(2048)
    except socket.error:
        pass
    else:
        for message in osc_decoder.decode(UDP_data):
            print(message)
            if selection == 'acc':
                if message[1] == '/sensor':
                    new_data = message[5:8]                   
            else:
                # Extract the quaternion
                if message[1] == '/quaternion':
                    # For the moment, only show the quaternion-vector
                    new_data = message[2:]                   
                
    # Update the 'data' for the plot, and put them into the corresponding plot-lines
    # select: acc / gyr / mag / quat
    selection = 'acc'
    
    if selection == 'quat':
        data = np.vstack((data[1:,:], new_data))
    elif selection == 'acc':
        data = np.vstack((data[1:,:], new_data))
    
    curve[0].setData(data[:,0])
    curve[1].setData(data[:,1])
    curve[2].setData(data[:,2])


if __name__=='__main__':
    # Establish the UDP connection
    # Note that those numbers can change - this has yet to be automated, so that we can select the sensor!
    udp_ports = [9000, 8015]
    udp_sockets = [socket.socket(socket.AF_INET, socket.SOCK_DGRAM) for _ in range(len(udp_ports))]
    
    for (index, udp_socket) in enumerate(udp_sockets):
        udp_socket.bind(("", udp_ports[index]))
        # index = index + 1
        udp_socket.setblocking(False)

    # Set up the PyQtGraph GUI
    app = QtGui.QApplication([])
    win = pg.GraphicsLayoutWidget(show=True, title='NGIMU')

    num_data = 800
    win.resize(1000, 600)
    win.setWindowTitle('Data Viewer')

    # Enable antialiasing for prettier plots
    pg.setConfigOptions(antialias=False)

    ph = win.addPlot(title='Streaming Plot')
    ph.enableAutoRange('xy', True)
    curve = [ ph.plot(pen='y', label='x'),
              ph.plot(pen='r', label='y'),
              ph.plot(pen='g', label='z') ]
    
    # Initial values
    data = np.zeros( (num_data, 3) ) 

    # Timer for updating the display
    timer = QtCore.QTimer()
    timer.timeout.connect(update)
    timer.start(10)                  # 10 msec

    # Eventloop
    QtGui.QApplication.instance().exec_()

