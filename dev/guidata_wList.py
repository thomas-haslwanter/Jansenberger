import sys
import time

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt

from guidata.qt.QtGui import (QApplication, QMainWindow,
                              QVBoxLayout, QWidget, QListView)
from guidata.dataset import dataitems as di
from guidata.dataset.datatypes import DataSet
from guidata.dataset.dataitems import (ChoiceItem, FloatItem) 
from guidata.dataset.qtwidgets import DataSetEditGroupBox
from guidata.configtools import get_icon


class ParameterDataSet(DataSet):
    """Interactive setting of the experimental parameters"""
    
    threshold = di.FloatItem("Threshold", default=1., min=.5, max=1.5)
    repetitions = di.IntItem("Repetitions", default=10, min=2, max=50)
    direction = di.ChoiceItem("Axis", ['x', 'y', 'z'])
    use_absVal = di.BoolItem("yes", 'Absolute Value')
    use_inversion = di.BoolItem("yes", 'Invert Signal')
    


class TodoModel(QtCore.QAbstractListModel):
    """Qt-Model for the list of performed experiments"""
    
    def __init__(self, *args, todos=None, **kwargs):
        super(TodoModel, self).__init__(*args, **kwargs)
        self.todos = todos or []
        
        
    def data(self, index, role):
        """Required function for a Qt-model"""
        
        if role == Qt.DisplayRole:
            _, text = self.todos[index.row()]
            return text
        
        if role == Qt.DecorationRole:
            status, _ = self.todos[index.row()]
            if status:
                return tick

    def rowCount(self, index):
        """Required function for a Qt-model"""
        
        return len(self.todos)



class MainWindow(QMainWindow):
    """Qt-Window for the display"""
    
    def __init__(self):
        QMainWindow.__init__(self)
        self.setWindowIcon(get_icon('python.png'))
        self.setWindowTitle("Application example")
        
        layout = QVBoxLayout()
        
        # Instantiate dataset-related widgets:
        self.groupbox = DataSetEditGroupBox("Parameters",
                                             ParameterDataSet, comment='')
        self.groupbox.SIG_APPLY_BUTTON_CLICKED.connect( self.clear )
        self.groupbox.get()
        
        #self.setCentralWidget(self.groupbox)
        layout.addWidget(self.groupbox)
        self.exerciseView = QListView()
        layout.addWidget(self.exerciseView)
        
        widget = QWidget()
        widget.setLayout( layout )
        self.setCentralWidget(widget)
        
        self.model = TodoModel()
        self.exerciseView.setModel(self.model)
        
        
    def add(self, text):
        """ Add an item to our todo list, getting the text from the input """
        
        # Access the list via the model.
        self.model.todos.append((False, text))
        # Trigger refresh.        
        self.model.layoutChanged.emit()
            
        
    def complete(self, row):
        #row = index.row()
        status, text = self.model.todos[row]
        self.model.todos[row] = (True, text)
        # .dataChanged takes top-left and bottom right, which are equal 
        # for a single selection.
        #self.model.dataChanged.emit(index, index)
        # Clear the selection (as it is no longer valid).
        
        
    def clear(self):
        self.model.todos = []
        self.model.layoutChanged.emit()
        
            
    def update_window(self):
        dataset = self.groupbox.dataset
        print(dataset.threshold)
        print(dataset.use_inversion)
        
if __name__ == '__main__':
    
    tick = QtGui.QImage('tick.png')
    app = QApplication(sys.argv)
    
    window = MainWindow()
    window.add('this is funny')
    window.add('this is NOT funny')
    window.complete(1)
    window.show()
    
    #app.exec_()
    sys.exit(app.exec_())