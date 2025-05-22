#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Main window for Plot Digitizer
"""

import os
import sys
from PyQt5.QtWidgets import (QMainWindow, QAction, QFileDialog, QMessageBox,
                            QToolBar, QDockWidget, QWidget, QVBoxLayout,
                            QHBoxLayout, QLabel, QComboBox, QDoubleSpinBox,
                            QPushButton, QGroupBox, QFormLayout, QTabWidget,
                            QRadioButton, QButtonGroup, QSpinBox)
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtCore import Qt, QSettings

from models.project import Project
from models.curve_data import CurveData
from utils.axis import AxisType
from gui.image_view import ImageView
from gui.curve_editor import CurveEditor
from gui.export_dialog import ExportDialog

class MainWindow(QMainWindow):
    """Main window for the Plot Digitizer application"""
    
    def __init__(self):
        """Initialize the main window"""
        super().__init__()
        
        self.project = Project()
        self.current_curve_index = -1
        
        self.init_ui()
        self.init_actions()
        self.init_menus()
        self.init_toolbars()
        self.init_sidebar()
        
        self.setWindowTitle("Plot Digitizer")
        self.resize(1200, 800)
        
        # Restore window geometry from settings
        self.settings = QSettings("Plot Digitizer", "Plot Digitizer")
        geometry = self.settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)
    
    def init_ui(self):
        """Initialize the user interface"""
        # Central widget with image view
        self.image_view = ImageView(self)
        self.image_view.corner_points_changed.connect(self.on_corner_points_changed)
        self.setCentralWidget(self.image_view)
        
        # Status bar
        self.statusBar().showMessage("Ready")
    
    def init_actions(self):
        """Initialize actions for menus and toolbars"""
        # File actions
        self.action_new = QAction("New Project", self)
        self.action_new.setShortcut("Ctrl+N")
        self.action_new.triggered.connect(self.on_new_project)
        
        self.action_open = QAction("Open Project", self)
        self.action_open.setShortcut("Ctrl+O")
        self.action_open.triggered.connect(self.on_open_project)
        
        self.action_save = QAction("Save Project", self)
        self.action_save.setShortcut("Ctrl+S")
        self.action_save.triggered.connect(self.on_save_project)
        
        self.action_save_as = QAction("Save Project As...", self)
        self.action_save_as.setShortcut("Ctrl+Shift+S")
        self.action_save_as.triggered.connect(self.on_save_project_as)
        
        self.action_load_image = QAction("Load Image", self)
        self.action_load_image.triggered.connect(self.on_load_image)
        
        self.action_export = QAction("Export Data...", self)
        self.action_export.triggered.connect(self.on_export_data)
        self.action_export.setEnabled(False)
        
        self.action_exit = QAction("Exit", self)
        self.action_exit.setShortcut("Ctrl+Q")
        self.action_exit.triggered.connect(self.close)
        
        # Edit actions
        self.action_apply_perspective = QAction("Apply Perspective Correction", self)
        self.action_apply_perspective.triggered.connect(self.on_apply_perspective)
        self.action_apply_perspective.setEnabled(False)
        
        # View actions
        self.action_zoom_in = QAction("Zoom In", self)
        self.action_zoom_in.setShortcut("Ctrl++")
        self.action_zoom_in.triggered.connect(self.image_view.zoom_in)
        
        self.action_zoom_out = QAction("Zoom Out", self)
        self.action_zoom_out.setShortcut("Ctrl+-")
        self.action_zoom_out.triggered.connect(self.image_view.zoom_out)
        
        self.action_zoom_fit = QAction("Zoom to Fit", self)
        self.action_zoom_fit.triggered.connect(self.image_view.zoom_to_fit)
        
        # Curve actions
        self.action_add_curve = QAction("Add Curve", self)
        self.action_add_curve.triggered.connect(self.on_add_curve)
        self.action_add_curve.setEnabled(False)
        
        self.action_remove_curve = QAction("Remove Curve", self)
        self.action_remove_curve.triggered.connect(self.on_remove_curve)
        self.action_remove_curve.setEnabled(False)
    
    def init_menus(self):
        """Initialize menu bar"""
        # File menu
        file_menu = self.menuBar().addMenu("File")
        file_menu.addAction(self.action_new)
        file_menu.addAction(self.action_open)
        file_menu.addAction(self.action_save)
        file_menu.addAction(self.action_save_as)
        file_menu.addSeparator()
        file_menu.addAction(self.action_load_image)
        file_menu.addAction(self.action_export)
        file_menu.addSeparator()
        file_menu.addAction(self.action_exit)
        
        # Edit menu
        edit_menu = self.menuBar().addMenu("Edit")
        edit_menu.addAction(self.action_apply_perspective)
        
        # View menu
        view_menu = self.menuBar().addMenu("View")
        view_menu.addAction(self.action_zoom_in)
        view_menu.addAction(self.action_zoom_out)
        view_menu.addAction(self.action_zoom_fit)
        
        # Curve menu
        curve_menu = self.menuBar().addMenu("Curve")
        curve_menu.addAction(self.action_add_curve)
        curve_menu.addAction(self.action_remove_curve)
    
    def init_toolbars(self):
        """Initialize toolbars"""
        # File toolbar
        file_toolbar = QToolBar("File", self)
        file_toolbar.addAction(self.action_new)
        file_toolbar.addAction(self.action_open)
        file_toolbar.addAction(self.action_save)
        file_toolbar.addAction(self.action_load_image)
        self.addToolBar(file_toolbar)
        
        # View toolbar
        view_toolbar = QToolBar("View", self)
        view_toolbar.addAction(self.action_zoom_in)
        view_toolbar.addAction(self.action_zoom_out)
        view_toolbar.addAction(self.action_zoom_fit)
        self.addToolBar(view_toolbar)
        
        # Edit toolbar
        edit_toolbar = QToolBar("Edit", self)
        edit_toolbar.addAction(self.action_apply_perspective)
        self.addToolBar(edit_toolbar)
        
        # Curve toolbar
        curve_toolbar = QToolBar("Curve", self)
        curve_toolbar.addAction(self.action_add_curve)
        curve_toolbar.addAction(self.action_remove_curve)
        curve_toolbar.addAction(self.action_export)
        self.addToolBar(curve_toolbar)
    
    def init_sidebar(self):
        """Initialize sidebar with settings panels"""
        # Create dock widget
        dock = QDockWidget("Settings", self)
        dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        
        # Create tabs for different settings
        tabs = QTabWidget()
        
        # Perspective correction tab
        perspective_tab = QWidget()
        perspective_layout = QVBoxLayout(perspective_tab)
        
        perspective_group = QGroupBox("Perspective Correction")
        perspective_group_layout = QVBoxLayout(perspective_group)
        
        mark_corners_btn = QPushButton("Mark Corners")
        mark_corners_btn.clicked.connect(self.on_mark_corners)
        
        apply_perspective_btn = QPushButton("Apply Correction")
        apply_perspective_btn.clicked.connect(self.on_apply_perspective)
        
        perspective_group_layout.addWidget(mark_corners_btn)
        perspective_group_layout.addWidget(apply_perspective_btn)
        perspective_layout.addWidget(perspective_group)
        perspective_layout.addStretch()
        
        # Axis calibration tab
        axis_tab = QWidget()
        axis_layout = QVBoxLayout(axis_tab)
        
        # X-axis group
        x_axis_group = QGroupBox("X-Axis")
        x_axis_layout = QFormLayout(x_axis_group)
        
        self.x_axis_type = QComboBox()
        self.x_axis_type.addItems(["Linear", "Logarithmic"])
        self.x_axis_type.currentIndexChanged.connect(self.on_x_axis_type_changed)
        
        self.x_min_value = QDoubleSpinBox()
        self.x_min_value.setRange(-1e6, 1e6)
        self.x_min_value.setDecimals(6)
        self.x_min_value.setValue(0)
        self.x_min_value.valueChanged.connect(self.on_x_axis_changed)
        
        self.x_max_value = QDoubleSpinBox()
        self.x_max_value.setRange(-1e6, 1e6)
        self.x_max_value.setDecimals(6)
        self.x_max_value.setValue(1)
        self.x_max_value.valueChanged.connect(self.on_x_axis_changed)
        
        mark_x_axis_btn = QPushButton("Mark X-Axis Limits")
        mark_x_axis_btn.clicked.connect(self.on_mark_x_axis)
        
        x_axis_layout.addRow("Type:", self.x_axis_type)
        x_axis_layout.addRow("Min Value:", self.x_min_value)
        x_axis_layout.addRow("Max Value:", self.x_max_value)
        x_axis_layout.addRow(mark_x_axis_btn)
        
        # Y-axis group
        y_axis_group = QGroupBox("Y-Axis")
        y_axis_layout = QFormLayout(y_axis_group)
        
        self.y_axis_type = QComboBox()
        self.y_axis_type.addItems(["Linear", "Logarithmic"])
        self.y_axis_type.currentIndexChanged.connect(self.on_y_axis_type_changed)
        
        self.y_min_value = QDoubleSpinBox()
        self.y_min_value.setRange(-1e6, 1e6)
        self.y_min_value.setDecimals(6)
        self.y_min_value.setValue(0)
        self.y_min_value.valueChanged.connect(self.on_y_axis_changed)
        
        self.y_max_value = QDoubleSpinBox()
        self.y_max_value.setRange(-1e6, 1e6)
        self.y_max_value.setDecimals(6)
        self.y_max_value.setValue(1)
        self.y_max_value.valueChanged.connect(self.on_y_axis_changed)
        
        mark_y_axis_btn = QPushButton("Mark Y-Axis Limits")
        mark_y_axis_btn.clicked.connect(self.on_mark_y_axis)
        
        y_axis_layout.addRow("Type:", self.y_axis_type)
        y_axis_layout.addRow("Min Value:", self.y_min_value)
        y_axis_layout.addRow("Max Value:", self.y_max_value)
        y_axis_layout.addRow(mark_y_axis_btn)
        
        axis_layout.addWidget(x_axis_group)
        axis_layout.addWidget(y_axis_group)
        axis_layout.addStretch()
        
        # Curve tab
        curve_tab = QWidget()
        curve_layout = QVBoxLayout(curve_tab)
        
        # Curve selection group
        curve_selection_group = QGroupBox("Curve Selection")
        curve_selection_layout = QHBoxLayout(curve_selection_group)
        
        self.curve_combo = QComboBox()
        self.curve_combo.currentIndexChanged.connect(self.on_curve_selected)
        
        add_curve_btn = QPushButton("Add")
        add_curve_btn.clicked.connect(self.on_add_curve)
        
        remove_curve_btn = QPushButton("Remove")
        remove_curve_btn.clicked.connect(self.on_remove_curve)
        
        curve_selection_layout.addWidget(self.curve_combo)
        curve_selection_layout.addWidget(add_curve_btn)
        curve_selection_layout.addWidget(remove_curve_btn)
        
        # Curve editor
        self.curve_editor = CurveEditor(self)
        
        # Data export group
        export_group = QGroupBox("Data Export")
        export_layout = QVBoxLayout(export_group)
        
        sampling_layout = QHBoxLayout()
        self.uniform_sampling = QRadioButton("Uniform")
        self.adaptive_sampling = QRadioButton("Adaptive")
        self.uniform_sampling.setChecked(True)
        
        sampling_group = QButtonGroup(self)
        sampling_group.addButton(self.uniform_sampling)
        sampling_group.addButton(self.adaptive_sampling)
        
        sampling_layout.addWidget(self.uniform_sampling)
        sampling_layout.addWidget(self.adaptive_sampling)
        
        # Sampling parameters
        params_layout = QFormLayout()
        
        self.num_points = QSpinBox()
        self.num_points.setRange(10, 10000)
        self.num_points.setValue(100)
        
        self.max_error = QDoubleSpinBox()
        self.max_error.setRange(0.01, 10.0)
        self.max_error.setValue(0.5)
        self.max_error.setDecimals(2)
        
        params_layout.addRow("Number of Points:", self.num_points)
        params_layout.addRow("Max Error:", self.max_error)
        
        export_btn = QPushButton("Export Data...")
        export_btn.clicked.connect(self.on_export_data)
        
        export_layout.addLayout(sampling_layout)
        export_layout.addLayout(params_layout)
        export_layout.addWidget(export_btn)
        
        curve_layout.addWidget(curve_selection_group)
        curve_layout.addWidget(self.curve_editor)
        curve_layout.addWidget(export_group)
        curve_layout.addStretch()
        
        # Add tabs to the tab widget
        tabs.addTab(perspective_tab, "Perspective")
        tabs.addTab(axis_tab, "Axes")
        tabs.addTab(curve_tab, "Curves")
        
        # Set the tab widget as the dock widget's content
        dock.setWidget(tabs)
        
        # Add the dock widget to the main window
        self.addDockWidget(Qt.RightDockWidgetArea, dock)
    
    def on_new_project(self):
        """Handle new project action"""
        # Check if current project should be saved
        if not self.check_save_current():
            return
        
        # Create new project
        self.project = Project()
        self.current_curve_index = -1
        
        # Update UI
        self.image_view.set_image(None)
        self.image_view.set_corner_points(None)
        self.update_curve_combo()
        self.update_ui_state()
        
        self.statusBar().showMessage("New project created")
    
    def on_open_project(self):
        """Handle open project action"""
        # Check if current project should be saved
        if not self.check_save_current():
            return
        
        # Get filename from dialog
        filename, _ = QFileDialog.getOpenFileName(
            self, "Open Project", "", "Plot Digitizer Project (*.pdp)")
        
        if not filename:
            return
        
        # Load project
        project = Project.load(filename)
        if project is None:
            QMessageBox.critical(self, "Error", "Failed to load project")
            return
        
        # Update UI with loaded project
        self.project = project
        self.current_curve_index = -1
        
        # Show the image
        if self.project.transformed_image is not None:
            self.image_view.set_image(self.project.transformed_image)
        else:
            self.image_view.set_image(self.project.image)
        
        # Set corner points
        self.image_view.set_corner_points(self.project.corner_points)
        
        # Update axis settings
        self.update_axis_controls()
        
        # Update curve list
        self.update_curve_combo()
        
        # Update UI state
        self.update_ui_state()
        
        self.statusBar().showMessage(f"Opened project: {filename}")
    
    def on_save_project(self):
        """Handle save project action"""
        if self.project.filename:
            self.save_project(self.project.filename)
        else:
            self.on_save_project_as()
    
    def on_save_project_as(self):
        """Handle save project as action"""
        # Get filename from dialog
        filename, _ = QFileDialog.getSaveFileName(
            self, "Save Project", "", "Plot Digitizer Project (*.pdp)")
        
        if not filename:
            return
        
        # Add extension if not present
        if not filename.endswith(".pdp"):
            filename += ".pdp"
        
        self.save_project(filename)
    
    def save_project(self, filename):
        """Save the project to a file"""
        # Save the project
        if not self.project.save(filename):
            QMessageBox.critical(self, "Error", "Failed to save project")
            return
        
        self.statusBar().showMessage(f"Project saved to: {filename}")
    
    def on_load_image(self):
        """Handle load image action"""
        # Get image filename from dialog
        filename, _ = QFileDialog.getOpenFileName(
            self, "Load Image", "", "Images (*.png *.jpg *.jpeg *.bmp *.tif *.tiff)")
        
        if not filename:
            return
        
        # Load the image
        if not self.project.load_image(filename):
            QMessageBox.critical(self, "Error", "Failed to load image")
            return
        
        # Show the image
        self.image_view.set_image(self.project.image)
        
        # Reset corner points
        self.image_view.set_corner_points(None)
        
        # Update UI state
        self.update_ui_state()
        
        self.statusBar().showMessage(f"Loaded image: {filename}")
    
    def on_mark_corners(self):
        """Handle mark corners button"""
        # Enable corner marking mode in the image view
        self.image_view.start_marking_corners()
        self.statusBar().showMessage("Mark the four corners of the plot (clockwise from top-left)")
    
    def on_corner_points_changed(self, points):
        """Handle corner points changed in the image view"""
        # Update the project with the new corner points
        self.project.set_corner_points(points)
        
        # Enable the apply perspective action
        self.action_apply_perspective.setEnabled(True)
        
        self.statusBar().showMessage("Corner points updated")
    
    def on_apply_perspective(self):
        """Handle apply perspective correction action"""
        if self.project.corner_points is None or len(self.project.corner_points) != 4:
            QMessageBox.warning(self, "Warning", "Please mark the four corners first")
            return
        
        # Apply perspective correction
        if not self.project.apply_perspective_correction():
            QMessageBox.critical(self, "Error", "Failed to apply perspective correction")
            return
        
        # Show the transformed image
        self.image_view.set_image(self.project.transformed_image)
        
        # Enable axis and curve actions
        self.action_add_curve.setEnabled(True)
        
        self.statusBar().showMessage("Perspective correction applied")
    
    def on_mark_x_axis(self):
        """Handle mark X-axis limits button"""
        # Enable axis marking mode in the image view
        self.image_view.start_marking_axis("x")
        self.statusBar().showMessage("Mark the minimum and maximum points on the X-axis")
    
    def on_mark_y_axis(self):
        """Handle mark Y-axis limits button"""
        # Enable axis marking mode in the image view
        self.image_view.start_marking_axis("y")
        self.statusBar().showMessage("Mark the minimum and maximum points on the Y-axis")
    
    def on_x_axis_type_changed(self, index):
        """Handle X-axis type changed"""
        axis_type = AxisType.LINEAR if index == 0 else AxisType.LOGARITHMIC
        
        # Check if values need adjustment for logarithmic scale
        if axis_type == AxisType.LOGARITHMIC:
            if self.x_min_value.value() <= 0:
                self.x_min_value.setValue(0.1)
            if self.x_max_value.value() <= 0:
                self.x_max_value.setValue(10.0)
        
        # Update the project's X-axis type
        self.project.x_axis.axis_type = axis_type
        
        # Update calibration
        self.on_x_axis_changed()
    
    def on_y_axis_type_changed(self, index):
        """Handle Y-axis type changed"""
        axis_type = AxisType.LINEAR if index == 0 else AxisType.LOGARITHMIC
        
        # Check if values need adjustment for logarithmic scale
        if axis_type == AxisType.LOGARITHMIC:
            if self.y_min_value.value() <= 0:
                self.y_min_value.setValue(0.1)
            if self.y_max_value.value() <= 0:
                self.y_max_value.setValue(10.0)
        
        # Update the project's Y-axis type
        self.project.y_axis.axis_type = axis_type
        
        # Update calibration
        self.on_y_axis_changed()
    
    def on_x_axis_changed(self):
        """Handle X-axis settings changed"""
        # Update the project's X-axis calibration
        self.project.x_axis.set_calibration(
            self.project.x_axis.min_pixel,
            self.project.x_axis.max_pixel,
            self.x_min_value.value(),
            self.x_max_value.value()
        )
    
    def on_y_axis_changed(self):
        """Handle Y-axis settings changed"""
        # Update the project's Y-axis calibration
        self.project.y_axis.set_calibration(
            self.project.y_axis.min_pixel,
            self.project.y_axis.max_pixel,
            self.y_min_value.value(),
            self.y_max_value.value()
        )
    
    def update_axis_controls(self):
        """Update the axis control values from the project"""
        # Block signals to avoid triggering callbacks
        self.x_axis_type.blockSignals(True)
        self.y_axis_type.blockSignals(True)
        self.x_min_value.blockSignals(True)
        self.x_max_value.blockSignals(True)
        self.y_min_value.blockSignals(True)
        self.y_max_value.blockSignals(True)
        
        # Update X-axis controls
        self.x_axis_type.setCurrentIndex(0 if self.project.x_axis.axis_type == AxisType.LINEAR else 1)
        self.x_min_value.setValue(self.project.x_axis.min_value)
        self.x_max_value.setValue(self.project.x_axis.max_value)
        
        # Update Y-axis controls
        self.y_axis_type.setCurrentIndex(0 if self.project.y_axis.axis_type == AxisType.LINEAR else 1)
        self.y_min_value.setValue(self.project.y_axis.min_value)
        self.y_max_value.setValue(self.project.y_axis.max_value)
        
        # Unblock signals
        self.x_axis_type.blockSignals(False)
        self.y_axis_type.blockSignals(False)
        self.x_min_value.blockSignals(False)
        self.x_max_value.blockSignals(False)
        self.y_min_value.blockSignals(False)
        self.y_max_value.blockSignals(False)
    
    def on_add_curve(self):
        """Handle add curve action"""
        # Add a new curve to the project
        curve_index = self.project.add_curve()
        
        # Update the curve combo box
        self.update_curve_combo()
        
        # Select the new curve and explicitly trigger curve selection
        self.curve_combo.setCurrentIndex(curve_index)
        self.on_curve_selected(curve_index)  # Explicitly call this
        
        # Enable the curve editor
        self.curve_editor.set_enabled(True)
        
        self.statusBar().showMessage("Added new curve")
    
    def on_remove_curve(self):
        """Handle remove curve action"""
        if self.current_curve_index < 0:
            return
        
        # Remove the current curve
        if not self.project.remove_curve(self.current_curve_index):
            return
        
        # Update the curve combo box
        self.update_curve_combo()
        
        # Update the current curve index
        if self.curve_combo.count() > 0:
            self.curve_combo.setCurrentIndex(0)
        else:
            self.current_curve_index = -1
            self.curve_editor.set_enabled(False)
        
        self.statusBar().showMessage("Removed curve")
    
    def on_curve_selected(self, index):
        """Handle curve selection changed"""
        if index < 0:
            self.current_curve_index = -1
            self.curve_editor.set_enabled(False)
            # Make sure image view exits edit mode
            self.image_view.mode = "view"
            self.image_view.setCursor(Qt.ArrowCursor)
            self.image_view.setDragMode(self.image_view.ScrollHandDrag)
            return
        
        # Update the current curve index
        self.current_curve_index = index
        
        # Get the selected curve
        curve = self.project.get_curve(index)
        if curve is None:
            self.curve_editor.set_enabled(False)
            return
        
        # Set the curve in the editor
        self.curve_editor.set_curve(curve)
        self.curve_editor.set_enabled(True)
        
        # Synchronize edit mode state
        if self.curve_editor.edit_knots_btn.isChecked():
            # If edit mode button is checked, ensure image view is in edit mode
            self.image_view.start_editing_curve(curve)
        else:
            # If edit mode button is not checked, ensure image view is in view mode
            self.image_view.mode = "view"
            self.image_view.setCursor(Qt.ArrowCursor)
            self.image_view.setDragMode(self.image_view.ScrollHandDrag)
        
        # Enable the remove curve and export actions
        self.action_remove_curve.setEnabled(True)
        self.action_export.setEnabled(True)
    
    def update_curve_combo(self):
        """Update the curve combo box with the current curves"""
        # Remember the current selected curve index
        current_index = self.current_curve_index
        
        # Block signals to avoid triggering callbacks during update
        self.curve_combo.blockSignals(True)
        
        # Clear the combo box
        self.curve_combo.clear()
        
        # Add curve items
        for i in range(len(self.project.curves)):
            self.curve_combo.addItem(f"Curve {i+1}")
        
        # Unblock signals
        self.curve_combo.blockSignals(False)
        
        # Restore or set selection if curves exist
        if len(self.project.curves) > 0:
            if current_index >= 0 and current_index < len(self.project.curves):
                self.curve_combo.setCurrentIndex(current_index)
                # Don't call on_curve_selected here as it will be called by setCurrentIndex
            else:
                # No valid current curve, select the first one
                self.curve_combo.setCurrentIndex(0)
                self.on_curve_selected(0)
        else:
            # No curves, ensure everything is reset
            self.current_curve_index = -1
            self.on_curve_selected(-1)
        
        # Update UI state
        self.update_ui_state()
    
    def on_export_data(self):
        """Handle export data action"""
        if self.current_curve_index < 0:
            return
        
        # Get the selected curve
        curve = self.project.get_curve(self.current_curve_index)
        if curve is None:
            return
        
        # Create curve data model
        curve_data = CurveData(curve, self.project.x_axis, self.project.y_axis)
        
        # Sample the curve based on selected method
        if self.uniform_sampling.isChecked():
            data = curve_data.sample_uniform(self.num_points.value())
        else:
            data = curve_data.sample_adaptive(self.max_error.value())
        
        # Show export dialog
        dialog = ExportDialog(self, curve_data)
        dialog.exec_()
    
    def update_ui_state(self):
        """Update the enabled state of UI elements based on current state"""
        has_image = self.project.image is not None
        has_transformed = self.project.transformed_image is not None
        has_corners = self.project.corner_points is not None and len(self.project.corner_points) == 4
        has_curves = len(self.project.curves) > 0
        has_current_curve = self.current_curve_index >= 0
        
        # File actions
        self.action_save.setEnabled(True)
        self.action_save_as.setEnabled(True)
        self.action_export.setEnabled(has_current_curve)
        
        # Edit actions
        self.action_apply_perspective.setEnabled(has_image and has_corners)
        
        # View actions
        self.action_zoom_in.setEnabled(has_image)
        self.action_zoom_out.setEnabled(has_image)
        self.action_zoom_fit.setEnabled(has_image)
        
        # Curve actions
        self.action_add_curve.setEnabled(has_transformed)
        self.action_remove_curve.setEnabled(has_current_curve)
    
    def check_save_current(self):
        """Check if the current project should be saved before proceeding"""
        # If no image is loaded, no need to save
        if self.project.image is None:
            return True
        
        # Ask user if they want to save
        reply = QMessageBox.question(
            self, "Save Project?",
            "Do you want to save the current project?",
            QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
            QMessageBox.Save)
        
        if reply == QMessageBox.Cancel:
            return False
        elif reply == QMessageBox.Save:
            self.on_save_project()
        
        return True
    
    def closeEvent(self, event):
        """Handle window close event"""
        # Save window geometry
        self.settings.setValue("geometry", self.saveGeometry())
        
        # Check if current project should be saved
        if not self.check_save_current():
            event.ignore()
            return
        
        event.accept()
