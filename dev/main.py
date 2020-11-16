# -*- coding: utf-8 -*-
"""
Various methods of drawing scrolling plots.
"""
#import initExample  ## Add path to library (just for examples; you do not need this)

import pyqtgraph as pg
from pyqtgraph.Qt import QtCore
from PyQt5 import QtGui
from PyQt5.QtWidgets import QApplication
import numpy as np
import argparse
import math
import time
from pythonosc import dispatcher
from pythonosc import osc_server
from pythonosc.osc_server import AsyncIOOSCUDPServer
from pythonosc.dispatcher import Dispatcher
import asyncio


win = pg.GraphicsLayoutWidget(show=True)
win.setWindowTitle('pyqtgraph example: Scrolling Plots')

async def loop():
    """Example main loop that only runs for 10 iterations before finishing"""
    #print(i)
    await asyncio.sleep(0.001)



async def init_main():
    server = AsyncIOOSCUDPServer((args.ip, args.port), dispatcher, asyncio.get_event_loop())
    transport, protocol = await server.create_serve_endpoint()  # Create datagram endpoint and start serving

    await loop()  # Enter main loop of program
    transport.close()  # Clean up serve endpoint


# 3) Plot in chunks, adding one new plot curve for every 100 samples
chunkSize = 100
# Remove chunks after we have 10
maxChunks = 10
startTime = pg.ptime.time()
p5 = win.addPlot(colspan=2)
p5.setLabel('bottom', 'Time', 's')
p5.setXRange(-10, 0)
curves = []
data5 = np.empty((chunkSize + 1, 2))
ptr5 = 0




def update3(a,b,c,d,e):
    global quatx, quaty, quatz, quatk
    quatx = b
    quaty = c
    quatz = d
    quatk = e

    global p5, data5, ptr5, curves
    print(quatz)
    now = pg.ptime.time()
    for c in curves:
        c.setPos(-(now - startTime), 0)

    i = ptr5 % chunkSize
    if i == 0:
        curve = p5.plot()
        curves.append(curve)
        last = data5[-1]
        data5 = np.empty((chunkSize + 1, 2))
        data5[0] = last
        while len(curves) > maxChunks:
            c = curves.pop(0)
            p5.removeItem(c)
    else:
        curve = curves[-1]
    data5[i + 1, 0] = now - startTime
    data5[i + 1, 1] = quatz
    curve.setData(x=data5[:i + 2, 0], y=data5[:i + 2, 1])
    ptr5 += 1



def main_loop():
        asyncio.run(init_main())
# update all plots
def update():
    #asyncio.sleep(1)
    update3()


timer = pg.QtCore.QTimer()
timer.timeout.connect(main_loop)
timer.start(10)

## Start Qt event loop unless running in interactive mode or using pyside.
if __name__ == '__main__':
    quatx=0
    quaty=0
    quatz=0
    quatk=0
    import sys

    parser = argparse.ArgumentParser()
    parser.add_argument("--ip", default="0.0.0.0", help="The ip to listen on")
    parser.add_argument("--port",
                        type=int, default=8001, help="The port to listen on")
    args = parser.parse_args()
    f = open("testfile_1.txt", "a+")
    dispatcher = dispatcher.Dispatcher()
    # dispatcher.map("/sensors",)

    dispatcher.map("/quaternion", update3)
    # dispatcher.map("/battery", some_printing) # pyqtgraph scrolling plots

    # Each incoming packet will be handled in its own thread //added
    # server = osc_server.ThreadingOSCUDPServer(
    #    (args.ip, args.port), dispatcher)


    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QApplication.instance().exec_()
        
        
        
