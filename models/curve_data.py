#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Curve data model for Plot Digitizer
"""

import pandas as pd
from utils.sampling import uniform_sampling, adaptive_sampling, export_to_csv

class CurveData:
    """Class to represent extracted data from a curve"""
    
    def __init__(self, curve, x_axis, y_axis):
        """
        Initialize with a curve and axes
        
        Args:
            curve: NurbsCurve object
            x_axis: X-axis object
            y_axis: Y-axis object
        """
        self.curve = curve
        self.x_axis = x_axis
        self.y_axis = y_axis
        self.data = None
    
    def sample_uniform(self, num_points=100):
        """
        Sample the curve with uniform spacing in the independent variable
        
        Args:
            num_points: Number of sample points
            
        Returns:
            Pandas DataFrame with the sampled data
        """
        self.data = uniform_sampling(self.curve, self.x_axis, self.y_axis, num_points)
        return self.data
    
    def sample_adaptive(self, max_error=0.5, min_points=10, max_points=1000):
        """
        Sample the curve adaptively based on local curvature
        
        Args:
            max_error: Maximum allowed error between linear segments and curve
            min_points: Minimum number of points to sample
            max_points: Maximum number of points to sample
            
        Returns:
            Pandas DataFrame with the sampled data
        """
        self.data = adaptive_sampling(
            self.curve, self.x_axis, self.y_axis, max_error, min_points, max_points)
        return self.data
    
    def export_csv(self, filename, by_column=True):
        """
        Export data to a CSV file
        
        Args:
            filename: Output filename
            by_column: If True, export data by columns (x in first column, y in second)
                       If False, export data by rows (x in first row, y in second)
                       
        Returns:
            True if successful, False otherwise
        """
        if self.data is None or self.data.empty:
            return False
        
        try:
            export_to_csv(self.data, filename, by_column)
            return True
        except Exception as e:
            print(f"Error exporting to CSV: {e}")
            return False
    
    def get_statistics(self):
        """
        Calculate basic statistics for the sampled data
        
        Returns:
            Dictionary with statistics
        """
        if self.data is None or self.data.empty:
            return None
        
        stats = {
            'count': len(self.data),
            'x_min': self.data['x'].min(),
            'x_max': self.data['x'].max(),
            'y_min': self.data['y'].min(),
            'y_max': self.data['y'].max(),
            'x_mean': self.data['x'].mean(),
            'y_mean': self.data['y'].mean()
        }
        
        return stats
