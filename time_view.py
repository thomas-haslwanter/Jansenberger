import numpy as np
import yaml
import sys
import shutil
import time
import datetime
import os

from PyQt5 import QtWidgets, uic 
from PyQt5.QtCore import Qt, pyqtSignal
import pyqtgraph as pg
from pyqtgraph.Qt import QtGui, QtCore

import ngimu


class _Light(QtWidgets.QWidget):
    """Paint a Traffic-light like signal"""

    def __init__(self, mainWin, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setSizePolicy(
         QtWidgets.QSizePolicy.MinimumExpanding,
         QtWidgets.QSizePolicy.MinimumExpanding
         )
        
        
        mainWin.signal.connect(self._trigger_refresh)
        self.mainWin = mainWin

    def sizeHint(self):
         return QtCore.QSize(40,120)

    def paintEvent(self, e):
        painter = QtGui.QPainter(self)
        
        padding = 5
        
        # Define our canvas.
        d_height = painter.device().height() - (padding * 2)
        d_width = painter.device().width() - (padding * 2)
        
        # Draw the trafficlight
        height = painter.device().height()
        width = painter.device().width()
        middle = width/2
        
        outer_padding = 5
        inner_padding = 5
        
        
        diameter = ((height - 2*outer_padding) - 4*inner_padding)/3
        box = (diameter + 4*inner_padding,  height - 2*outer_padding)
        top_left = (middle - box[0]/2, outer_padding)
        
        pen = QtGui.QPen()
        pen.setColor(QtGui.QColor('black'))
        pen.setWidth(20)
        
        painter.drawRect(*top_left, *box)
        
        # Get current state.
        
        signal = self.mainWin.sensor.show_data[0,-1]
        
        upper_lim = 0.5
        lower_lim = -0.5
        if signal > upper_lim:
            value = 2
        elif signal < lower_lim:
            value = 0
        else:
            value = 1
            
        
        # Draw the lights.
        colors = [QtGui.QColor(self.mainWin.defaults['topColor']),
                  QtGui.QColor(self.mainWin.defaults['middleColor']),
                  QtGui.QColor(self.mainWin.defaults['bottomColor'])]

        brush = QtGui.QBrush()
        brush.setStyle(Qt.SolidPattern)
        #brush.setColor(QtGui.QColor('red'))
        for ii in range(3):
            if ii == value:
                brush.setColor(colors[ii])
                brush.setStyle(Qt.SolidPattern)
                painter.setBrush(brush)
            else:
                brush.setStyle(Qt.NoBrush)
                painter.setBrush(brush)
                
            painter.drawEllipse(
                top_left[0] + 2*inner_padding,
                top_left[1] + inner_padding + ii*(inner_padding + diameter),
                diameter,
                diameter)
            brush.setColor(QtGui.QColor('blue'))
            
        painter.end()
        
    def _trigger_refresh(self):
         self.update()

        

class EnterText(QtWidgets.QDialog):
    """Dialog for entering values"""

    def __init__(self, title, *args, **kwargs):
        super(EnterText, self).__init__(*args, **kwargs)

        self.setWindowTitle(title)

        QBtn = QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel

        self.buttonBox = QtWidgets.QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.valueEdit = QtWidgets.QLineEdit()

        self.layout = QtWidgets.QVBoxLayout()
        self.layout.addWidget(self.valueEdit)
        self.layout.addWidget(self.buttonBox)
        self.setMinimumWidth(250)
        self.setLayout(self.layout)


class TimeViewWindow(QtWidgets.QMainWindow):
    """Class for the time-series view"""

    signal = pyqtSignal()
    
    def __init__(self, sensor, *args, **kwargs):
        """ Initialization Routines """

        super(TimeViewWindow, self).__init__(*args, **kwargs)

        #Load the UI Page
        uic.loadUi('TimeView.ui', self)

        # Create the DataView
        self.graphWidget = pg.PlotWidget()
        self.stackedWidget.addWidget( self.graphWidget )
        
        
        ph = self.graphWidget
        curves = [ ph.plot(pen='y', label='x'),
                  ph.plot(pen='r', label='y'),
                  ph.plot(pen='g', label='z') ]
        
        self.comboBox.addItems(['Accelerometer', 'Gyroscope'])
        self.logging = False

        # Change the language settings
        with open('lang.yaml', 'r') as fh:
            self.lang_dict = yaml.load(fh, Loader=yaml.FullLoader)

        self.exitButton.setText( self.lang_dict['Exit'] )
        self.logButton.setText( self.lang_dict['Start_Log'] )
        self.actionTime_View.setText( self.lang_dict['Time_View'] )
        self.actionxy_View.setText( self.lang_dict['xy_View'] )
        self.actionTrafficLight_View.setText( self.lang_dict['TrafficLight_View'] )
        self.actionLimits.setText( self.lang_dict['Limits'] )
        self.menuLanguage.setTitle( self.lang_dict['Language'] )
        self.menuMyViews.setTitle( self.lang_dict['View'] )
        self.menuSettings.setTitle( self.lang_dict['Settings'] )
        self.statusBar().showMessage( self.lang_dict['Status'] )

        # Load the default settings
        with open('settings.yaml', 'r') as fh:
            self.defaults = yaml.load(fh, Loader=yaml.FullLoader)

        self.actionLimits.triggered.connect( self.set_Limits )
        self.actionChannels.triggered.connect( self.set_coordinates )
        self.actionTime_View.triggered.connect( self.show_timeView )
        self.actionxy_View.triggered.connect( self.show_xyView )
        self.actionTrafficLight_View.triggered.connect( self.show_trafficlightView )
        self.exitButton.clicked.connect( self.save_and_close )
        self.actionen.triggered.connect( self.change_lang_to_eng )
        self.actionde.triggered.connect( self.change_lang_to_de )
        self.comboBox.currentIndexChanged.connect ( self.changeChannel )
        self.logButton.clicked.connect( self.record_data )

        
        # Set shortcuts
        self.actionTime_View.setShortcut("Ctrl+1")
        self.actionxy_View.setShortcut("Ctrl+2")
        self.actionTrafficLight_View.setShortcut("Ctrl+3")
        
        # Sensor data
        self.sensor = sensor
        sensor.curves = curves
        self.view = 'timeView'
        self.channel_nrs = [0,1]    # for xy-View
        self.actionChannels.setEnabled(False)
        
        # Create the TrafficLight
        self.light = _Light(mainWin=self)
        self.stackedWidget.addWidget( self.light )
        self.signal.connect( self.light._trigger_refresh )
        
        self.stackedWidget.setCurrentIndex(0)

        self.changeChannel(0)
        
        # Timer for updating the display
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(lambda: self.update_view())
        self.timer.start(10)                  
        
        
    def save_and_close(self):
        """ Saves logging stream and closes the program """

        if hasattr(self, 'fh_out'):
            if not self.fh_out.closed:
                if self.sensor.store_ptr > 0:
                    np.savetxt(self.fh_out, self.sensor.store_data, delimiter=',')
                self.fh_out.close()
                print(f'Recorded data written to: {self.fh_out.name}')
            
        # Close the application            
        self.close()
        


    def record_data(self):
        """ Stream the incoming signals to a unique file in the selected data-directory """
        
        if self.logging == False:
            self.logging = True
            self.logButton.setText( self.lang_dict['Stop_Log'] )
            self.logButton.setStyleSheet('background-color: red')
            date_time = datetime.datetime.now().strftime("%Y%m%d_%H-%M-%S")
            data_dir = self.defaults['dataDir']
            out_file = os.path.join( data_dir, date_time + '.dat' )
            self.statusBar().showMessage( 'Recording ' + out_file )
            
            try:
                self.fh_out = open(out_file, 'wb')
            except:
                print(f'Could not open {out_file}. Please check if the default directory in SETTINGS.YAML is correct!')
                exit()
                
            # Write a header
            self.fh_out.write(b'Time (s),'+\
                              b'Gyroscope X (deg/s),Gyroscope Y (deg/s),Gyroscope Z (deg/s),'+\
                              b'Accelerometer X (g),Accelerometer Y (g),Accelerometer Z (g),'+\
                              b'Magnetometer X (uT),Magnetometer Y (uT),Magnetometer Z (uT),'+\
                              b'Barometer (hPa),'+\
                              b'Quat 0, Quat X, Quat Y, Quat Z\n')
                
        else:
            if self.sensor.store_ptr > 0:
                np.savetxt(self.fh_out, self.sensor.store_data, delimiter=',')
            self.fh_out.close()
            print(f'Recorded data written to: {self.fh_out.name}')

            self.logging = False
            self.logButton.setText( self.lang_dict['Start_Log'] )
            self.logButton.setStyleSheet('background-color: ')
            self.statusBar().showMessage( self.lang_dict['Status'] )
            

    def changeChannel(self, i):
        """ Choose what data to display """
        
        selected = self.comboBox.itemText(i)
        if i == 0:
            self.sensor.channel = 'acc'
            new_val = self.defaults['accLim']
        elif i == 1:
            self.sensor.channel = 'gyr'
            new_val = self.defaults['gyrLim']
        else:
            print('No sensor selected...')
            
        if self.view == 'timeView':
            self.graphWidget.setYRange(-new_val, new_val)
        elif self.view == 'xyView':
            self.graphWidget.setXRange(-new_val, new_val)
            self.graphWidget.setYRange(-new_val, new_val)
            
    def update_view(self):
        """Update the data in the streaming plot"""
        
        # Get the data from the NGIMU
        #new_data = self.sensor.get_data(self.sensor.channel)
        new_data = self.sensor.get_data('dat_quat')

        # If the sensor times out, take the last received datapoint
        if not new_data:
            print('still running!')
            new_data = self.sensor.show_data[:,-1]
            dummy_data = True
        elif len(new_data) != 15:
            print('new data have the wrong shape!')
            new_data = self.sensor.show_data[:,-1]
            dummy_data = True
        else:
            dummy_data = False
            
                    
            
        # Update the 'data' for the plot, and put them into the corresponding plot-lines
        if dummy_data:
            self.sensor.show_data = np.hstack((self.sensor.show_data[:,1:], np.c_[new_data]))
        else:
            if self.sensor.channel == 'acc':
                self.sensor.show_data = np.hstack((self.sensor.show_data[:,1:], np.c_[new_data[4:7]]))
            elif self.sensor.channel == 'gyr':
                self.sensor.show_data = np.hstack((self.sensor.show_data[:,1:], np.c_[new_data[1:4]]))
            else:
                print(f'Do not know channel {self.channel}')
        
        if self.view == 'timeView':
            for curve, data in zip(self.sensor.curves, self.sensor.show_data):
                curve.setData(data)
        elif self.view == 'xyView':
            self.sensor.curves[0].setData(self.sensor.show_data[self.channel_nrs[0]], self.sensor.show_data[self.channel_nrs[1]])
            
        if self.logging:
            if not dummy_data:
                self.sensor.store_data[self.sensor.store_ptr,:] = new_data
                self.sensor.store_ptr += 1

        if self.sensor.store_ptr == len(self.sensor.store_data):
            np.savetxt(self.fh_out, self.sensor.store_data, delimiter=',')
            self.sensor.store_ptr = 0
            
        if self.view == 'trafficlightView':
            self.signal.emit()

    def set_Limits(self):
        """Get a new value for the y-limit, and apply it to the existing graph"""

        dlg = EnterText(title='Y-Limit:')
        if dlg.exec_():
            new_val = np.float(dlg.valueEdit.text())
            print(f'New value: {new_val}')

            if self.view == 'timeView':
                self.graphWidget.setYRange(-new_val, new_val)
            elif self.view == 'xyView':
                self.graphWidget.setXRange(-new_val, new_val)
                self.graphWidget.setYRange(-new_val, new_val)
            else:
                raise ValueError(f'Do knot know channel {self.view}')
        else:
            print('No change')

            
    def set_coordinates(self):
        """Select the channels in the xy-view """

        dlg = EnterText(title='Select Coordinates (e.g. "x:z"):')
        if dlg.exec_():
            channels = dlg.valueEdit.text().split(':')
            valid = 'xyz'
            channel_nrs = []
            for channel in channels:
                if channel.lower() not in valid:
                    raise ValueError('Coordinate selector has to have the form "x:z", and valid values are only "xyz"!')
                else: 
                    channel_nrs.append('xyz'.find(channel.lower()))
            
            print(f'New channels: {channel_nrs}')
            self.channel_nrs = channel_nrs

        else:
            print('No change')

    def change_lang_to_de(self):
        """Change to German menu"""
        shutil.copy('lang_de.yaml', 'lang.yaml')
        self.close()


    def change_lang_to_eng(self):
        """Change to an English menu"""
        shutil.copy('lang_en.yaml', 'lang.yaml')
        self.close()


    def show_timeView(self):
        """Shows three components versus time"""
        
        self.stackedWidget.setCurrentIndex(0)
        self.view = 'timeView'
        for ii in range(3):
            self.sensor.curves[ii].setVisible(True)
            
        ph = self.graphWidget
        ph.setXRange(0, len(self.sensor.show_data[0]))
        ph.showGrid(x=False, y=False)
        self.actionChannels.setEnabled(False)
        
        
    def show_xyView(self):
        """Shows one signal as a traffic light, with two independent thresholds"""
        
        self.stackedWidget.setCurrentIndex(0)
        self.view = 'xyView'
        for ii in [1,2]:
            self.sensor.curves[ii].setVisible(False)
            
        ph = self.graphWidget
        ph.showGrid(x=True, y=True)
            
        self.sensor.curves[0].setData(self.sensor.show_data[0], self.sensor.show_data[1])
        y_range = ph.getAxis('left').range
        ph.setXRange(float(y_range[0]), float(y_range[1]))
        # is this a bug? With only one call, the limit does not set correctly!
        ph.setXRange(float(y_range[0]), float(y_range[1]))     
        
        self.actionChannels.setEnabled(True)
        
            
    def show_trafficlightView(self):
        """Shows one signal as a traffic light, with two independent thresholds"""
        
        self.view = 'trafficlightView'
        self.stackedWidget.setCurrentIndex(1)
        
        self.actionChannels.setEnabled(False)
            
                    
            
def main():
    # Establish the UDP connection
    # Note that those numbers can change - this has yet to be automated, so that we can select the sensor!
    sensor = ngimu.Sensor(debug_flag=False)
    if sensor.address[0] == -1:
        print('No sensor, so the program has been terminated.')
        return

    # Initialize the sensor.show_data
    num_data = 800      # for the display
    save_data = 100     # to save in blocks
    sensor.show_data = np.zeros( (3, num_data) )
    sensor.store_data = np.zeros( (save_data, 15) )
    sensor.store_ptr = 0
    sensor.channel = 'acc'

    app = QtWidgets.QApplication(sys.argv)

    tv_win = TimeViewWindow(sensor=sensor)
    tv_win.show()

    sys.exit(app.exec_())

if __name__ == '__main__':         
    main()
