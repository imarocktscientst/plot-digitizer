#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Perspective correction module for Plot Digitizer
"""

import numpy as np
import cv2

def find_quad_corners(image):
    """
    Helper function to find quadrilateral corners in the image.
    For automated corner detection (optional feature).
    
    Args:
        image: Input image (numpy array)
        
    Returns:
        numpy array of corner points (4x2)
    """
    # Convert to grayscale if needed
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()
        
    # Apply threshold to get binary image
    _, thresh = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
    
    # Find contours
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Find the largest contour (assuming it's the plot area)
    largest_contour = max(contours, key=cv2.contourArea)
    
    # Approximate the contour to get a polygon
    epsilon = 0.02 * cv2.arcLength(largest_contour, True)
    approx = cv2.approxPolyDP(largest_contour, epsilon, True)
    
    # If we have 4 points, great! Otherwise, find the convex hull
    if len(approx) != 4:
        hull = cv2.convexHull(largest_contour)
        epsilon = 0.02 * cv2.arcLength(hull, True)
        approx = cv2.approxPolyDP(hull, epsilon, True)
    
    # If we still don't have 4 points, return the 4 corners of the bounding box
    if len(approx) != 4:
        x, y, w, h = cv2.boundingRect(largest_contour)
        approx = np.array([
            [[x, y]],
            [[x+w, y]],
            [[x+w, y+h]],
            [[x, y+h]]
        ])
    
    # Reshape to make it easier to work with
    corners = approx.reshape(4, 2)
    
    # Reorder points to [top-left, top-right, bottom-right, bottom-left]
    ordered_corners = reorder_corners(corners)
    
    return ordered_corners

def reorder_corners(pts):
    """
    Reorders quadrilateral corners to [top-left, top-right, bottom-right, bottom-left]
    
    Args:
        pts: Input points (4x2 numpy array)
        
    Returns:
        Reordered points (4x2 numpy array)
    """
    # Calculate the center
    center = np.mean(pts, axis=0)
    
    # Get vectors from center to points
    vectors = pts - center
    
    # Calculate angles
    angles = np.arctan2(vectors[:, 1], vectors[:, 0])
    
    # Sort by angle
    sorted_indices = np.argsort(angles)
    
    # Rotate so that the first point is the top-left
    if sorted_indices[0] != 0:
        rotation = 4 - sorted_indices[0]
        sorted_indices = np.roll(sorted_indices, rotation)
    
    return pts[sorted_indices]

def apply_perspective_transform(image, source_points, target_width, target_height):
    """
    Apply perspective transformation to correct for camera angle
    
    Args:
        image: Input image (numpy array)
        source_points: Four corner points of the plot area in the input image (4x2 numpy array)
        target_width: Width of the output image
        target_height: Height of the output image
        
    Returns:
        Perspective-corrected image
    """
    # Define the target points (rectangle)
    target_points = np.array([
        [0, 0],  # top-left
        [target_width, 0],  # top-right
        [target_width, target_height],  # bottom-right
        [0, target_height]  # bottom-left
    ], dtype=np.float32)
    
    # Convert source_points to float32
    source_points = source_points.astype(np.float32)
    
    # Calculate the perspective transformation matrix
    matrix = cv2.getPerspectiveTransform(source_points, target_points)
    
    # Apply the transformation
    result = cv2.warpPerspective(image, matrix, (target_width, target_height))
    
    return result, matrix

def inverse_perspective_transform(point, matrix):
    """
    Transform a point from the corrected image back to the original image
    
    Args:
        point: Point in the corrected image (x, y)
        matrix: Perspective transformation matrix
        
    Returns:
        Corresponding point in the original image
    """
    # Add homogeneous coordinate
    homogeneous_point = np.array([point[0], point[1], 1], dtype=np.float32)
    
    # Apply inverse transformation
    inverse_matrix = np.linalg.inv(matrix)
    original_homogeneous = np.dot(inverse_matrix, homogeneous_point)
    
    # Convert back from homogeneous coordinates
    original_point = (original_homogeneous[0] / original_homogeneous[2],
                     original_homogeneous[1] / original_homogeneous[2])
    
    return original_point
