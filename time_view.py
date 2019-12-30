import numpy as np
import yaml
import sys
import shutil
import time
import datetime
import os

from PyQt5 import QtWidgets, uic 
import pyqtgraph as pg
from pyqtgraph.Qt import QtGui, QtCore

import ngimu



class ValueDialog(QtWidgets.QDialog):
    """Dialog for entering values"""

    def __init__(self, *args, **kwargs):
        super(ValueDialog, self).__init__(*args, **kwargs)

        self.setWindowTitle("Select a Value:")

        QBtn = QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel

        self.buttonBox = QtWidgets.QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.valueEdit = QtWidgets.QLineEdit()

        self.layout = QtWidgets.QVBoxLayout()
        self.layout.addWidget(self.valueEdit)
        self.layout.addWidget(self.buttonBox)
        self.setLayout(self.layout)


class TimeViewWindow(QtWidgets.QMainWindow):
    """Class for the time-series view"""

    def __init__(self, sensor, *args, **kwargs):
        """ Initialization Routines """

        super(TimeViewWindow, self).__init__(*args, **kwargs)

        #Load the UI Page
        uic.loadUi('TimeView.ui', self)

        # self.graphWidget.plot(np.arange(10))
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

        self.actionLimits.triggered.connect( self.set_yLim )
        self.exitButton.clicked.connect( self.close )
        self.actionen.triggered.connect( self.change_lang_to_eng )
        self.actionde.triggered.connect( self.change_lang_to_de )
        self.comboBox.currentIndexChanged.connect ( self.changeChannel )
        self.logButton.clicked.connect( self.record_data )

        
        # Sensor data
        self.sensor = sensor
        sensor.curves = curves

        self.changeChannel(0)
        
        # Timer for updating the display
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(lambda: self.update())
        self.timer.start(10)                  
        
        
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
        else:
            self.logging = False
            self.logButton.setText( self.lang_dict['Start_Log'] )
            self.logButton.setStyleSheet('background-color: ')
            self.statusBar().showMessage( self.lang_dict['Status'] )
            

    def changeChannel(self, i):
        """ Choose what data to display """
        
        selected = self.comboBox.itemText(i)
        if selected == 'acc':
            self.sensor.channel = selected
            new_val = self.defaults['accLim']
            self.graphWidget.setYRange(-new_val, new_val)
        elif selected == 'gyr':
            self.sensor.channel = selected
            new_val = self.defaults['gyrLim']
            self.graphWidget.setYRange(-new_val, new_val)
        else:
            print('No sensor selected...')
            
    def update(self):
        """Update the data in the streaming plot"""
        
        # Get the data from the NGIMU
        new_data = self.sensor.get_data(self.sensor.channel)

        # If the sensor times out, take the last received datapoint
        if not new_data:
            new_data = self.sensor.data[:,-1]
            print('still running!')
                    
        # Update the 'data' for the plot, and put them into the corresponding plot-lines
        self.sensor.data = np.hstack((self.sensor.data[:,1:], np.c_[new_data]))
        
        for curve, data in zip(self.sensor.curves, self.sensor.data):
            curve.setData(data)


    def set_yLim(self):
        """Get a new value for the y-limit, and apply it to the existing graph"""

        dlg = ValueDialog(self)
        if dlg.exec_():
            new_val = np.float(dlg.valueEdit.text())
            print(f'New value: {new_val}')

            self.graphWidget.setYRange(-new_val, new_val)
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


def main():
    # Establish the UDP connection
    # Note that those numbers can change - this has yet to be automated, so that we can select the sensor!
    sensor = ngimu.Sensor(debug_flag=False)
    if sensor.address[0] == -1:
        print('No sensor, so the program has been terminated.')
        return

    # Initialize the sensor data
    num_data = 800
    sensor.data = np.zeros( (3, num_data) )
    sensor.channel = 'acc'

    app = QtWidgets.QApplication(sys.argv)

    tv_win = TimeViewWindow(sensor=sensor)
    tv_win.show()

    sys.exit(app.exec_())

if __name__ == '__main__':         
    main()
