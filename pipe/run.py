from PySide2 import QtWidgets
from main_gui import PipelineGUI

if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    gui = PipelineGUI()
    gui.show()
    app.exec_()
