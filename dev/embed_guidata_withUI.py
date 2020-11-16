from PyQt5 import QtWidgets, uic 
from guidata.qt.QtGui import QMainWindow, QSplitter

from guidata.dataset.datatypes import (DataSet, BeginGroup, EndGroup,
                                       BeginTabGroup, EndTabGroup)
from guidata.dataset import dataitems as di
from guidata.dataset.dataitems import (ChoiceItem, FloatItem, StringItem,
                                       DirectoryItem, FileOpenItem)
from guidata.dataset.qtwidgets import DataSetShowGroupBox, DataSetEditGroupBox
from guidata.configtools import get_icon
from guidata.qthelpers import create_action, add_actions, get_std_icon


class ParameterDataSet(DataSet):
    threshold = di.FloatItem("Threshold", default=1., min=.5, max=1.5)
    repetitions = di.IntItem("Repetitions", default=10, min=2, max=50)
    direction = di.ChoiceItem("Axis", ['x', 'y', 'z'])
    use_absVal = di.BoolItem("yes", 'Absolute Value')
    use_inversion = di.BoolItem("yes", 'Invert Signal')
    

class MainWindow(QMainWindow):
    
    def __init__(self, *args, **kwargs):
        """ Initialization Routines """

        super(MainWindow, self).__init__(*args, **kwargs)
        #QtWidgets.QMainWindow.__init__(self)

        #Load the UI Page
        uic.loadUi('data.ui', self)
        
        self.setWindowTitle("Application example")
        
        # Instantiate dataset-related widgets:
        #self.groupbox = DataSetEditGroupBox("Parameters",
                                             #ParameterDataSet, comment='')
        #self.groupbox.SIG_APPLY_BUTTON_CLICKED.connect(self.update_window)
        #self.groupbox.get()
        
        #self.setCentralWidget(self.groupbox)
        self.parameterWidget = DataSetEditGroupBox("Parameters",
                                             ParameterDataSet, comment='')
        self.parameterWidget.SIG_APPLY_BUTTON_CLICKED.connect(self.update_window)
        self.parameterWidget.get()
        
        
    def update_window(self):
        dataset = self.parameterWidget.dataset
        #dataset = self.groupbox.dataset
        print(dataset.threshold)
        print(dataset.use_inversion)
        
if __name__ == '__main__':
    from guidata.qt.QtGui import QApplication
    import sys
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())