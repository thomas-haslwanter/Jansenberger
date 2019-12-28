"""
Testfile for a PyQt5 Menubar
"""

# author: Markus Pruckner & Thomas Haslwanter
# date:   Dec-2019 

import os
import sys
import time
import re
import numpy as np
import pandas as pd
import datetime

import pyqtgraph as pg
from PyQt5 import QtWidgets, QtGui, QtCore, QtMultimedia

import ngimu


class Sensor():
    """Default settings for the recording"""
    
    def __init__(self):
        """Initialize the sensor"""
        
        self.labels = ['Acceleration [g]',
                       'Angular Velocity [deg/s]']
        self.range = [ [-1.2, 1.2],
                       [-100, 100] ]
        self.channel = 'acc'   # can be 'acc' or 'gyr'
        self.rate = 50      # Hz
        self.IP = '0.0.0.0'
        self.port = 8015
        

class MainWindow(QtWidgets.QMainWindow):
    """ The central display Widget """    

    
    def __init__(self):
        ''' Define style of the main window '''
                
        super(MainWindow, self).__init__()
        self.setGeometry(50, 50, 500, 300)
        self.showMaximized()
        self.setWindowTitle("Jansenberger")
        self.setWindowIcon(QtGui.QIcon('C:/Users/maxpr_000/Desktop/Berufspraktikum/Coding/Jansenberger.jpg'))
        
        # Show the line-window
        self.set_window()
            
        # Filling up a menu bar
        bar = self.menuBar()
        # File menu
        display_menu = bar.addMenu('Anzeigeart')
        # adding actions to file menu
        trafficLight_action = QtWidgets.QAction('Ampel', self)
        linePlot_action = QtWidgets.QAction('Liniendiagramm', self)
        grid_action = QtWidgets.QAction('Raster', self)
        store_action = QtWidgets.QAction('Speichern', self)
        display_menu.addAction(trafficLight_action)
        display_menu.addAction(linePlot_action)
        display_menu.addAction(grid_action)
        display_menu.addAction(store_action)
        
        # Set shortcuts
        trafficLight_action.setShortcut("Ctrl+A")
        linePlot_action.setShortcut("Ctrl+L")
        grid_action.setShortcut("Ctrl+R")
        store_action.setShortcut("Ctrl+S")

        # Use `connect` method to bind signals to desired behavior
        linePlot_action.triggered.connect(lambda: self.set_window(win_type='line'))
        trafficLight_action.triggered.connect(lambda: self.set_window(win_type='light'))
        grid_action.triggered.connect(lambda: self.set_window(win_type='grid'))
        store_action.triggered.connect(lambda: self.set_window(win_type='store'))
        
        
    def set_window(self, win_type = 'line'):
        """
        Shows only the selected window in the central widget

        Parameter
        ---------
        win_type : string
                Has to be 'line', 'light', 'grid', or 'store'
        """
        
        # types = ['line', 'light', 'grid', 'store']

        if win_type == 'light':
            self.setCentralWidget(trafficLight())
        elif win_type == 'line':
            self.setCentralWidget(linePlotWindow())
        elif win_type == 'grid':
            self.setCentralWidget(gridWindow())
        else:
            self.setCentralWidget(storeWindow())

    
    def closeEvent(self, event):
        ''' React to window closing '''
        box = QtGui.QMessageBox()
        box.setWindowTitle('Jansenberger')
        box.setText('Anwendung wirklich beenden?')
        box.setStandardButtons(QtGui.QMessageBox.Yes|QtGui.QMessageBox.No)
        buttonY = box.button(QtGui.QMessageBox.Yes)
        buttonY.setText('Ja')
        buttonN = box.button(QtGui.QMessageBox.No)
        buttonN.setText('Nein')
        box.exec_()
        
        if box.clickedButton() == buttonY:
            event.accept()
            device1.accelerometer.notifications(None)
            if deviceFlag == True:
                device2.accelerometer.notifications(None)
            device1.gyroscope.notifications(None)
            time.sleep(3.0)
            print('Unsubscribed from notifications...')
            device1.disconnect()
            print('\nWindow closed')
        elif box.clickedButton() == buttonN:
            event.ignore()


class trafficLight(QtWidgets.QWidget):
    """ Show signals as a simple 'traffic-light' """    


    def __init__(self):
        """Initialize the traffic-light window"""
        
        super(trafficLight, self).__init__()
        self.initUI()
        
        # flag for swapping lightcolors
        self.swapFlag = False
        
        # Define a buffer to save the data
        row = 7500  # sample_rate (25 Hz) x time (5 min)
        col = 3     # 3 signals from accelerometer or 3 from gyroscope
        self.buffer = np.nan * np.ones((row, col))
        self.ii = 0
        
        # Create name for the outfile by defining the current date and time
        self.outfileAcc = datetime.datetime.now().strftime("%b%d%Y_%H-%M-%S_Acc")
        self.outfileGyr = datetime.datetime.now().strftime("%b%d%Y_%H-%M-%S_Gyr")


    def initUI(self):      
        """ Define the display size, title, and colors, and the initial color """
        
        self.setGeometry(300, 300, 350, 100)
        
        # Set layout to a QGridLayout, so you only need to define row and column
        self.layout = QtWidgets.QGridLayout()
        self.setLayout(self.layout)

        # Define width of several columns
        self.layout.setColumnStretch(0, 1)
        self.layout.setColumnStretch(1, 2)
        self.layout.setColumnStretch(2, 1)

        self.btnStop = QtGui.QPushButton('Stopp')
        self.layout.addWidget(self.btnStop, 0,0)
        self.btnStop.clicked.connect(self.stopStreaming)
        
        # Create a drop down menu
        self.cbox = QtGui.QComboBox()
        self.cbox.addItems(['X', 'Y', 'Z'])
        self.layout.addWidget(self.cbox, 1,0)
        
        self.check_save = QtWidgets.QCheckBox('Daten speichern')
        self.layout.addWidget(self.check_save, 5,0) 
        self.check_save.stateChanged.connect(self.checked)
        
        self.cbox = QtWidgets.QComboBox()
        self.cbox.addItems(['bitte waehlen', 'Accelerometer', 'Gyroscope'])
        self.layout.addWidget(self.cbox, 2,2)
        self.cbox.currentIndexChanged.connect(self.selectionChange)
        
        self.check_swap = QtWidgets.QCheckBox('Ampel umkehren')
        self.layout.addWidget(self.check_swap, 1,1)
        self.check_swap.stateChanged.connect(self.swapLights)
        
        self.thres1 = QtWidgets.QLineEdit('obere Schwelle')
        self.thres2 = QtWidgets.QLineEdit('untere Schwelle')
        self.layout.addWidget(self.thres1, 3,0)
        self.layout.addWidget(self.thres2, 4,0)
        self.thres1.textChanged.connect(self.upperThresChanged)
        self.thres2.textChanged.connect(self.lowerThresChanged)
        
        # define colors by giving RGB-values instead of QtCore.Qt.red/yellow/green
        # https://stampinblog.de/stampin-up/rgb-und-hex-farbcode-fuer-die-neuen-in-color-2017-2019-9730/
        self.colors = [QtGui.QColor(198, 44, 58), QtGui.QColor(254, 197, 45), QtGui.QColor(86, 174, 53)]
        self.colorNr = 1  # set the starting color to the second (0,1,2) element of self.colors   
        self.show()


    def upperThresChanged(self, text):
        """Define the upper threshold"""
        
        self.upperThreshold = float(text)


    def lowerThresChanged(self, text):
        """Define the lower threshold"""
        
        self.lowerThreshold = float(text)


    def paintEvent(self, e):
        """
        'paintEvent' is a method of each QWidget, and is used to
        re-paint the Widget
        """
        
        qp = QtGui.QPainter()
        qp.begin(self)
        qp.setPen(QtGui.QColor(QtCore.Qt.black))
        qp.drawRect(845, 115, 240, 210)
        qp.drawRect(845, 350, 240, 210)
        qp.drawRect(845, 585, 240, 210)
        self.drawRectangles(qp)
        qp.end()


    def drawRectangles(self, qp):
        """ Here three rectangles are drawn """
        
        lightColor = self.colors[self.colorNr]
        qp.setBrush(lightColor)
        
        if self.swapFlag == False:
            if self.colorNr == 0:
                qp.drawRect(845, 115, 240, 210)
                QtMultimedia.QSound.play("C:/Users/maxpr_000/Desktop/Berufspraktikum/Coding/button-37.wav")
            elif self.colorNr == 1:   
                qp.drawRect(845, 350, 240, 210)
            else:
                qp.drawRect(845, 585, 240, 210)
        else:
            if self.colorNr == 0:
                qp.drawRect(845, 585, 240, 210)
            elif self.colorNr == 1:   
                qp.drawRect(845, 350, 240, 210)
            else:
                qp.drawRect(845, 115, 240, 210)
                QtMultimedia.QSound.play("C:/Users/maxpr_000/Desktop/Berufspraktikum/Coding/button-37.wav")


    def selectionChange(self, i):
        ''' choose what data to measure '''
        
        print(self.cbox.itemText(i))
        self.sensor = self.cbox.itemText(i)
        if self.sensor == 'Accelerometer':
            self.btn = QtGui.QPushButton('Start')
            self.layout.addWidget(self.btn, 2,0)
            self.btn.clicked.connect(self.startAccStreaming)
            self.btn.clicked.connect(self.btn.deleteLater)
        elif self.sensor == 'Gyroscope':
            self.btn = QtGui.QPushButton('Start')
            self.layout.addWidget(self.btn, 2,0)
            self.btn.clicked.connect(self.startGyroStreaming)
            self.btn.clicked.connect(self.btn.deleteLater)
        else:
            print('No sensor selected...')


    def checked(self):
        ''' Open a dialog if "Save" is checked '''
        
        if self.check_save.isChecked():
            self.searchForDirectory()


    def searchForDirectory(self):
        ''' Create a file dialog for saving the data '''
        
        self.dirPath = QtGui.QFileDialog.getExistingDirectory(
            self,
            "Open a folder",
            "/home/my_user_name/",
            QtGui.QFileDialog.ShowDirsOnly
            )

    def swapLights(self):
        ''' If checked, swap the lightcolors red and green '''
        
        if self.check_swap.isChecked():
            self.swapFlag = True
        else:
            self.swapFlag = False

    def startAccStreaming(self):
        ''' stream data from accelerometer '''
        
        # Subscribe to notifications to get the data (until callback=None)
        device1.accelerometer.set_settings(data_rate=50)
        self.connect_and_start()
        self.p1.setLabel('left','Beschleunigung in g')
        self.p1.setTitle('Beschleunigungsmessung')


    def startGyroStreaming(self):
        ''' stream data from gyroscope '''
        
        self.connect_and_start()
        self.p1.setLabel('left','Winkelgeschwindigkeit  in °/s')
        self.p1.setTitle('Winkelgeschwindigkeitsmessung')


    def stopStreaming(self):
        ''' Stop data streaming after 'Stop' is clicked '''
        
        self.timerStop()
        device1.accelerometer.notifications(None)
        device1.gyroscope.notifications(None)
        time.sleep(3.0)
        print('Unsubscribed from notifications...')
        if self.check_save.isChecked():
            self.df = self.df[pd.notnull(self.df['X-data'])]  # Remove empty rows
            os.chdir(self.dirPath)
            if self.sensor == 'Accelerometer':
                self.df.to_csv(self.outfileAcc, sep='\t')
            else:
                self.df.to_csv(self.outfileGyr, sep='\t')
            
            print('\nData saved to ', self.dirPath)


    def connect_and_start(self):
        """ Connects the signals, and starts the timer
        Note: Qt signals can only be connected to instances, and not to
        pure classes!
        """
        
        self.timer = QtCore.QTimer()
        self.time = QtCore.QTime(0, 0, 0)
        
        self.timer.timeout.connect(self.timerEvent)
        self.timer.start(200)    


    def timerEvent(self):
        """ Every few msec, check the signal, and set the color of the
        rectangle accordingly. 
        the 'update' calls the 'paintEvent'
        """
        
        def stream_data(data):
            # take the signal from a sensor
            line = str(data)
            values = re.split('[:,}]', line)
        
            x_data = float(values[4]) * 1000  # converted into mG
            y_data = float(values[6]) * 1000
            z_data = float(values[8]) * 1000
            
            self.current = np.hstack((x_data,y_data,z_data))
            self.buffer[self.ii] = self.current
            self.df = pd.DataFrame(self.buffer)
            self.df.columns = ['X-data', 'Y-data', 'Z-data']
            self.ii += 1
            
            if self.cbox.currentText() == 'X':
                mySignal = x_data 
            elif self.cbox.currentText() == 'Y':
                mySignal = y_data
            else:
                mySignal = z_data
            
            if mySignal > self.upperThreshold:
                if self.colorNr is not 0:
                    self.colorNr = 0
                    self.update()
            elif mySignal > self.lowerThreshold:
                if self.colorNr is not 1:
                    self.colorNr = 1
                    self.update()
            else:
                if self.colorNr is not 2:
                    self.colorNr = 2
                    self.update()
        if self.sensor == 'Accelerometer':
            device1.accelerometer.notifications(stream_data)
        else:
            device1.gyroscope.notifications(stream_data)


    def timerStop(self):
        ''' Stop the timer when trafficLight should be stopped '''
        
        self.timer.stop()


class linePlotWindow(pg.GraphicsWindow):
    """ Window showing signals as a function of time """


    def __init__(self, sensor):
        """Initializ the line-window"""
        
        super(linePlotWindow, self).__init__()
        self.initUI()
        
        # Initialize the plot
        num_data = 800
        sensor.data = np.zeros( (3, num_data) )
        sensor.channel = 'acc'
        
        curves = [ ph.plot(pen='y', label='x'),
                  ph.plot(pen='r', label='y'),
                  ph.plot(pen='g', label='z') ]
        
        sensor.curves = curves
        
        
        # Define a buffer to save the data
        row = 135000  # sample_rate (50 Hz) x time (45 min)
        col = 3     # 3 signals from accelerometer and 3 from gyroscope
        self.buffer = np.nan * np.ones((row, col))
        self.ii = 0
        
        # Define a second buffer if 2 devices selected
        row = 135000  # sample_rate (50 Hz) x time (45 min)
        col = 3     # 3 signals from accelerometer and 3 from gyroscope
        self.buffer2 = np.nan * np.ones((row, col))
        self.jj = 0
        
        # Create name for the outfile by defining the current date and time
        self.outfileAcc = datetime.datetime.now().strftime("%b%d%Y_%H-%M-%S_Acc")
        self.outfileGyr = datetime.datetime.now().strftime("%b%d%Y_%H-%M-%S_Gyr")
        
        self.outfileAcc2 = datetime.datetime.now().strftime("%b%d%Y_%H-%M-%S_Acc2")
        self.outfileGyr2 = datetime.datetime.now().strftime("%b%d%Y_%H-%M-%S_Gyr2")


    def initUI(self):
        ''' Define display style '''
        
        self.showMaximized()
        self.setBackground(None)
        
        # Set layout to a QGridLayout, so you only need to define row and column
        self.layout = QtWidgets.QGridLayout()
        self.setLayout(self.layout)

        # Add Widgets to the layout    
        self.btnStop = QtGui.QPushButton('Stopp')
        self.btnStop.clicked.connect(self.stopStreaming)
        self.layout.addWidget(self.btnStop, 0,0)
        
        self.check = QtWidgets.QCheckBox('Daten speichern')
        self.check.stateChanged.connect(self.checked)
        self.layout.addWidget(self.check, 2,0) 
          
        self.cbox = QtWidgets.QComboBox()
        self.cbox.addItems(['bitte waehlen', 'Accelerometer', 'Gyroscope'])
        self.layout.addWidget(self.cbox, 2,2)
        self.cbox.currentIndexChanged.connect(self.selectionChange)
        
        self.layout.addWidget(QtWidgets.QLabel('Messung:'), 1,2) 
        
        # Create a plot with a legend next to it
        self.p1 = pg.plot()
        self.p1.win.hide()
        self.p1.showGrid(x=True, y=True)
        self.p1.setLabel('bottom','Zeit')
        
        # Create a curve to plot
        self.curveX = self.p1.plot(pen='r')                       
        self.curveY = self.p1.plot(pen='g')
        self.curveZ = self.p1.plot(pen='c')
        
        self.vb = self.addViewBox()  # Empty box next to the plot
        self.vb.setMaximumWidth(3000)
        self.legend = pg.LegendItem()
        self.legend.setParentItem(self.vb)
        
        self.legend.addItem(self.curveX, 'x-data')
        self.legend.addItem(self.curveY, 'y-data')
        self.legend.addItem(self.curveZ, 'z-data')
        
        # Anchor the upper-left corner of the legend to the upper-left corner of its parent
        self.legend.anchor((-24.5,0),(0,0))
        
        # Add the plot to the window
        self.layout.addWidget(self.p1, 0,1)
        
        # Define width of several columns
        self.layout.setColumnStretch(1, 3)


    def selectionChange(self, i):
        ''' choose what data to measure '''
        
        print(self.cbox.itemText(i))
        self.sensor = self.cbox.itemText(i)
        if self.sensor == 'Accelerometer':
            self.btn = QtGui.QPushButton('Start')
            self.layout.addWidget(self.btn, 1,0)
            self.btn.clicked.connect(self.startAccStreaming)
            self.btn.clicked.connect(self.btn.deleteLater)  # delete Start btn
        elif self.sensor == 'Gyroscope':
            self.btn = QtGui.QPushButton('Start')
            self.layout.addWidget(self.btn, 1,0)
            self.btn.clicked.connect(self.startGyroStreaming)
            self.btn.clicked.connect(self.btn.deleteLater)
        else:
            print('No sensor selected...')
    
    def checked(self):
        ''' Open a dialog if "Save" is checked '''
        if self.check.isChecked():
            self.searchForDirectory()
     
    def searchForDirectory(self):
        ''' Create a file dialog for saving the data '''
        self.dirPath = QtGui.QFileDialog.getExistingDirectory(
            self,
            "Open a folder",
            "/home/my_user_name/",
            QtGui.QFileDialog.ShowDirsOnly
            )


    def startAccStreaming(self):
        ''' stream data from accelerometer '''
        
        # Subscribe to notifications to get the data (until callback=None)
        device1.accelerometer.set_settings(data_rate=50)
        device1.accelerometer.notifications(self.streamingData1)
        
        if deviceFlag == True:
            device2.accelerometer.set_settings(data_rate=50)
            device2.accelerometer.notifications(self.streamingData2)
            
        self.p1.setLabel('left','Beschleunigung in g')
        self.p1.setTitle('Beschleunigungsmessung')


    def startGyroStreaming(self):
        ''' stream data from gyroscope '''
        
        device1.gyroscope.notifications(self.streamingData)
        self.p1.setLabel('left','Winkelgeschwindigkeit  in °/s')
        self.p1.setTitle('Winkelgeschwindigkeitsmessung')


    def stopStreaming(self):
        ''' Stop data streaming after 'Stop' is clicked '''
        
        device1.accelerometer.notifications(None)
        device1.gyroscope.notifications(None)
        if deviceFlag == True:
            device2.accelerometer.notifications(None)
        time.sleep(3.0)
        print('Unsubscribed from notifications...')
        if self.check.isChecked():
            self.df = self.df[pd.notnull(self.df['X-data'])]  # Remove empty rows
            os.chdir(self.dirPath)
            if self.sensor == 'Accelerometer':
                self.df.to_csv(self.outfileAcc, sep='\t')
                if deviceFlag == True:
                    self.df2 = self.df2[pd.notnull(self.df2['X-data'])]  # Remove empty rows
                    self.df2.to_csv(self.outfileAcc2, sep='\t')
            else:
                self.df.to_csv(self.outfileGyr, sep='\t')
            
            print('\nData saved to ', self.dirPath)


    def streamingData1(self, data):
        ''' Plot sensor data in realtime
        
        Each time this function is called, the data display is updated
        '''        
        self.Xmx[:-1] = self.Xmx[1:]          # shift data in the temporal mean 1 sample left
        self.Xmy[:-1] = self.Xmy[1:]
        self.Xmz[:-1] = self.Xmz[1:]
        
        line = str(data)
        values = re.split('[:,}]', line)      # split the string to get the values
        
        x_data = float(values[4])
        y_data = float(values[6])
        z_data = float(values[8])
        
        self.current = np.hstack((x_data,y_data,z_data))
        self.buffer[self.ii] = self.current
        self.df = pd.DataFrame(self.buffer)
        self.df.columns = ['X-data', 'Y-data', 'Z-data']
        self.ii += 1
        
        self.Xmx[-1] = x_data               # vector containing the instantaneous values      
        self.Xmy[-1] = y_data
        self.Xmz[-1] = z_data
        
        self.ptr += 1                              # update x position for displaying the curve
        
        self.curveX.setData(self.Xmx)              # set the curve with this data
        self.curveX.setPos(self.ptr, 0)            # set x position in the graph to 0
        self.curveY.setData(self.Xmy)
        self.curveY.setPos(self.ptr, 0)
        self.curveZ.setData(self.Xmz)
        self.curveZ.setPos(self.ptr, 0)
        
        QtWidgets.QApplication.processEvents()    # process the plot


    def streamingData2(self, data):
        ''' Plot sensor data in realtime
        Each time this function is called, the data display is updated
        '''        
        
        line = str(data)
        values = re.split('[:,}]', line)      # split the string to get the values
        
        x_data = float(values[4])
        y_data = float(values[6])
        z_data = float(values[8])
        
        self.current2 = np.hstack((x_data,y_data,z_data))
        self.buffer2[self.jj] = self.current2
        self.df2 = pd.DataFrame(self.buffer2)
        self.df2.columns = ['X-data', 'Y-data', 'Z-data']
        self.jj += 1


class gridWindow(pg.GraphicsWindow):
    """ Show two components versus each other """
    
    def __init__(self):
        """Initialize the grid window"""
        
        super(gridWindow, self).__init__()
        self.initUI()
        
        # Define a buffer to save the data
        row = 7500  # sample_rate (25 Hz) x time (5 min)
        col = 3     # 3 signals from accelerometer or 3 from gyroscope
        self.buffer = np.nan * np.ones((row, col))
        self.ii = 0
        
        # Create name for the outfile by defining the current date and time
        self.outfileAcc = datetime.datetime.now().strftime("%b%d%Y_%H-%M-%S_Acc")
        self.outfileGyr = datetime.datetime.now().strftime("%b%d%Y_%H-%M-%S_Gyr")


    def initUI(self):
        """ Define display style """
        
        self.showMaximized()
        self.setBackground(None)
        
        # Set layout to a QGridLayout, so you only need to define row and column
        self.layout = QtWidgets.QGridLayout()
        self.setLayout(self.layout)
        
        self.btnStop = QtGui.QPushButton('Stop')
        self.layout.addWidget(self.btnStop, 0,0)
        self.btnStop.clicked.connect(self.stopStreaming)
        
        self.save = QtWidgets.QCheckBox('Daten speichern')
        self.layout.addWidget(self.save, 2,0) 
        self.save.stateChanged.connect(self.checked)
        
        self.Xmax = QtWidgets.QLineEdit('X-Limit')
        self.Ymax = QtWidgets.QLineEdit('Y-Limit')
        self.layout.addWidget(self.Xmax, 3,0)
        self.layout.addWidget(self.Ymax, 4,0)
        self.Xmax.textChanged.connect(self.xLimit)
        self.Ymax.textChanged.connect(self.yLimit)
        
        self.cbox = QtWidgets.QComboBox()
        self.cbox.addItems(['bitte waehlen', 'Accelerometer', 'Gyroscope'])
        self.layout.addWidget(self.cbox, 2,2)
        self.cbox.currentIndexChanged.connect(self.selectionChange)        
        
        # Create a plot with a legend next to it
        self.plot = pg.plot()
        self.plot.win.hide()
        self.plot.showGrid(x=True, y=True)
        self.plot.setXRange(-2200,2200)
        self.plot.setYRange(-2200,2200)
        
        # Create a curve to plot
        self.graph = self.plot.plot()                       
        
        self.windowWidth = 1
        self.Xmx = np.linspace(0, 0, self.windowWidth)    # Create array that will contain the relevant time series     
        self.Xmy = np.linspace(0, 0, self.windowWidth)
        self.ptr = -self.windowWidth                      # Set first x position
        
        # Add the plot to the window
        self.layout.addWidget(self.plot, 0,1)
        
        # Define width of several columns
        self.layout.setColumnStretch(1, 3)


    def selectionChange(self, i):
        """ choose what data to measure """
        
        print(self.cbox.itemText(i))
        self.sensor = self.cbox.itemText(i)
        if self.sensor == 'Accelerometer':
            self.btn = QtGui.QPushButton('Start')
            self.layout.addWidget(self.btn, 1,0)
            self.btn.clicked.connect(self.startAccStreaming)
            self.btn.clicked.connect(self.btn.deleteLater)
        elif self.sensor == 'Gyroscope':
            self.btn = QtGui.QPushButton('Start')
            self.layout.addWidget(self.btn, 1,0)
            self.btn.clicked.connect(self.startGyroStreaming)
            self.btn.clicked.connect(self.btn.deleteLater)
        else:
            print('No sensor selected...')

    def checked(self):
        """ Open a dialog if "Save" is checked """
        
        if self.check.isChecked():
            self.searchForDirectory()


    def searchForDirectory(self):
        """ Create a file dialog for saving the data """
        
        self.dirPath = QtGui.QFileDialog.getExistingDirectory(
            self,
            "Open a folder",
            "/home/my_user_name/",
            QtGui.QFileDialog.ShowDirsOnly
            )


    def xLimit(self, text):
        """ Set the x-limit """
        
        self.xLim = float(text)


    def yLimit(self, text):
        """ Set the y-limit """
        
        self.yLim = float(text)


    def startAccStreaming(self):
        """ stream data from accelerometer """
        
        # Subscribe to notifications to get the data (until callback=None)
        device1.accelerometer.set_settings(data_rate=12.5)
        device1.accelerometer.notifications(self.streamingData)
        self.plot.setTitle('Beschleunigungsmessung')


    def startGyroStreaming(self):
        """ stream data from gyroscope """
        
        device1.gyroscope.notifications(self.streamingData)
        self.plot.setTitle('Winkelgeschwindigkeitsmessung')


    def stopStreaming(self):
        """ Stop data streaming after 'Stop' is clicked """
        
        device1.accelerometer.notifications(None)
        device1.gyroscope.notifications(None)
        time.sleep(3.0)
        print('Unsubscribed from notifications...')
        if self.check.isChecked():
            self.df = self.df[pd.notnull(self.df['X-data'])]  # Remove empty rows
            os.chdir(self.dirPath)
            if self.sensor == 'Accelerometer':
                self.df.to_csv(self.outfileAcc, sep='\t')
            else:
                self.df.to_csv(self.outfileGyr, sep='\t')
            
            print('\nData saved to ', self.dirPath)
        
#        self.plot.clear() # clear the plot for the next run


    def streamingData(self, data):
        """ Plot sensor data in realtime
        
        Each time this function is called, the data display is updated
        """        
        self.Xmx[:-1] = self.Xmx[1:]                    # shift data in the temporal mean 1 sample left
        self.Xmy[:-1] = self.Xmy[1:]
                
        line = str(data)
        values = re.split('[:,}]', line)      # split the string to get the values
        
        x_data = float(values[4])
        y_data = float(values[6])
        z_data = float(values[8])
        
        self.current = np.hstack((x_data,y_data,z_data))
        self.buffer[self.ii] = self.current
        self.df = pd.DataFrame(self.buffer)
        self.df.columns = ['X-data', 'Y-data', 'Z-data']
        self.ii += 1
        
        """Convert data into mG"""
        self.Xmx[-1] = x_data * 1000              # vector containing the instantaneous values      
        self.Xmy[-1] = y_data * 1000
        
        self.graph.setData(self.Xmx, self.Xmy, symbol='o', symbolBrush='r', symbolSize=20)
        # add lines for positive and negative x/y-limits
#        self.plot.addLine(y=self.xLim, pen='c')
#        self.plot.addLine(y=-self.xLim, pen='c')
#        self.plot.addLine(x=self.yLim, pen='c')
#        self.plot.addLine(x=-self.yLim, pen='c')
        
        QtWidgets.QApplication.processEvents()    # process the plot


class storeWindow(QtWidgets.QWidget):
    """ Class to only save the data (no visualization) """
    
    def __init__(self):
        """Initialize the storage window"""
        
        super(storeWindow, self).__init__()
        self.initUI()
        
        # Define a buffer to save the data
        row = 7500  # sample_rate (25 Hz) x time (5 min)
        col = 3     # 3 signals from accelerometer or 3 from gyroscope
        self.buffer = np.nan * np.ones((row, col))
        self.ii = 0
        
        # Define a second buffer for the case that 2 devices are selected
        row = 135000  # sample_rate (50 Hz) x time (45 min)
        col = 3     # 3 signals from accelerometer and 3 from gyroscope
        self.buffer2 = np.nan * np.ones((row, col))
        self.jj = 0
        
        # Create name for the outfile by defining the current date and time
        self.outfileAcc = datetime.datetime.now().strftime("%b%d%Y_%H-%M-%S_Acc")
        self.outfileGyr = datetime.datetime.now().strftime("%b%d%Y_%H-%M-%S_Gyr")
        
        self.outfileAcc2 = datetime.datetime.now().strftime("%b%d%Y_%H-%M-%S_Acc2")
        self.outfileGyr2 = datetime.datetime.now().strftime("%b%d%Y_%H-%M-%S_Gyr2")


    def initUI(self):  
        """define the corresponding UI"""
        
         # Set layout to a QGridLayout, so you only need to define row and column
        self.layout = QtWidgets.QGridLayout()
        self.setLayout(self.layout)
        
        self.btnStop = QtGui.QPushButton('Stop')
        self.layout.addWidget(self.btnStop, 0,0)
        self.btnStop.clicked.connect(self.stopStreaming)
        
        self.cbox = QtWidgets.QComboBox()
        self.cbox.addItems(['bitte waehlen', 'Accelerometer', 'Gyroscope'])
        self.layout.addWidget(self.cbox, 0,1)
        self.cbox.currentIndexChanged.connect(self.selectionChange)


    def selectionChange(self, i):
        """ choose what data to measure """
        
        print(self.cbox.itemText(i))
        self.sensor = self.cbox.itemText(i)
        if self.sensor == 'Accelerometer':
            self.btn = QtGui.QPushButton('Start')
            self.layout.addWidget(self.btn, 1,0)
            self.btn.clicked.connect(self.searchForDirectory)
            self.btn.clicked.connect(self.btn.deleteLater)
        elif self.sensor == 'Gyroscope':
            self.btn = QtGui.QPushButton('Start')
            self.layout.addWidget(self.btn, 1,0)
            self.btn.clicked.connect(self.searchForDirectory)
            self.btn.clicked.connect(self.btn.deleteLater)
        else:
            print('No sensor selected...')


    def searchForDirectory(self):
        """ Create a file dialog for saving the data """
            
        self.dirPath = QtGui.QFileDialog.getExistingDirectory(
            self,
            "Open a folder",
            ".",
            QtGui.QFileDialog.ShowDirsOnly
            )
        if self.sensor == 'Accelerometer':
            self.startAccStreaming()
        else:
            self.startGyroStreaming()


    def startAccStreaming(self):
        """ stream data from accelerometer """
        
        # Subscribe to notifications to get the data (until callback=None)
        device1.accelerometer.set_settings(data_rate=50)
        # high_frequency_stream has to be true for streaming multiple devices
        device1.accelerometer.high_frequency_stream = True
        device1.accelerometer.notifications(self.streamingData1)
        
        if deviceFlag == True:
            device2.accelerometer.set_settings(data_rate=50)
            device2.accelerometer.high_frequency_stream = True
            device2.accelerometer.notifications(self.streamingData2)


    def startGyroStreaming(self):
        """ stream data from gyroscope """
        
        device1.gyroscope.notifications(self.streamingData1)
        device1.gyroscope.high_frequency_stream = True
        
        if deviceFlag == True:
            device2.gyroscope.notifications(self.streamingData2)
            device2.gyroscope.high_frequency_stream = True


    def stopStreaming(self):
        """ Stop data streaming after 'Stop' is clicked """
        
        device1.accelerometer.notifications(None)
        device1.gyroscope.notifications(None)
        if deviceFlag == True:
            device2.accelerometer.notifications(None)
            device2.gyroscope.notifications(None)
        time.sleep(3.0)
        print('Unsubscribed from notifications...')
        self.df = self.df[pd.notnull(self.df['X-data'])]  # Remove empty rows
        os.chdir(self.dirPath)
        if self.sensor == 'Accelerometer':
            self.df.to_csv(self.outfileAcc, sep='\t')
            if deviceFlag == True:
                self.df2 = self.df2[pd.notnull(self.df2['X-data'])]
                self.df2.to_csv(self.outfileAcc2, sep='\t')
        else:
            self.df.to_csv(self.outfileGyr, sep='\t')
            if deviceFlag == True:
                self.df2 = self.df2[pd.notnull(self.df2['X-data'])]
                self.df2.to_csv(self.outfileGyr2, sep='\t')
            
        print('\nData saved to ', self.dirPath)


    def streamingData1(self, data):
        """ Get sensor data and save it to a buffer """
        
        line = str(data)
        values = re.split('[:,}]', line)  # split the string to get the values
        
        x_data = float(values[4])
        y_data = float(values[6])
        z_data = float(values[8])
        
        self.current = np.hstack((x_data,y_data,z_data))
        self.buffer[self.ii] = self.current
        self.df = pd.DataFrame(self.buffer)
        self.df.columns = ['X-data', 'Y-data', 'Z-data']
        self.ii += 1


    def streamingData2(self, data):
        """ Get the data from the second device and 
        save it to another buffer
        """        
        
        line = str(data)
        values = re.split('[:,}]', line)  # split the string to get the values
        
        x_data = float(values[4])
        y_data = float(values[6])
        z_data = float(values[8])
        
        self.current2 = np.hstack((x_data,y_data,z_data))
        self.buffer2[self.jj] = self.current2
        self.df2 = pd.DataFrame(self.buffer2)
        self.df2.columns = ['X-data', 'Y-data', 'Z-data']
        self.jj += 1


if __name__ == '__main__':
    # Set device 
    sensor = ngimu.Sensor(timeout=None)

    # Set the defaults
    sensor.channel = 'acc'
    sensor.limit = 1.2      # [g]

    second_sensor = False  # Define a flag to check if second device is selected used to be "deviceFlag"

    """
    query_device = input('Add another device (y/n)? ')
    if query_device == 'y':
        deviceFlag = True
        address2 = select_device()
        device2 = MetaWearClient(str(address2), debug=True) 
        device2.accelerometer.set_settings(data_rate=12.5)
        device2.accelerometer.set_settings(data_range=4.0)
        device2.gyroscope.set_settings(data_rate=25)
        device2.gyroscope.set_settings(data_range=500)
    else:
        deviceFlag = False
        print('Only one device selected\n')
    """
    
    # Create a QApplication (the if/then is needed in spyder)
    if not QtWidgets.QApplication.instance():
        app = QtWidgets.QApplication(sys.argv)
    else:
        app = QtWidgets.QApplication.instance()
    #app = QtWidgets.QApplication.instance()
    
    # Set back- and foreground colors
    pg.setConfigOption('background', 'k')   
    pg.setConfigOption('foreground', 'w')
    
    GUI = MainWindow()
    GUI.show()
    
    # Timer for updating the display
    timer = QtCore.QTimer()
    timer.timeout.connect(update)
    timer.start(10)                  
    
    sys.exit(app.exec_())
