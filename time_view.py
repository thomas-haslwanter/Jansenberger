import numpy as np
import yaml
import sys
import shutil
import time

from PyQt5 import QtWidgets, uic 
from PyQt5.QtGui import QApplication, QDialog, QDialogButtonBox, QVBoxLayout, QLineEdit
import pyqtgraph as pg
from pyqtgraph.Qt import QtGui, QtCore

import ngimu


def update(sensor):
    """Update the data in the streaming plot"""
    
    # Get the data from the NGIMU
    new_data = sensor.get_data(sensor.channel)
                
    # Update the 'data' for the plot, and put them into the corresponding plot-lines
    sensor.data = np.hstack((sensor.data[:,1:], np.c_[new_data]))
    
    for curve, data in zip(sensor.curves, sensor.data):
        curve.setData(data)


class ValueDialog(QDialog):
    """Dialog for entering values"""

    def __init__(self, *args, **kwargs):
        super(ValueDialog, self).__init__(*args, **kwargs)

        self.setWindowTitle("Select a Value:")

        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel

        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.valueEdit = QLineEdit()

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.valueEdit)
        self.layout.addWidget(self.buttonBox)
        self.setLayout(self.layout)


class TimeViewWindow(QtWidgets.QMainWindow):
    """Class for the time-series view"""

    def __init__(self, *args, **kwargs):
        super(TimeViewWindow, self).__init__(*args, **kwargs)

        #Load the UI Page
        uic.loadUi('TimeView.ui', self)

        self.graphWidget.plot(np.arange(10))


        self.comboBox.addItems(['Acc', 'Gyr'])

        # Change the language settings
        with open('lang.yaml', 'r') as fh:
            lang_dict = yaml.load(fh, Loader=yaml.FullLoader)

        self.exitButton.setText(lang_dict['Exit'])
        self.logButton.setText(lang_dict['Start_Log'])
        self.actionTime_View.setText(lang_dict['Time_View'])
        self.actionxy_View.setText(lang_dict['xy_View'])
        self.actionTrafficLight_View.setText(lang_dict['TrafficLight_View'])
        self.actionLimits.setText(lang_dict['Limits'])
        self.menuLanguage.setTitle(lang_dict['Language'])
        self.menuMyViews.setTitle(lang_dict['View'])
        self.menuSettings.setTitle(lang_dict['Settings'])
        self.statusBar().showMessage(lang_dict['Status'])

        # Load the default settings
        with open('settings.yaml', 'r') as fh:
            settings = yaml.load(fh, Loader=yaml.FullLoader)

        self.actionLimits.triggered.connect( self.set_yLim )
        self.exitButton.clicked.connect(self.close)
        self.actionen.triggered.connect( self.change_lang_to_eng )
        self.actionde.triggered.connect( self.change_lang_to_de )

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
    sensor = ngimu.Sensor()

    app = QtWidgets.QApplication(sys.argv)

    tv_win = TimeViewWindow()
    tv_win.show()

    sys.exit(app.exec_())

if __name__ == '__main__':         
    main()
