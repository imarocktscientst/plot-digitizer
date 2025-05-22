#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Project data model for Plot Digitizer
"""

import os
import json
import numpy as np
import cv2
from utils.axis import Axis, AxisType
from utils.nurbs import NurbsCurve, NurbsKnot

class Project:
    """Class to represent a plot digitization project"""
    
    def __init__(self):
        """Initialize an empty project"""
        self.image_path = None
        self.image = None
        self.transformed_image = None
        self.perspective_matrix = None
        self.corner_points = None
        self.x_axis = Axis(AxisType.LINEAR)
        self.y_axis = Axis(AxisType.LINEAR)
        self.curves = []
        self.filename = None
        
    def load_image(self, image_path):
        """
        Load an image from file
        
        Args:
            image_path: Path to the image file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.image = cv2.imread(image_path)
            if self.image is None:
                return False
            
            self.image_path = image_path
            self.transformed_image = None
            self.perspective_matrix = None
            self.corner_points = None
            return True
        except Exception as e:
            print(f"Error loading image: {e}")
            return False
    
    def set_corner_points(self, points):
        """
        Set the corner points for perspective correction
        
        Args:
            points: Array of four (x, y) coordinates for the corners
        """
        self.corner_points = np.array(points)
        self.transformed_image = None
        self.perspective_matrix = None
    
    def apply_perspective_correction(self, width=800, height=600):
        """
        Apply perspective correction to the image
        
        Args:
            width: Width of the corrected image
            height: Height of the corrected image
            
        Returns:
            True if successful, False otherwise
        """
        from utils.perspective import apply_perspective_transform
        
        if self.image is None or self.corner_points is None:
            return False
        
        try:
            self.transformed_image, self.perspective_matrix = apply_perspective_transform(
                self.image, self.corner_points, width, height)
            return True
        except Exception as e:
            print(f"Error applying perspective correction: {e}")
            return False
    
    def add_curve(self):
        """
        Add a new curve to the project
        
        Returns:
            Index of the new curve
        """
        curve = NurbsCurve()
        self.curves.append(curve)
        return len(self.curves) - 1
    
    def remove_curve(self, index):
        """
        Remove a curve from the project
        
        Args:
            index: Index of the curve to remove
            
        Returns:
            True if successful, False otherwise
        """
        if 0 <= index < len(self.curves):
            del self.curves[index]
            return True
        return False
    
    def get_curve(self, index):
        """
        Get a curve by index
        
        Args:
            index: Index of the curve
            
        Returns:
            NurbsCurve object or None if index is invalid
        """
        if 0 <= index < len(self.curves):
            return self.curves[index]
        return None
    
    def save(self, filename):
        """
        Save the project to a file
        
        Args:
            filename: Output filename (should end with .pdp)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create the project directory
            base_path = os.path.splitext(filename)[0]
            os.makedirs(base_path, exist_ok=True)
            
            # Save the image
            image_path = os.path.join(base_path, "source_image.png")
            if self.image is not None:
                cv2.imwrite(image_path, self.image)
            
            # Save the transformed image if available
            if self.transformed_image is not None:
                transformed_path = os.path.join(base_path, "transformed_image.png")
                cv2.imwrite(transformed_path, self.transformed_image)
            
            # Prepare project data
            project_data = {
                'image_path': os.path.relpath(image_path, base_path),
                'corner_points': self.corner_points.tolist() if self.corner_points is not None else None,
                'x_axis': {
                    'type': 'LINEAR' if self.x_axis.axis_type == AxisType.LINEAR else 'LOGARITHMIC',
                    'min_pixel': self.x_axis.min_pixel,
                    'max_pixel': self.x_axis.max_pixel,
                    'min_value': self.x_axis.min_value,
                    'max_value': self.x_axis.max_value
                },
                'y_axis': {
                    'type': 'LINEAR' if self.y_axis.axis_type == AxisType.LINEAR else 'LOGARITHMIC',
                    'min_pixel': self.y_axis.min_pixel,
                    'max_pixel': self.y_axis.max_pixel,
                    'min_value': self.y_axis.min_value,
                    'max_value': self.y_axis.max_value
                },
                'curves': [curve.to_dict() for curve in self.curves]
            }
            
            # Save project data
            with open(filename, 'w') as f:
                json.dump(project_data, f, indent=2)
            
            self.filename = filename
            return True
        except Exception as e:
            print(f"Error saving project: {e}")
            return False
    
    @classmethod
    def load(cls, filename):
        """
        Load a project from a file
        
        Args:
            filename: Input filename (.pdp file)
            
        Returns:
            Project object or None if loading fails
        """
        try:
            project = cls()
            
            # Read project data
            with open(filename, 'r') as f:
                project_data = json.load(f)
            
            # Get base path
            base_path = os.path.splitext(filename)[0]
            
            # Load image
            image_path = os.path.join(base_path, project_data['image_path'])
            if not project.load_image(image_path):
                return None
            
            # Load corner points
            if project_data['corner_points'] is not None:
                project.corner_points = np.array(project_data['corner_points'])
                
                # Apply perspective correction if corner points are available
                project.apply_perspective_correction()
            
            # Load axis configuration
            x_axis_data = project_data['x_axis']
            project.x_axis = Axis(AxisType.LINEAR if x_axis_data['type'] == 'LINEAR' else AxisType.LOGARITHMIC)
            project.x_axis.set_calibration(
                x_axis_data['min_pixel'],
                x_axis_data['max_pixel'],
                x_axis_data['min_value'],
                x_axis_data['max_value']
            )
            
            y_axis_data = project_data['y_axis']
            project.y_axis = Axis(AxisType.LINEAR if y_axis_data['type'] == 'LINEAR' else AxisType.LOGARITHMIC)
            project.y_axis.set_calibration(
                y_axis_data['min_pixel'],
                y_axis_data['max_pixel'],
                y_axis_data['min_value'],
                y_axis_data['max_value']
            )
            
            # Load curves
            project.curves = [NurbsCurve.from_dict(curve_data) for curve_data in project_data['curves']]
            
            project.filename = filename
            return project
        except Exception as e:
            print(f"Error loading project: {e}")
            return None
