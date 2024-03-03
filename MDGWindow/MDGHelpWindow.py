# This Python file uses the following encoding: utf-8
import sys
import webbrowser

from PySide6.QtWidgets import QApplication, QMainWindow

from MDGWindow.MDGMdkWindow import MDGMdkWindow
from MDGui.Ui_MDGHelpWindow import Ui_MDGHelpWindow


class MDGHelpWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_MDGHelpWindow()
        self.ui.setupUi(self)

        self.ui.mdk_button.clicked.connect(self.open_minecraft_forge)
        self.ui.mdk_help_download_button.clicked.connect(self.open_mdk_help)
        self.ui.close_button.clicked.connect(self.hide)

    def open_minecraft_forge(self):
        webbrowser.open('https://files.minecraftforge.net/net/minecraftforge/forge/')

    def open_mdk_help(self):
        self.mdk_help_window = MDGMdkWindow()
        self.mdk_help_window.show()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = MDGHelpWindow()
    widget.show()
    sys.exit(app.exec())