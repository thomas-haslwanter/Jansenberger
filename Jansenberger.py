"""
App for recording experimental data with the NGIMU, at the Institute Jansenberger

Notes
-----
The files "subjects.txt" and "experimentors.txt" have to be manipulated outside this program.
"""

#   author: Thomas Haslwanter
#   date:   Feb-2020

# Import the required standard Python packages, ...
import numpy as np
import yaml
import sys
import shutil
import time
import datetime
import os


# ..., the Qt-packages, ...
from PyQt5 import QtWidgets, uic, QtCore, QtGui
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
import pyqtgraph as pg

import guidata
#_app = guidata.qapplication() # not required if a QApplication has already been created
import guidata.dataset.datatypes as dt
import guidata.dataset.dataitems as di

# ... and the module for the interface with the NGIMU
import ngimu


class DefaultParameters(dt.DataSet):
    """ Settings Instructions 'comment': <br>Plain text or <b>rich text</b> are both supported. """
    
    with open('settings.yaml', 'r') as fh:
        defaults = yaml.load(fh, Loader=yaml.FullLoader)
        
    data_dir = di.DirectoryItem("Directory", defaults['dataDir'])

    _b_TimeView = dt.BeginGroup("Time View")
    acc_limit = di.FloatItem("Limit [Accelerometer]", default=defaults['accLim'], min=0, max=3, step=0.01, slider=True)                             
    gyr_limit = di.FloatItem("Limit [Gyroscope]", default=defaults['gyrLim'], min=100, max=1000, step=1, slider=True)                             
    thresholds = di.FloatItem("Thresholds", default=defaults['thresholds'], min=0, max=3, step=0.01, slider=True)
    _e_TimeView = dt.EndGroup("Time View")
    # For some funny reason, the display is off if this is put inside the "Time View"-Group
    init_sensorType = di.ChoiceItem("Initial sensortype", [(0,'acc'), (1,'gyr')], default=defaults['initSensortype'], radio=True)

    _b_Exercise = dt.BeginGroup("Exercise")
    color_top = di.ColorItem("Top", default=defaults['topColor'])
    color_middle = di.ColorItem("Middle", default=defaults['middleColor'])
    color_bottom  = di.ColorItem("Bottom", default=defaults['bottomColor'])
    upper_thresh = di.FloatItem("Upper Threshold", default=defaults['upperThresh'], min=0, max=2, step=0.01, slider=True)                             
    lower_thresh = di.FloatItem("Lower Threshold", default=defaults['lowerThresh'], min=0.1, max=1, step=0.01, slider=True)                             
    _e_Exercise = dt.EndGroup("Colors")

    _b_Sensors = dt.BeginGroup("Sensors")
    sensor_0 = di.IntItem('Sensor 1', default=defaults['sensor0'])
    sensor_1 = di.IntItem('Sensor 2', default=defaults['sensor1'])
    _e_Sensors = dt.EndGroup("Sensors")

    opening_view = di.ChoiceItem("Initial View", [(0, 'Time-View'), (1, "xy-View"), (2, 'TrafficLight-View')], radio=True)
    

class MainWindow(QtWidgets.QMainWindow):
    """Class for the Time-View and the xy-View"""

    signal = pyqtSignal()
    
    
    def __init__(self, sensors, experiment, *args, **kwargs):
        """ Initialization Routines """

        super(MainWindow, self).__init__(*args, **kwargs)


        # Experimental parameters
        self.exp = experiment

        #Load the UI Page
        uic.loadUi('Jansenberger.ui', self)

        # Create the DataView
        self.graphWidget = pg.PlotWidget()
        self.stackedWidget.addWidget( self.graphWidget )
        
        
        # Initialize 3 curves
        # For the TimeView all 3 are required, the xy-View uses only the first one
        ph = self.graphWidget
        curves = [ ph.plot(pen='y', label='x'),
                  ph.plot(pen='r', label='y'),
                  ph.plot(pen='g', label='z'),
                  ph.plot(pen='b', size=50, symbolBrush='r', symbolPen='w')]
                  #ph.plot(pen='r', label='a')]
        
        
        self.threshold_handles=None     # by default, show no threshold
        self.comboBox.addItems(['Accelerometer', 'Gyroscope'])
        self.logging = False

        # Change the language settings
        with open('lang.yaml', 'r') as fh:
            self.lang_dict = yaml.load(fh, Loader=yaml.FullLoader)

        self.exitButton.setText( self.lang_dict['Exit'] )
        self.logButton.setText( self.lang_dict['StartLog'] )
        
        self.action2dChannels.setText( self.lang_dict['2dChannels'] )
        self.actionChangeDefaults.setText( self.lang_dict['ChangeDefaults'] )
        self.actionExerciseView.setText( self.lang_dict['ExerciseView'] )
        self.actionExThresholds.setText (self.lang_dict['ExThresholds'])
        self.actionLimits.setText( self.lang_dict['Limits'] )
        self.actionTimeView.setText( self.lang_dict['TimeView'] )
        self.actionThresholds.setText (self.lang_dict['Thresholds'])
        self.actionXyView.setText( self.lang_dict['XyView'] )
        
        self.menuModes.setTitle( self.lang_dict['Modes'] )
        self.menuView.setTitle( self.lang_dict['View'] )
        self.menuHelp.setTitle( self.lang_dict['Help'] )
        self.menuSettings.setTitle( self.lang_dict['Settings'] )
        self.menuLanguage.setTitle( self.lang_dict['Language'] )
        
        self.statusBar().showMessage( self.lang_dict['Status'] )

        # Load the default settings
        with open('settings.yaml', 'r') as fh:
            self.defaults = yaml.load(fh, Loader=yaml.FullLoader)
        
        # Make sure the default data-dir exists
        if not os.path.exists(self.defaults['dataDir']):
            self.change_defaults()
            with open('settings.yaml', 'r') as fh:
                self.defaults = yaml.load(fh, Loader=yaml.FullLoader)

        self.lower_thresh = self.defaults['lowerThresh']
        self.upper_thresh = self.defaults['upperThresh']
        self.thresholds = self.defaults['thresholds']
        self.actionHelpfile.triggered.connect( self.show_help )
        self.actionExit.triggered.connect( self.save_and_close )
        self.actionAutoRange.triggered.connect( self.set_autoRange )
        self.actionLimits.triggered.connect( self.set_limits )
        self.actionExThresholds.triggered.connect( self.set_exThresholds )
        self.actionThresholds.triggered.connect( self.show_thresholds )
        self.action2dChannels.triggered.connect( self.change_channels )
        self.actionSingles.triggered.connect( self.show_singles )
        self.actionSensor.triggered.connect( self.set_sensor )
        self.actionChangeDefaults.triggered.connect( self.change_defaults )
        self.actionTimeView.triggered.connect( self.show_timeView )
        self.actionXyView.triggered.connect( self.show_xyView )
        self.actionExerciseView.triggered.connect( self.show_exerciseView )
        self.exitButton.clicked.connect( self.save_and_close )
        self.actionLangEn.triggered.connect( self.change_lang_to_eng )
        self.actionLangDe.triggered.connect( self.change_lang_to_de )
        self.comboBox.currentIndexChanged.connect ( self.change_source )
        self.logButton.clicked.connect( self.record_data )

        
        # Set shortcuts
        self.actionTimeView.setShortcut("Ctrl+1")
        self.actionXyView.setShortcut("Ctrl+2")
        self.actionExerciseView.setShortcut("Ctrl+3")
        self.actionExit.setShortcut("Ctrl+x")
        
        # Sensor data
        self.sensors = sensors
        self.exp.curves = curves
        self.view = 'timeView'
        self.channel_nrs = [0,1]    # for xy-View
        self.action2dChannels.setEnabled(False)
        self.actionExThresholds.setEnabled(False)
        self.setWindowTitle('Subject: ' + self.exp.subject)
        
        # Create the TrafficLight
        self.light = ExerciseLight(mainWin=self)
        self.stackedWidget.addWidget( self.light )
        self.signal.connect( self.light._trigger_refresh )
        
        self.stackedWidget.setCurrentIndex(0)

        self.change_source(0)
        
        # Timer for updating the display
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(lambda: self.update_view())
        self.timer.start(10)                  
        
        
    def show_help(self):
        """Show the Help-file"""
        
        help_file = 'Help.html'
        print(help_file)
        os.system(help_file)
        
        
    def change_defaults(self):
        """ Allow the user to change the default settings """
        
        # Create QApplication
        import guidata
        _app = guidata.qapplication()
        
        e = DefaultParameters()
        print(e)
        if e.edit():
            defaults = {
            'accLim': e.acc_limit,
            'gyrLim': e.gyr_limit,
            'dataDir': e.data_dir,
            'topColor': e.color_top,
            'middleColor': e.color_middle,
            'bottomColor': e.color_bottom,
            'upperThresh': e.upper_thresh,
            'lowerThresh': e.lower_thresh,
            'initSensortype': e.init_sensorType,
            'openingView': e.opening_view,
            'thresholds': e.thresholds,
            'sensor0': e.sensor_0,
            'sensor1': e.sensor_1
            }
            settings_file = 'settings.yaml'
            with open(settings_file, 'w') as fh:
                yaml.dump(defaults, fh)
            print(f'New settings saved to {settings_file}')
            print(e)
            # e.view()
        
        
    def save_and_close(self):
        """ Saves logging stream and closes the program """

        if hasattr(self, 'out_files'):
            for sensor, out_file in zip(self.sensors, self.out_files):
                if not out_file['fh'].closed:
                    if sensor.store_ptr > 0:
                        print(sensor.store_ptr)
                        np.savetxt(out_file, sensor.store_data[:sensor.store_ptr,:], delimiter=',')
                    out_file['fh'].close()
                    print(f"Recorded data written to: {out_file['name']}")
            
        # Close the application            
        self.close()
        

    def record_data(self):
        """ Stream the incoming signals to a unique file in the selected data-directory """
        
        if self.logging == False:
            self.logging = True
            self.logButton.setText( self.lang_dict['Stop_Log'] )
            self.logButton.setStyleSheet('background-color: red')
            
            now = datetime.datetime.now()
            date_time = now.strftime("%Y%m%d_%H-%M-%S")
            date = now.strftime("%c")
            
            data_dir = self.defaults['dataDir']
            subject = self.exp.subject

            self.out_files = []
            for ii in range(len(self.sensors)):
                out_file = os.path.join( data_dir, date_time + '_' + \
                        subject.split(',')[0] + '_' + str(ii) + '.dat' )

                self.statusBar().showMessage( 'Recording ' + out_file )
                
                try:
                    fh_out = open(out_file, 'wb')
                except:
                    print(f'Could not open {out_file}. Please check if the default directory in SETTINGS.YAML is correct!')
                    exit()
                    
                # Write a header
                fh_out.write(f'Subject: {self.exp.subject}\n'.encode())
                fh_out.write(f'Experimentor: {self.exp.experimentor}\n'.encode())
                fh_out.write(f'Date: {date}\n'.encode())
                #fh_out.write(f'Sample rate: '.encode())
                
                fh_out.write(b'Time (s),'+\
                                  b'Gyroscope X (deg/s),Gyroscope Y (deg/s),Gyroscope Z (deg/s),'+\
                                  b'Accelerometer X (g),Accelerometer Y (g),Accelerometer Z (g),'+\
                                  b'Magnetometer X (uT),Magnetometer Y (uT),Magnetometer Z (uT),'+\
                                  b'Barometer (hPa),'+\
                                  b'Quat 0, Quat X, Quat Y, Quat Z\n')

                self.out_files.append({'fh':fh_out, 'name':out_file})
                
        else:
            self.logging = False
            self.logButton.setText( self.lang_dict['Start_Log'] )
            self.logButton.setStyleSheet('background-color: ')
            self.statusBar().showMessage( self.lang_dict['Status'] )
            
            for out_file, sensor in zip(self.out_files, self.sensors):
                if sensor.store_ptr > 0:
                    np.savetxt(out_file['fh'], sensor.store_data[:sensor.store_ptr,:], delimiter=',')
                out_file['fh'].close()
                print(f"Recorded data written to: {out_file['name']} ")


    def change_source(self, i):
        """ Choose what data to display """
        
        selected = self.comboBox.itemText(i)
        if i == 0:
            self.exp.sensorType = 'acc'
            new_val = self.defaults['accLim']
        elif i == 1:
            self.exp.sensorType = 'gyr'
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
        for ii, sensor in enumerate(self.sensors):
            new_data = sensor.get_data('dat_quat')

            # If the sensor times out, take the last received datapoint
            if not new_data:
                print('still running!')
                new_data = sensor.show_data[:,-1]
                dummy_data = True
            elif len(new_data) != 15:
                print('new data have the wrong shape!')
                new_data = sensor.show_data[:,-1]
                dummy_data = True
            else:
                dummy_data = False
                
                        
            # Data logger
            if self.logging:
                if not dummy_data:
                    sensor.store_data[sensor.store_ptr,:] = new_data
                    sensor.store_ptr += 1

            if sensor.store_ptr == len(sensor.store_data):
                np.savetxt(self.out_files[ii]['fh'], sensor.store_data, delimiter=',')
                sensor.store_ptr = 0
                

            # Data viewer
            if ii == self.exp.show_nr:
                # Update the 'data' for the plot, and put them into the corresponding plot-lines
                if dummy_data:
                    sensor.show_data = np.hstack((sensor.show_data[:,1:], np.c_[new_data]))
                else:
                    if self.exp.sensorType == 'acc':
                        sensor.show_data = np.hstack((sensor.show_data[:,1:], np.c_[new_data[4:7]]))
                    elif self.exp.sensorType == 'gyr':
                        sensor.show_data = np.hstack((sensor.show_data[:,1:], np.c_[new_data[1:4]]))
                    else:
                        print(f'Do not know channel {self.exp.sensorType}')
                
                if self.view == 'timeView':
                    for curve, data in zip(self.exp.curves[:3], sensor.show_data):
                        curve.setData(data)
                elif self.view == 'xyView':
                    self.exp.curves[0].setData(sensor.show_data[self.channel_nrs[0]], sensor.show_data[self.channel_nrs[1]])
                    self.exp.curves[3].setData([sensor.show_data[self.channel_nrs[0]][-1]], [sensor.show_data[self.channel_nrs[1]][-1]])

                if self.view == 'trafficlightView':
                    self.signal.emit()

            
    def set_sensor(self):
        """Select which sensor to display"""
        
        dlg = EnterText(title=f'Select sensor (max={len(self.sensors)-1}):', default=self.exp.show_nr)
        if dlg.exec_():
            new_val = np.int(dlg.valueEdit.text())
            print(f'New value: {new_val}')

            self.exp.show_nr = new_val
        
        
    def set_autoRange(self):
        """Automatically adjusts to the view all data"""
        
        self.graphWidget.enableAutoRange()
        
        
    def set_limits(self):
        """
        Get a new value for the limits and apply them to the existing graph.
        Works for timeView and for xyView
        """

        dlg = EnterText(title='Y-Limit:', default=np.round(self.graphWidget.visibleRange().bottom(), decimals=2))
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

            
    def show_singles(self):
        """
        Select display of a single channel per sensor
        - The input has to be either 'x', 'y', or 'z'
        - Otherwise, all three channels are displayed
        """
        
        # For 2 sensors, I have to make a new "view"
        
        valid = 'xyz'
        default_txt = 'x'
        dlg = EnterText(title='Select channel(s) to display (e.g. "x"), or "3" for all channels:', default=default_txt)
        if dlg.exec_():
            singles = dlg.valueEdit.text()
            #if len(singles) != len(self.sensors):
                #raise ValueError(f'Number of selected channels must equal number of sensors {len(sensors)}!')
                #return
            if len(singles) != 1:   # For inputs with more than one letter, revert to "show all"
                for ii in range(3):
                    self.exp.curves[ii].setVisible(True)
            else:    
                for single in singles:
                    if single.lower() not in valid:
                        for ii in range(3):
                            self.exp.curves[ii].setVisible(True)
                    else: 
                        for ii in range(3):
                            if ii != 'xyz'.find(single.lower()):
                                self.exp.curves[ii].setVisible(False)
                            else:
                                self.exp.curves[ii].setVisible(True)
        
        
    def change_channels(self):
        """Select the channels in the xy-view """

        # Get current coordinates:
        old_channels = self.channel_nrs
        valid = 'xyz'
        default_txt = valid[old_channels[0]] + ':' + valid[old_channels[1]]
        dlg = EnterText(title='Select Coordinates (e.g. "x:z"):', default=default_txt)
        if dlg.exec_():
            channels = dlg.valueEdit.text().split(':')
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

            
    def set_exThresholds(self):
        """Select the lower/upper threshold for the TrafficLight-view """
    
        dlg = EnterText(title='Select lower/upper threshold (e.g. "0.4; 0.9"):')
        if dlg.exec_():
            thresholds = np.array(dlg.valueEdit.text().split(';'), dtype=float)
    
        else:
            print('No change')
            
        self.lower_thresh = thresholds[0]     
        self.upper_thresh = thresholds[1]     
            
       
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
            self.exp.curves[ii].setVisible(True)
            
        self.exp.curves[3].setVisible(False)    # big dot only in time-view
            
        ph = self.graphWidget
        sensor = self.sensors[self.exp.show_nr]
        ph.setXRange(0, len(sensor.show_data[0]))
        ph.setXRange(0, len(sensor.show_data[0]))
        ph.showGrid(x=False, y=False)
        
        # Enable/disable the appropriate options
        self.actionLimits.setEnabled(True)
        self.actionSingles.setEnabled(True)
        self.actionThresholds.setEnabled(True)
        
        self.action2dChannels.setEnabled(False)
        self.actionExThresholds.setEnabled(False)
        
        # if you come from xyView, clear existing thresholds
        if self.threshold_handles and (type(self.threshold_handles) == list):
            for threshold in self.threshold_handles:
                threshold.setVisible(False)
                threshold = None
        
    def show_thresholds(self):
        """Indicates a horizontal 'threshold-line' in the timeView window
        - If a numerical value gets entered in the dialog, a white threshold line
          is set at that level.
        - If a text is entered, the line is removed
        """
        
        ph = self.graphWidget
        #ph.autoRange(padding=0)
        rect = ph.viewRect()
        
        #axX = ph.getAxis('bottom')
        #curXRange = axX.range
        #axY = ph.getAxis('left')
        
        #x_data = self.exp.curves[0].getData()[0]
        #x_range = [np.min(x_data), np.max(x_data)]
        
        if self.view == 'timeView':
            if self.threshold_handles is None:
                self.threshold_handles =  ph.plot(np.r_[rect.left(), rect.right()], 
                                                self.thresholds*np.r_[1,1],
                                                pen='w')
            else:
                if type(self.threshold_handles) == list:
                    for threshold in self.threshold_handles:
                        threshold.setVisible(True)
                else:
                    self.threshold_handles.setVisible(True)
                
            num_data = len(self.exp.curves[0].getData()[0])
            self.graphWidget.setXRange(0, num_data, padding=0)
                
        elif self.view == 'xyView':
            if self.threshold_handles is None:
                self.threshold_handles =  [
                    ph.plot( self.thresholds*np.r_[-1,1], -self.thresholds*np.r_[1,1], pen='w'),
                    ph.plot( self.thresholds*np.r_[-1,1],  self.thresholds*np.r_[1,1], pen='w'),
                    ph.plot(-self.thresholds*np.r_[1,1],  self.thresholds*np.r_[-1,1], pen='w'),
                    ph.plot( self.thresholds*np.r_[1,1],  self.thresholds*np.r_[-1,1], pen='w'),
                    ]
            else:
                for threshold in self.threshold_handles:
                    threshold.setVisible(True)
            
        
        dlg = EnterText(title='Threshold-value, or "none" for no display:', default=np.round(self.thresholds, decimals=1))
        if dlg.exec_():
            try:
                new_val = np.float(dlg.valueEdit.text())
                print(f'New value: {new_val}')
                self.thresholds=new_val
    
                if self.view == 'timeView':
                    self.threshold_handles.setData([rect.left(), rect.right()], self.thresholds*np.r_[1,1])
                elif self.view == 'xyView':
                    self.threshold_handles[0].setData( self.thresholds*np.r_[-1,1], -self.thresholds*np.r_[1,1] )
                    self.threshold_handles[1].setData( self.thresholds*np.r_[-1,1],  self.thresholds*np.r_[1,1] )
                    self.threshold_handles[2].setData(-self.thresholds*np.r_[1,1],  self.thresholds*np.r_[-1,1] )
                    self.threshold_handles[3].setData( self.thresholds*np.r_[1,1],  self.thresholds*np.r_[-1,1] )
                else:
                    raise ValueError(f'Do knot know channel {self.view}')
            except ValueError:      # if the user enters a string, such as 'None'
                if self.view == 'timeView':
                    self.threshold_handles.setVisible(False)
                else:           # xyView
                    for threshold in self.threshold_handles:
                        threshold.setVisible(False)
        else:
            print('No change')
        
            
    def show_xyView(self):
        """Shows one signal as a traffic light, with two independent thresholds"""
        
        self.stackedWidget.setCurrentIndex(0)
        self.view = 'xyView'
        for ii in [1,2]:
            self.exp.curves[ii].setVisible(False)
            
        self.exp.curves[3].setVisible(True)
            
        ph = self.graphWidget
        ph.showGrid(x=True, y=True)
            
        sensor = self.sensors[self.exp.show_nr]
        self.exp.curves[0].setData(sensor.show_data[0], sensor.show_data[1])
        self.exp.curves[3].setData(sensor.show_data[0], sensor.show_data[1])
        #self.exp.curves[3].setData([sensor.show_data[0][0]], [sensor.show_data[1][0]])
        new_val = float(ph.getAxis('left').range[0])
        print(new_val)
        
        ph.setXRange(-new_val, new_val)
        # is this a bug? With only one call, the limit does not set correctly!
        ph.setXRange(-new_val, new_val)
        ph.setYRange(-new_val, new_val)
        
        # Enable/disable the appropriate options
        self.action2dChannels.setEnabled(True)
        self.actionLimits.setEnabled(True)
        
        self.actionExThresholds.setEnabled(False)
        self.actionSingles.setEnabled(False)
        #self.actionTimeviewThreshold.setEnabled(False)
        
        # if you come from timeView, clear existing thresholds
        if self.threshold_handles and (type(self.threshold_handles) != list):
            self.threshold_handles.setVisible(False)
            self.threshold_handles = None
            
    def show_exerciseView(self):
        """Shows one signal as a traffic light, with two independent thresholds"""
        
        self.view = 'trafficlightView'
        self.stackedWidget.setCurrentIndex(1)
        
        self.action2dChannels.setEnabled(False)
        self.actionLimits.setEnabled(False)
        self.actionExThresholds.setEnabled(True)
            
                    
class ExerciseLight(QtWidgets.QWidget):
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
        sensor = self.mainWin.sensors[self.mainWin.exp.show_nr]
        signal = sensor.show_data[0,-1]
        
        if np.abs(signal) > self.mainWin.upper_thresh:
            value = 2
        elif np.abs(signal) < self.mainWin.lower_thresh:
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

    def __init__(self, title, default, *args, **kwargs):
        super(EnterText, self).__init__(*args, **kwargs)

        self.setWindowTitle(title)

        QBtn = QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel

        self.buttonBox = QtWidgets.QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.valueEdit = QtWidgets.QLineEdit()
        self.valueEdit.setText(str(default))

        self.layout = QtWidgets.QVBoxLayout()
        self.layout.addWidget(self.valueEdit)
        self.layout.addWidget(self.buttonBox)
        self.setMinimumWidth(500)
        self.setLayout(self.layout)
        

def get_subjects():
    """ Initial setup, who does the recording and who is the subject"""
    
    subject_file = 'subjects.txt'
    experimentor_file = 'experimentors.txt'
    
    with open(subject_file, 'r') as fh:
        subjects = fh.readlines()
    for ii in range(len(subjects)):
        subjects[ii] = subjects[ii][:-1]
    
    with open(experimentor_file, 'r') as fh:
        experimentors = fh.readlines()
    for ii in range(len(experimentors)):
        experimentors[ii] = experimentors[ii][:-1]
    
    return (subjects, experimentors)

    
class Experiment():
    """ Experimental parameters """
    
    def __init__(self):
        self.num_data = 800     # for the display
        self.save_data = 100    # to save in blocks
        self.show_nr = 0        # which sensor to
        self.sensorType = 'acc'    # which channel to display 

        # Select the subject and the experimentor
        p = Subjects()      # "p" for "persons"
        p.edit()
        self.subject = p.sub_list[p.sub_nr]
        self.experimentor = p.exp_list[p.exp_nr]

        
class Subjects(dt.DataSet):
    """ Select Experimentor and Subject """
    
    sub_list, exp_list = get_subjects()
    
    exp_nr = di.ChoiceItem("Experimentors", exp_list)
    sub_nr = di.ChoiceItem("Subjects", sub_list)
    

def main():
    """ Main Program """


    app = QtWidgets.QApplication(sys.argv)

    # Create and display the splash screen
    splash_pix = QtGui.QPixmap(r'Resources\Jansenberger.png')
    splash = QtWidgets.QSplashScreen(splash_pix, Qt.WindowStaysOnTopHint)
    splash.setMask(splash_pix.mask())
    #splash.raise_() 
    splash.show()
    app.processEvents()

    # Simulate something that takes time
    time.sleep(2)
    QTimer.singleShot(500, splash.close)
    
    # Define the experiment, subjects and parameters
    _app = guidata.qapplication()
    experiment = Experiment()

    # Establish the UDP connection
    # Currently the numbers are taken from the "settings.yaml"-file. This has yet to be automated, so that we can select the sensor!
    with open('settings.yaml', 'r') as fh:
        defaults = yaml.load(fh, Loader=yaml.FullLoader)
    ports = [defaults['sensor0']]
    if defaults['sensor1'] != 0:
        ports.append(defaults['sensor1'])
        
    sensors = []

    for ii, port in enumerate(ports):
        print(f'Sensor {ii}:')
        sensor = ngimu.Sensor(port=port, debug_flag=False)
        if sensor.address[0] == -1:
            print(f'No sensor on port {port}.')
        else:
            sensor.show_data = np.zeros( (3, experiment.num_data) )
            sensor.store_data = np.zeros( (experiment.save_data, 15) )
            sensor.store_ptr = 0

            sensors.append(sensor)

                    
    tv_win = MainWindow(sensors=sensors, experiment=experiment)
    tv_win.show()

    sys.exit(app.exec_())


if __name__ == '__main__':         
    main()
