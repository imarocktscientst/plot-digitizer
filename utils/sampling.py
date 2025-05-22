#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Data sampling module for Plot Digitizer
"""

import numpy as np
from utils.axis import Axis, AxisType

def uniform_sampling(curve, x_axis, y_axis, num_points=100):
    """
    Sample a curve with uniform spacing in the independent variable
    
    Args:
        curve: NurbsCurve object to sample
        x_axis: X-axis object for conversion from pixels to values
        y_axis: Y-axis object for conversion from pixels to values
        num_points: Number of sample points
        
    Returns:
        Pandas DataFrame with x and y columns containing the sampled data
    """
    import pandas as pd
    
    if curve.bspline is None or len(curve.knots) < 2:
        return pd.DataFrame(columns=['x', 'y'])
    
    # Get the pixel coordinates of all knots
    knot_pixels = np.array([(knot.x, knot.y) for knot in curve.knots])
    
    # Convert to axis values
    knot_x_values = np.array([x_axis.pixel_to_value(px) for px in knot_pixels[:, 0]])
    
    # Determine range of the independent variable
    x_min = np.min(knot_x_values)
    x_max = np.max(knot_x_values)
    
    # Generate uniform x values
    if x_axis.axis_type == AxisType.LINEAR:
        x_values = np.linspace(x_min, x_max, num_points)
    else:  # Logarithmic
        x_values = np.logspace(np.log10(x_min), np.log10(x_max), num_points)
    
    # Convert x values to pixel coordinates
    x_pixels = np.array([x_axis.value_to_pixel(x) for x in x_values])
    
    # For each x pixel, find the corresponding y pixel on the curve
    result_data = []
    
    for x_px in x_pixels:
        # Find the t parameter where the curve has this x coordinate
        # This is a simple approach: sample the curve densely and find closest point
        t_values = np.linspace(0, 1, 1000)
        curve_points = curve.evaluate(t_values)
        
        if curve_points is None or len(curve_points) == 0:
            continue
        
        # Find the point with the closest x coordinate
        distances = np.abs(curve_points[:, 0] - x_px)
        closest_idx = np.argmin(distances)
        closest_point = curve_points[closest_idx]
        
        # Convert pixel coordinates to axis values
        x_val = x_axis.pixel_to_value(closest_point[0])
        y_val = y_axis.pixel_to_value(closest_point[1])
        
        result_data.append({'x': x_val, 'y': y_val})
    
    return pd.DataFrame(result_data)

def adaptive_sampling(curve, x_axis, y_axis, max_error=0.5, min_points=10, max_points=1000):
    """
    Sample a curve adaptively based on local curvature
    
    Args:
        curve: NurbsCurve object to sample
        x_axis: X-axis object for conversion from pixels to values
        y_axis: Y-axis object for conversion from pixels to values
        max_error: Maximum allowed error between linear segments and curve
        min_points: Minimum number of points to sample
        max_points: Maximum number of points to sample
        
    Returns:
        Pandas DataFrame with x and y columns containing the sampled data
    """
    import pandas as pd
    
    if curve.bspline is None or len(curve.knots) < 2:
        return pd.DataFrame(columns=['x', 'y'])
    
    # Get adaptively sampled points in pixel coordinates
    pixel_points = curve.adaptive_sample(max_error, min_points, max_points)
    
    if pixel_points is None or len(pixel_points) == 0:
        return pd.DataFrame(columns=['x', 'y'])
    
    # Convert pixel coordinates to axis values
    result_data = []
    
    for point in pixel_points:
        x_val = x_axis.pixel_to_value(point[0])
        y_val = y_axis.pixel_to_value(point[1])
        result_data.append({'x': x_val, 'y': y_val})
    
    return pd.DataFrame(result_data)

def export_to_csv(df, filename, by_column=True):
    """
    Export data to CSV file
    
    Args:
        df: Pandas DataFrame containing the data
        filename: Output filename
        by_column: If True, export data by columns (x in first column, y in second)
                  If False, export data by rows (x in first row, y in second)
    """
    if by_column:
        # Default pandas to_csv exports by columns
        df.to_csv(filename, index=False)
    else:
        # Transpose data to export by rows
        df_t = df.T
        df_t.to_csv(filename, header=False)
