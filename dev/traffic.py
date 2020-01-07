from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt
import sys

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
        
        
        #brush = QtGui.QBrush()
        #brush.setColor(QtGui.QColor('black'))
        #brush.setStyle(Qt.SolidPattern)
        #rect = QtCore.QRect(0, 0, painter.device().width(), painter.device().height())
        #painter.fillRect(rect, brush)
        
        # Get current state.
        dial = self.parent()._dial
        vmin, vmax = dial.minimum(), dial.maximum()
        value = dial.value()
        
        padding = 5
        
        # Define our canvas.
        d_height = painter.device().height() - (padding * 2)
        d_width = painter.device().width() - (padding * 2)
        
        # Draw the trafficlight
        height = painter.device().height()
        width = painter.device().width()
        middle = width/2
        
        outer_padding = 5
        inner_padding = 2
        
        
        diameter = ((height - 2*outer_padding) - 4*inner_padding)/3
        box = (diameter + 4*inner_padding,  height - 2*outer_padding)
        top_left = [middle - box['width']/2, outer_padding]
        
        pen = QtGui.QPen()
        pen.setColor(QtGui.QColor('black'))
        pen.setWidth(5)
        
        painter.drawRect(*top_left, *box)
        
        # Draw the bars.
        #step_size = d_height / 5
        
        #bar_height = step_size * 0.6
        #bar_spacer = step_size * 0.4 / 2
        
        #pc = (value - vmin) / (vmax - vmin)
        #n_steps_to_draw = int(pc * 5)
        #brush.setColor(QtGui.QColor('red'))
        #for n in range(n_steps_to_draw):
             #rect = QtCore.QRect(
                 #padding,
                 #padding + d_height - ((n+1) * step_size) + bar_spacer,
                 #d_width,
                 #bar_height
                 #)
             #painter.fillRect(rect, brush)

        painter.end()

    def _trigger_refresh(self):
         self.update()


class Traffic(QtWidgets.QWidget):
    """
    Custom Qt Widget to show a power bar and dial.
    Demonstrating compound and custom-drawn widget.
    """
    
    def __init__(self, steps=5, *args, **kwargs):
        super(Traffic, self).__init__(*args, **kwargs)
        
        layout = QtWidgets.QVBoxLayout()
        self._bar = _Bar()
        layout.addWidget(self._bar)
        
        self._dial = QtWidgets.QDial()
        self._dial.valueChanged.connect( self._bar._trigger_refresh )
        layout.addWidget(self._dial)
        self.setLayout(layout)


if __name__ == '__main__':

    app = QtWidgets.QApplication(sys.argv)

    bar = Traffic()
    bar.show()

    sys.exit(app.exec_())