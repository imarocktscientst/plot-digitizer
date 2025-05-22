#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Curve editor widget for Plot Digitizer
"""

import numpy as np
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                           QListWidget, QPushButton, QFormLayout, QDoubleSpinBox,
                           QGroupBox, QCheckBox, QSlider, QMessageBox)
from PyQt5.QtCore import Qt

class CurveEditor(QWidget):
    """Widget for editing NURBS curves"""
    
    def __init__(self, parent=None):
        """Initialize the curve editor"""
        super().__init__(parent)
        
        self.parent = parent
        self.curve = None
        
        self.init_ui()
        
        # Disable the widget until a curve is selected
        self.set_enabled(False)
    
    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout(self)
        
        # Knot list group
        knot_group = QGroupBox("Knot Points")
        knot_layout = QVBoxLayout(knot_group)
        
        # Knot list
        self.knot_list = QListWidget()
        self.knot_list.currentRowChanged.connect(self.on_knot_selected)
        
        # Knot list buttons
        knot_btn_layout = QHBoxLayout()
        
        self.add_knot_btn = QPushButton("Add")
        self.add_knot_btn.clicked.connect(self.on_add_knot)
        
        self.remove_knot_btn = QPushButton("Remove")
        self.remove_knot_btn.clicked.connect(self.on_remove_knot)
        self.remove_knot_btn.setEnabled(False)
        
        self.edit_knots_btn = QPushButton("Edit Mode")
        self.edit_knots_btn.setCheckable(True)
        self.edit_knots_btn.clicked.connect(self.on_edit_knots)
        
        knot_btn_layout.addWidget(self.add_knot_btn)
        knot_btn_layout.addWidget(self.remove_knot_btn)
        knot_btn_layout.addWidget(self.edit_knots_btn)
        
        knot_layout.addWidget(self.knot_list)
        knot_layout.addLayout(knot_btn_layout)
        
        # Knot properties group
        prop_group = QGroupBox("Knot Properties")
        prop_layout = QFormLayout(prop_group)
        
        # Position
        pos_layout = QHBoxLayout()
        
        self.x_pos = QDoubleSpinBox()
        self.x_pos.setRange(0, 10000)
        self.x_pos.setDecimals(1)
        self.x_pos.valueChanged.connect(self.on_position_changed)
        
        self.y_pos = QDoubleSpinBox()
        self.y_pos.setRange(0, 10000)
        self.y_pos.setDecimals(1)
        self.y_pos.valueChanged.connect(self.on_position_changed)
        
        pos_layout.addWidget(QLabel("X:"))
        pos_layout.addWidget(self.x_pos)
        pos_layout.addWidget(QLabel("Y:"))
        pos_layout.addWidget(self.y_pos)
        
        # Tension
        tension_layout = QHBoxLayout()
        
        self.tension = QSlider(Qt.Horizontal)
        self.tension.setRange(0, 100)
        self.tension.setValue(0)
        self.tension.valueChanged.connect(self.on_tension_changed)
        
        self.tension_value = QLabel("0.0")
        
        tension_layout.addWidget(self.tension)
        tension_layout.addWidget(self.tension_value)
        
        # Manual tangent
        tangent_layout = QHBoxLayout()
        
        self.manual_tangent = QCheckBox("Manual Tangent")
        self.manual_tangent.stateChanged.connect(self.on_manual_tangent_changed)
        
        tangent_layout.addWidget(self.manual_tangent)
        
        # Tangent angle
        angle_layout = QHBoxLayout()
        
        self.tangent_angle = QDoubleSpinBox()
        self.tangent_angle.setRange(-360, 360)
        self.tangent_angle.setDecimals(1)
        self.tangent_angle.setSingleStep(15)
        self.tangent_angle.setValue(0)
        self.tangent_angle.setEnabled(False)
        self.tangent_angle.valueChanged.connect(self.on_tangent_angle_changed)
        
        angle_layout.addWidget(QLabel("Angle:"))
        angle_layout.addWidget(self.tangent_angle)
        angle_layout.addWidget(QLabel("°"))
        
        # Tangent magnitude
        magnitude_layout = QHBoxLayout()
        
        self.tangent_magnitude = QDoubleSpinBox()
        self.tangent_magnitude.setRange(0.1, 10)
        self.tangent_magnitude.setDecimals(1)
        self.tangent_magnitude.setSingleStep(0.1)
        self.tangent_magnitude.setValue(1.0)
        self.tangent_magnitude.setEnabled(False)
        self.tangent_magnitude.valueChanged.connect(self.on_tangent_magnitude_changed)
        
        magnitude_layout.addWidget(QLabel("Magnitude:"))
        magnitude_layout.addWidget(self.tangent_magnitude)
        
        # Add fields to form layout
        prop_layout.addRow("Position:", pos_layout)
        prop_layout.addRow("Tension:", tension_layout)
        prop_layout.addRow(tangent_layout)
        prop_layout.addRow(angle_layout)
        prop_layout.addRow(magnitude_layout)
        
        # Add groups to main layout
        layout.addWidget(knot_group)
        layout.addWidget(prop_group)
        layout.addStretch()
    
    def set_curve(self, curve):
        """
        Set the curve to edit
        
        Args:
            curve: NurbsCurve object
        """
        self.curve = curve
        
        # Reset edit mode button to unchecked state
        self.edit_knots_btn.setChecked(False)
        
        self.update_knot_list()
    
    def set_enabled(self, enabled):
        """
        Enable or disable the editor
        
        Args:
            enabled: Boolean flag
        """
        self.setEnabled(enabled)
        
        if not enabled:
            self.curve = None
            self.knot_list.clear()
            self.edit_knots_btn.setChecked(False)
            # Make sure we exit edit mode in the image view
            if hasattr(self.parent, 'image_view'):
                self.parent.image_view.mode = "view"
                self.parent.image_view.setCursor(Qt.ArrowCursor)
                self.parent.image_view.setDragMode(self.parent.image_view.ScrollHandDrag)
    
    def update_knot_list(self):
        """Update the knot list with current knots from the curve"""
        if self.curve is None:
            return
        
        # Remember the current selected row
        current_row = self.knot_list.currentRow()
        
        # Block signals to avoid triggering callbacks
        self.knot_list.blockSignals(True)
        
        # Clear the list
        self.knot_list.clear()
        
        # Add knot items
        for i, knot in enumerate(self.curve.knots):
            self.knot_list.addItem(f"Knot {i+1} ({knot.x:.1f}, {knot.y:.1f})")
        
        # Restore selection
        if current_row >= 0 and current_row < self.knot_list.count():
            self.knot_list.setCurrentRow(current_row)
        elif self.knot_list.count() > 0:
            self.knot_list.setCurrentRow(0)
        
        # Unblock signals
        self.knot_list.blockSignals(False)
        
        # Update curve preview
        self.update_curve_preview()
    
    def update_properties_ui(self):
        """Update the properties UI with the selected knot's values"""
        if self.curve is None:
            return
        
        current_row = self.knot_list.currentRow()
        if current_row < 0 or current_row >= len(self.curve.knots):
            return
        
        knot = self.curve.knots[current_row]
        
        # Block signals to avoid triggering callbacks
        self.x_pos.blockSignals(True)
        self.y_pos.blockSignals(True)
        self.tension.blockSignals(True)
        self.manual_tangent.blockSignals(True)
        self.tangent_angle.blockSignals(True)
        self.tangent_magnitude.blockSignals(True)
        
        # Update UI values
        self.x_pos.setValue(knot.x)
        self.y_pos.setValue(knot.y)
        self.tension.setValue(int(knot.tension * 100))
        self.tension_value.setText(f"{knot.tension:.2f}")
        
        has_manual_tangent = knot.tangent_angle is not None
        self.manual_tangent.setChecked(has_manual_tangent)
        self.tangent_angle.setEnabled(has_manual_tangent)
        self.tangent_magnitude.setEnabled(has_manual_tangent)
        
        if has_manual_tangent:
            # Convert from radians to degrees
            angle_deg = np.degrees(knot.tangent_angle)
            self.tangent_angle.setValue(angle_deg)
            self.tangent_magnitude.setValue(knot.tangent_magnitude)
        
        # Unblock signals
        self.x_pos.blockSignals(False)
        self.y_pos.blockSignals(False)
        self.tension.blockSignals(False)
        self.manual_tangent.blockSignals(False)
        self.tangent_angle.blockSignals(False)
        self.tangent_magnitude.blockSignals(False)
        
        # Enable/disable remove button
        self.remove_knot_btn.setEnabled(self.knot_list.count() > 2)
    
    def update_curve_preview(self):
        """Update the curve preview in the image view"""
        if self.curve is None:
            return
        
        # Update the curve's B-spline representation
        self.curve.update_curve()
        
        # Update the curve display in the image view
        if hasattr(self.parent, 'image_view'):
            if self.parent.image_view.mode == "edit_curve":
                self.parent.image_view.update_curve_path(self.curve)
    
    def on_knot_selected(self, row):
        """
        Handle knot selection changed
        
        Args:
            row: Selected row index
        """
        if row < 0:
            return
        
        # Update properties UI
        self.update_properties_ui()
    
    def on_add_knot(self):
        """Handle add knot button"""
        if self.curve is None:
            return
        
        # Enable edit mode in the image view
        self.edit_knots_btn.setChecked(True)
        self.on_edit_knots(True)
        
        self.parent.statusBar().showMessage("Click on the image to add a knot point")
    
    def on_remove_knot(self):
        """Handle remove knot button"""
        if self.curve is None:
            return
        
        current_row = self.knot_list.currentRow()
        if current_row < 0 or current_row >= len(self.curve.knots):
            return
        
        # Check if we have enough knots
        if len(self.curve.knots) <= 2:
            QMessageBox.warning(self, "Warning", "A curve needs at least 2 knots")
            return
        
        # Remove the knot
        self.curve.remove_knot(current_row)
        
        # Update the knot list
        self.update_knot_list()
        
        # Select another knot
        if current_row >= self.knot_list.count():
            current_row = self.knot_list.count() - 1
        
        if current_row >= 0:
            self.knot_list.setCurrentRow(current_row)
    
    def on_edit_knots(self, checked):
        """
        Handle edit knots button toggled
        
        Args:
            checked: Boolean flag indicating if the button is checked
        """
        if self.curve is None:
            return
        
        if checked:
            # Enable edit mode in the image view
            self.parent.image_view.start_editing_curve(self.curve)
            self.parent.statusBar().showMessage("Edit mode: Click to add knots, drag to move")
        else:
            # Switch back to view mode
            self.parent.image_view.mode = "view"
            self.parent.image_view.setCursor(Qt.ArrowCursor)
            self.parent.image_view.setDragMode(self.parent.image_view.ScrollHandDrag)
            self.parent.statusBar().showMessage("View mode")
    
    def on_position_changed(self):
        """Handle position changed"""
        if self.curve is None:
            return
        
        current_row = self.knot_list.currentRow()
        if current_row < 0 or current_row >= len(self.curve.knots):
            return
        
        # Update knot position
        x = self.x_pos.value()
        y = self.y_pos.value()
        self.curve.knots[current_row].set_position(x, y)
        
        # Update the knot list
        self.update_knot_list()
        
        # Update curve preview
        self.update_curve_preview()
    
    def on_tension_changed(self, value):
        """
        Handle tension slider changed
        
        Args:
            value: New tension value (0-100)
        """
        if self.curve is None:
            return
        
        current_row = self.knot_list.currentRow()
        if current_row < 0 or current_row >= len(self.curve.knots):
            return
        
        # Update knot tension
        tension = value / 100.0
        self.curve.knots[current_row].set_tension(tension)
        self.tension_value.setText(f"{tension:.2f}")
        
        # Update curve preview
        self.update_curve_preview()
    
    def on_manual_tangent_changed(self, state):
        """
        Handle manual tangent checkbox changed
        
        Args:
            state: Checkbox state (Qt.Checked or Qt.Unchecked)
        """
        if self.curve is None:
            return
        
        current_row = self.knot_list.currentRow()
        if current_row < 0 or current_row >= len(self.curve.knots):
            return
        
        # Enable/disable tangent controls
        has_manual_tangent = state == Qt.Checked
        self.tangent_angle.setEnabled(has_manual_tangent)
        self.tangent_magnitude.setEnabled(has_manual_tangent)
        
        # Update knot tangent
        if has_manual_tangent:
            # Convert from degrees to radians
            angle_rad = np.radians(self.tangent_angle.value())
            magnitude = self.tangent_magnitude.value()
            self.curve.knots[current_row].set_tangent(angle_rad, magnitude)
        else:
            # Use auto tangent
            self.curve.knots[current_row].tangent_angle = None
        
        # Update curve preview
        self.update_curve_preview()
    
    def on_tangent_angle_changed(self, value):
        """
        Handle tangent angle changed
        
        Args:
            value: New angle value in degrees
        """
        if self.curve is None or not self.manual_tangent.isChecked():
            return
        
        current_row = self.knot_list.currentRow()
        if current_row < 0 or current_row >= len(self.curve.knots):
            return
        
        # Convert from degrees to radians
        angle_rad = np.radians(value)
        
        # Update knot tangent
        self.curve.knots[current_row].set_tangent(angle_rad)
        
        # Update curve preview
        self.update_curve_preview()
    
    def on_tangent_magnitude_changed(self, value):
        """
        Handle tangent magnitude changed
        
        Args:
            value: New magnitude value
        """
        if self.curve is None or not self.manual_tangent.isChecked():
            return
        
        current_row = self.knot_list.currentRow()
        if current_row < 0 or current_row >= len(self.curve.knots):
            return
        
        # Update knot tangent
        angle_rad = np.radians(self.tangent_angle.value())
        self.curve.knots[current_row].set_tangent(angle_rad, value)
        
        # Update curve preview
        self.update_curve_preview()
