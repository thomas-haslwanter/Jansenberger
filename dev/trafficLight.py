from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt, QTimer
import sys
import yaml
import time
import numpy as np


from PyQt5 import QtCore
from PyQt5 import QtGui

import guidata
from guidata.dataset.dataitems import ChoiceItem
from guidata.dataset.datatypes import DataSet


def get_subjects():
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


class Subjects(DataSet):
    """
    Select Experimentor and Subject
    """
    sub, exp = get_subjects()
    
    _Experimentor = ChoiceItem("Experimentors", exp)
    _Subject = ChoiceItem("Subjects",sub )
                     

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
        dial = self.parent()._dial
        vmin, vmax = dial.minimum(), dial.maximum()
        value = dial.value()
        
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
            if ii == int(value / 33):
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

        
class TrafficLight(QtWidgets.QWidget):
    """
    Custom Qt Widget to show a power bar and dial.
    Demonstrating compound and custom-drawn widget.
    """

    def __init__(self, steps=5, *args, **kwargs):
        super(TrafficLight, self).__init__(*args, **kwargs)
        
        layout = QtWidgets.QVBoxLayout()
        self._light = _Light()
        layout.addWidget(self._light)
        
        self._dial = QtWidgets.QDial()
        self._dial.valueChanged.connect( self._light._trigger_refresh )
        layout.addWidget(self._dial)
        self.setLayout(layout)

if __name__ == '__main__':

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
    
    _app = guidata.qapplication()
                    
    sub, exp = get_subjects()
    
    e = Subjects()
    e.edit()
    e.view()
    
    tv_win = TrafficLight()
    tv_win.show()
    
    sys.exit(app.exec_())
