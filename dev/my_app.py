import numpy as np
import yaml
from PyQt5 import QtWidgets, uic
import pyqtgraph as pg
import sys
from PyQt5.QtGui import QApplication

class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)

        #Load the UI Page
        uic.loadUi('TimeView.ui', self)

        self.graphWidget.plot(np.arange(10))

        self.exitButton.clicked.connect(self.close)

        self.comboBox.addItems(['Acc', 'Gyr'])

        # Change the language settings
        with open('lang.yaml', 'r') as fh:
            lang_dict = yaml.load(fh)

        self.exitButton.setText(lang_dict['Exit'])
        self.logButton.setText(lang_dict['Start_Log'])
        self.actionTime_View.setText(lang_dict['Time_View'])
        self.actionxy_View.setText(lang_dict['xy_View'])
        self.actionTrafficLight_View.setText(lang_dict['TrafficLight_View'])
        self.actionLimits.setText(lang_dict['Limits'])
        self.actionLanguage.setText(lang_dict['Language'])
        self.menuMyViews.setTitle(lang_dict['View'])
        self.menuSettings.setTitle(lang_dict['Settings'])
        self.statusBar().showMessage(lang_dict['Status'])

        # Load the default settings
        with open('settings.yaml', 'r') as fh:
            settings = yaml.load(fh)

def main():
    app = QtWidgets.QApplication(sys.argv)
    main = MainWindow()
    main.show()
    sys.exit(app.exec_())

if __name__ == '__main__':         
    main()
