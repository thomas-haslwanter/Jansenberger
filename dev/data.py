import sys

from PyQt5 import QtWidgets, uic 
import guidata.dataset.datatypes as dt
import guidata.dataset.dataitems as di
from guidata.dataset.qtwidgets import DataSetEditGroupBox

class OtherDataSet(dt.DataSet):
    title = di.StringItem("Title", default="Title")
    opacity = di.FloatItem("Opacity", default=1., min=.1, max=1)

    
class MainWindow(QtWidgets.QMainWindow):
    """Class for the data view"""

    def __init__(self, *args, **kwargs):
        """ Initialization Routines """

        #super(MainWindow, self).__init__(*args, **kwargs)
        QtWidgets.QMainWindow.__init__(self)

        #Load the UI Page
        #uic.loadUi('data.ui', self)
        
        self.groupbox = DataSetEditGroupBox('Threshold Parameters', OtherDataSet, comment='')
        self.groupbox.SIG_APPLY_BUTTON_CLICKED.connect( self.close ) 
        
        self.dataWidget = self.groupbox
        
        self.pushButton.clicked.connect( self.close )


def main():

    app = QtWidgets.QApplication(sys.argv)

    main_win = MainWindow()
    main_win.show()

    sys.exit(app.exec_())

if __name__ == '__main__':         
    main()
