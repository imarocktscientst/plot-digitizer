#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Plot Digitizer - A tool to extract data from plot images
"""

import sys
import os
from PyQt5.QtWidgets import QApplication
from gui.main_window import MainWindow

def main():
    """Main entry point for the application"""
    # Create the Qt Application
    app = QApplication(sys.argv)
    app.setApplicationName("Plot Digitizer")
    app.setOrganizationName("Plot Digitizer")
    
    # Create and show the main window
    main_win = MainWindow()
    main_win.show()
    
    # Start the event loop
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
