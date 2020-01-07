import sys
from PyQt5 import QtWidgets, uic 


class MainWindow(QtWidgets.QMainWindow):
    """Class for the time-series view"""

    def __init__(self, *args, **kwargs):
        """ Initialization Routines """

        super(MainWindow, self).__init__(*args, **kwargs)

        #Load the UI Page
        uic.loadUi('JLT.ui', self)


        self.actionExit.triggered.connect( self.close )
        self.actionThomas.triggered.connect( self.show_thomas )
        self.actionloves.triggered.connect( self.show_loves )
        self.actionJean.triggered.connect( self.show_jean )

        # Set shortcuts
        self.actionThomas.setShortcut("Ctrl+T")
        self.actionloves.setShortcut("Ctrl+L")
        self.actionJean.setShortcut("Ctrl+J")

    def show_thomas(self):
        self.thomas = Thomas(self)
        self.setCentralWidget(self.thomas)

    def show_loves(self):
        self.loves = Loves(self)
        self.setCentralWidget(self.loves)

    def show_jean(self):
        self.jean = Jean(self)
        self.setCentralWidget(self.jean)


class Thomas(QtWidgets.QWidget):
    """ The central display Widget """    
    def __init__(self, mainWin):

        super(Thomas, self).__init__()

        #Load the UI Page
        uic.loadUi('Thomas.ui', self)

        self.pushButton.clicked.connect( mainWin.close )


class Loves(QtWidgets.QWidget):
    """ The central display Widget """    
    def __init__(self, mainWin):

        super(Loves, self).__init__()

        #Load the UI Page
        uic.loadUi('loves.ui', self)




class Jean(QtWidgets.QWidget):
    """ The central display Widget """    
    def __init__(self, mainWin):

        super(Jean, self).__init__()

        #Load the UI Page
        uic.loadUi('jean.ui', self)



def main():

    app = QtWidgets.QApplication(sys.argv)

    main_win = MainWindow()
    main_win.show()

    sys.exit(app.exec_())

if __name__ == '__main__':         
    main()
