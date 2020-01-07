import sys
from PyQt5 import QtWidgets, uic 
from PyQt5.QtCore import Qt
#import pyqtgraph as pg
from pyqtgraph.Qt import QtGui, QtCore
import time
import yaml

class MainWindow(QtWidgets.QMainWindow):
    """Class for the time-series view"""

    def __init__(self, *args, **kwargs):
        """ Initialization Routines """

        super(MainWindow, self).__init__(*args, **kwargs)

        #Load the UI Page
        uic.loadUi('stacking.ui', self)

        self.light = _Light()
        self.stackedWidget.addWidget( self.light )
        self.oneButton.clicked.connect( self.show_0 )
        self.twoButton.clicked.connect( self.show_1 )
        
        # Timer for updating the display
        timer = QtCore.QTimer()
        timer.timeout.connect( self.light._trigger_refresh )
        timer.start(10) 


    def show_0(self):
        self.stackedWidget.setCurrentIndex(0)
        
    def show_1(self):
        self.stackedWidget.setCurrentIndex(1)
        
        
class _Light(QtWidgets.QWidget):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setSizePolicy(
         QtWidgets.QSizePolicy.MinimumExpanding,
         QtWidgets.QSizePolicy.MinimumExpanding
         )

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
        pen.setWidth(10)
        
        painter.drawRect(*top_left, *box)
        
        # Get current state.
        value = int(time.time()) % 3
        print(value)
        
        # Draw the lights.
        settings_file = 'settings.yaml'
        with open(settings_file, 'r') as fh_settings:
            settings = yaml.load(fh_settings, Loader=yaml.FullLoader)
        # colors = [QtGui.QColor('red'), QtGui.QColor('red'), QtGui.QColor('green')]
        colors = [QtGui.QColor(settings['topColor']),
                  QtGui.QColor(settings['middleColor']),
                  QtGui.QColor(settings['bottomColor'])]

        brush = QtGui.QBrush()
        brush.setStyle(Qt.SolidPattern)
        #brush.setColor(QtGui.QColor('red'))
        for ii in range(3):
            if ii == value :
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
        print('hi')
        self.update()

        
def main():
    app = QtWidgets.QApplication(sys.argv)

    main_win = MainWindow()
    main_win.show()
    

    sys.exit(app.exec_())

if __name__ == '__main__':         
    main()
