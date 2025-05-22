#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Export dialog for Plot Digitizer
"""

import os
import pandas as pd
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
                           QLabel, QLineEdit, QPushButton, QFileDialog,
                           QGroupBox, QRadioButton, QButtonGroup, QSpinBox,
                           QDoubleSpinBox, QTableWidget, QTableWidgetItem,
                           QHeaderView, QCheckBox, QMessageBox, QTabWidget,
                           QTextEdit, QWidget)
from PyQt5.QtCore import Qt

class ExportDialog(QDialog):
    """Dialog for exporting curve data"""
    
    def __init__(self, parent, curve_data):
        """
        Initialize the export dialog
        
        Args:
            parent: Parent widget
            curve_data: CurveData object
        """
        super().__init__(parent)
        
        self.curve_data = curve_data
        
        self.init_ui()
        self.setWindowTitle("Export Data")
        self.resize(800, 600)
    
    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout(self)
        
        # Create tabs
        tabs = QTabWidget()
        
        # Data tab
        data_tab = QWidget()
        data_layout = QVBoxLayout(data_tab)
        
        # Display the sampled data table
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["X", "Y"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        data_layout.addWidget(self.table)
        
        # Export options tab
        options_tab = QWidget()
        options_layout = QVBoxLayout(options_tab)
        
        # Sampling group
        sampling_group = QGroupBox("Sampling Method")
        sampling_layout = QVBoxLayout(sampling_group)
        
        # Uniform sampling
        uniform_layout = QHBoxLayout()
        self.uniform_sampling = QRadioButton("Uniform sampling")
        self.uniform_sampling.setChecked(True)
        self.uniform_sampling.toggled.connect(self.on_sampling_changed)
        
        self.num_points = QSpinBox()
        self.num_points.setRange(10, 10000)
        self.num_points.setValue(100)
        self.num_points.valueChanged.connect(self.on_sampling_params_changed)
        
        uniform_layout.addWidget(self.uniform_sampling)
        uniform_layout.addWidget(QLabel("Number of points:"))
        uniform_layout.addWidget(self.num_points)
        uniform_layout.addStretch()
        
        # Adaptive sampling
        adaptive_layout = QHBoxLayout()
        self.adaptive_sampling = QRadioButton("Adaptive sampling")
        self.adaptive_sampling.toggled.connect(self.on_sampling_changed)
        
        self.max_error = QDoubleSpinBox()
        self.max_error.setRange(0.001, 10.0)
        self.max_error.setValue(0.5)
        self.max_error.setDecimals(3)
        self.max_error.setSingleStep(0.1)
        self.max_error.valueChanged.connect(self.on_sampling_params_changed)
        
        self.min_points = QSpinBox()
        self.min_points.setRange(5, 1000)
        self.min_points.setValue(10)
        self.min_points.valueChanged.connect(self.on_sampling_params_changed)
        
        self.max_points = QSpinBox()
        self.max_points.setRange(10, 10000)
        self.max_points.setValue(1000)
        self.max_points.valueChanged.connect(self.on_sampling_params_changed)
        
        adaptive_layout.addWidget(self.adaptive_sampling)
        adaptive_layout.addWidget(QLabel("Max error:"))
        adaptive_layout.addWidget(self.max_error)
        adaptive_layout.addWidget(QLabel("Min points:"))
        adaptive_layout.addWidget(self.min_points)
        adaptive_layout.addWidget(QLabel("Max points:"))
        adaptive_layout.addWidget(self.max_points)
        adaptive_layout.addStretch()
        
        # Add to sampling group
        sampling_layout.addLayout(uniform_layout)
        sampling_layout.addLayout(adaptive_layout)
        
        # CSV format group
        format_group = QGroupBox("CSV Format")
        format_layout = QVBoxLayout(format_group)
        
        # Column/row orientation
        orientation_layout = QHBoxLayout()
        self.by_column = QRadioButton("By columns (X, Y)")
        self.by_column.setChecked(True)
        
        self.by_row = QRadioButton("By rows (X; Y)")
        
        orientation_layout.addWidget(self.by_column)
        orientation_layout.addWidget(self.by_row)
        orientation_layout.addStretch()
        
        # Include header
        header_layout = QHBoxLayout()
        self.include_header = QCheckBox("Include header")
        self.include_header.setChecked(True)
        
        header_layout.addWidget(self.include_header)
        header_layout.addStretch()
        
        # Add to format group
        format_layout.addLayout(orientation_layout)
        format_layout.addLayout(header_layout)
        
        # Add to options layout
        options_layout.addWidget(sampling_group)
        options_layout.addWidget(format_group)
        options_layout.addStretch()
        
        # Statistics tab
        stats_tab = QWidget()
        stats_layout = QVBoxLayout(stats_tab)
        
        # Statistics text
        self.stats_text = QTextEdit()
        self.stats_text.setReadOnly(True)
        
        stats_layout.addWidget(self.stats_text)
        
        # Add tabs to tab widget
        tabs.addTab(data_tab, "Data")
        tabs.addTab(options_tab, "Options")
        tabs.addTab(stats_tab, "Statistics")
        
        # Add tab widget to main layout
        layout.addWidget(tabs)
        
        # Now that all UI components are created, update the table and statistics
        self.update_table()
        self.update_statistics()
        
        # Export button
        export_layout = QHBoxLayout()
        
        export_btn = QPushButton("Export to CSV...")
        export_btn.clicked.connect(self.on_export)
        
        copy_btn = QPushButton("Copy to Clipboard")
        copy_btn.clicked.connect(self.on_copy)
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        
        export_layout.addWidget(export_btn)
        export_layout.addWidget(copy_btn)
        export_layout.addStretch()
        export_layout.addWidget(close_btn)
        
        layout.addLayout(export_layout)
    
    def update_table(self):
        """Update the table with the current data"""
        # Sample the curve
        if self.uniform_sampling.isChecked():
            data = self.curve_data.sample_uniform(self.num_points.value())
        else:
            data = self.curve_data.sample_adaptive(
                self.max_error.value(),
                self.min_points.value(),
                self.max_points.value()
            )
        
        # Update table
        self.table.setRowCount(len(data))
        
        for i, (_, row) in enumerate(data.iterrows()):
            x_item = QTableWidgetItem(f"{row['x']:.6g}")
            y_item = QTableWidgetItem(f"{row['y']:.6g}")
            
            self.table.setItem(i, 0, x_item)
            self.table.setItem(i, 1, y_item)
    
    def update_statistics(self):
        """Update the statistics text with data stats"""
        # Sample the curve
        if self.uniform_sampling.isChecked():
            data = self.curve_data.sample_uniform(self.num_points.value())
        else:
            data = self.curve_data.sample_adaptive(
                self.max_error.value(),
                self.min_points.value(),
                self.max_points.value()
            )
        
        # Calculate statistics
        stats = {
            'Number of points': len(data),
            'X range': (data['x'].min(), data['x'].max()),
            'Y range': (data['y'].min(), data['y'].max()),
            'X mean': data['x'].mean(),
            'Y mean': data['y'].mean(),
            'X median': data['x'].median(),
            'Y median': data['y'].median(),
            'X std dev': data['x'].std(),
            'Y std dev': data['y'].std()
        }
        
        # Format statistics text
        stats_text = "Data Statistics:\n\n"
        
        stats_text += f"Number of points: {stats['Number of points']}\n\n"
        
        stats_text += f"X range: {stats['X range'][0]:.6g} to {stats['X range'][1]:.6g}\n"
        stats_text += f"Y range: {stats['Y range'][0]:.6g} to {stats['Y range'][1]:.6g}\n\n"
        
        stats_text += f"X mean: {stats['X mean']:.6g}\n"
        stats_text += f"Y mean: {stats['Y mean']:.6g}\n\n"
        
        stats_text += f"X median: {stats['X median']:.6g}\n"
        stats_text += f"Y median: {stats['Y median']:.6g}\n\n"
        
        stats_text += f"X standard deviation: {stats['X std dev']:.6g}\n"
        stats_text += f"Y standard deviation: {stats['Y std dev']:.6g}\n"
        
        # Set the statistics text
        self.stats_text.setText(stats_text)
    
    def on_sampling_changed(self):
        """Handle sampling method changed"""
        # Enable/disable options based on selected method
        self.num_points.setEnabled(self.uniform_sampling.isChecked())
        
        self.max_error.setEnabled(self.adaptive_sampling.isChecked())
        self.min_points.setEnabled(self.adaptive_sampling.isChecked())
        self.max_points.setEnabled(self.adaptive_sampling.isChecked())
        
        # Update the table and statistics
        self.update_table()
        self.update_statistics()
    
    def on_sampling_params_changed(self):
        """Handle sampling parameters changed"""
        # Update the table and statistics
        self.update_table()
        self.update_statistics()
    
    def on_export(self):
        """Handle export button"""
        # Get filename from dialog
        filename, _ = QFileDialog.getSaveFileName(
            self, "Export CSV", "", "CSV Files (*.csv)")
        
        if not filename:
            return
        
        # Add extension if not present
        if not filename.endswith(".csv"):
            filename += ".csv"
        
        # Sample the curve
        if self.uniform_sampling.isChecked():
            data = self.curve_data.sample_uniform(self.num_points.value())
        else:
            data = self.curve_data.sample_adaptive(
                self.max_error.value(),
                self.min_points.value(),
                self.max_points.value()
            )
        
        try:
            # Export based on orientation
            if self.by_column.isChecked():
                if not self.include_header.isChecked():
                    data.to_csv(filename, index=False, header=False)
                else:
                    data.to_csv(filename, index=False)
            else:
                data_t = data.T
                if not self.include_header.isChecked():
                    data_t.to_csv(filename, index=False, header=False)
                else:
                    data_t.to_csv(filename, index=False)
            
            QMessageBox.information(self, "Success", f"Data exported to {filename}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to export data: {e}")
    
    def on_copy(self):
        """Handle copy to clipboard button"""
        # Sample the curve
        if self.uniform_sampling.isChecked():
            data = self.curve_data.sample_uniform(self.num_points.value())
        else:
            data = self.curve_data.sample_adaptive(
                self.max_error.value(),
                self.min_points.value(),
                self.max_points.value()
            )
        
        try:
            # Export to clipboard based on orientation
            if self.by_column.isChecked():
                text = data.to_csv(index=False, header=self.include_header.isChecked())
            else:
                data_t = data.T
                text = data_t.to_csv(index=False, header=self.include_header.isChecked())
            
            # Copy to clipboard
            clipboard = self.parent().parent().clipboard()
            clipboard.setText(text)
            
            QMessageBox.information(self, "Success", "Data copied to clipboard")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to copy data: {e}")
