#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Axis calibration module for Plot Digitizer
"""

import numpy as np
from enum import Enum

class AxisType(Enum):
    """Enumeration for axis types"""
    LINEAR = 1
    LOGARITHMIC = 2

class Axis:
    """Class to represent an axis with calibration and scaling functions"""
    
    def __init__(self, axis_type=AxisType.LINEAR):
        """
        Initialize an axis
        
        Args:
            axis_type: Type of axis (linear or logarithmic)
        """
        self.axis_type = axis_type
        self.min_pixel = 0
        self.max_pixel = 1
        self.min_value = 0
        self.max_value = 1
        
    def set_calibration(self, min_pixel, max_pixel, min_value, max_value):
        """
        Set the calibration parameters for the axis
        
        Args:
            min_pixel: Minimum pixel coordinate
            max_pixel: Maximum pixel coordinate
            min_value: Minimum value at min_pixel
            max_value: Maximum value at max_pixel
        """
        self.min_pixel = min_pixel
        self.max_pixel = max_pixel
        self.min_value = min_value
        self.max_value = max_value
        
        # Validate parameters for logarithmic scale
        if self.axis_type == AxisType.LOGARITHMIC:
            if min_value <= 0 or max_value <= 0:
                raise ValueError("Logarithmic axis values must be positive")
    
    def pixel_to_value(self, pixel):
        """
        Convert a pixel coordinate to the corresponding value
        
        Args:
            pixel: Pixel coordinate
            
        Returns:
            The corresponding value on the axis
        """
        if self.axis_type == AxisType.LINEAR:
            # Linear interpolation
            pixel_range = self.max_pixel - self.min_pixel
            if pixel_range == 0:
                return self.min_value
            
            value_range = self.max_value - self.min_value
            normalized_position = (pixel - self.min_pixel) / pixel_range
            return self.min_value + normalized_position * value_range
        else:
            # Logarithmic interpolation
            pixel_range = self.max_pixel - self.min_pixel
            if pixel_range == 0:
                return self.min_value
            
            log_min = np.log10(self.min_value)
            log_max = np.log10(self.max_value)
            log_range = log_max - log_min
            
            normalized_position = (pixel - self.min_pixel) / pixel_range
            log_value = log_min + normalized_position * log_range
            
            return 10 ** log_value
    
    def value_to_pixel(self, value):
        """
        Convert a value to the corresponding pixel coordinate
        
        Args:
            value: Value on the axis
            
        Returns:
            The corresponding pixel coordinate
        """
        if self.axis_type == AxisType.LINEAR:
            # Linear interpolation
            value_range = self.max_value - self.min_value
            if value_range == 0:
                return self.min_pixel
            
            pixel_range = self.max_pixel - self.min_pixel
            normalized_position = (value - self.min_value) / value_range
            return self.min_pixel + normalized_position * pixel_range
        else:
            # Logarithmic interpolation
            if value <= 0:
                raise ValueError("Logarithmic axis values must be positive")
                
            log_min = np.log10(self.min_value)
            log_max = np.log10(self.max_value)
            log_range = log_max - log_min
            
            if log_range == 0:
                return self.min_pixel
            
            pixel_range = self.max_pixel - self.min_pixel
            log_value = np.log10(value)
            normalized_position = (log_value - log_min) / log_range
            
            return self.min_pixel + normalized_position * pixel_range
