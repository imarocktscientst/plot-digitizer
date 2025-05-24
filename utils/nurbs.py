#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NURBS curves implementation for Plot Digitizer
"""

import numpy as np
from scipy import interpolate

class NurbsKnot:
    """Class to represent a knot in a NURBS curve"""
    
    def __init__(self, x, y, tension=0.0, tangent_angle=None):
        """
        Initialize a NURBS knot
        
        Args:
            x: X-coordinate
            y: Y-coordinate
            tension: Tension parameter (0.0 - 1.0)
            tangent_angle: Angle of the tangent (in radians, None for auto)
        """
        self.x = x
        self.y = y
        self.tension = max(0.0, min(1.0, tension))  # Clamp to [0, 1]
        self.tangent_angle = tangent_angle  # None means auto-calculated
        self.tangent_magnitude = 1.0  # Default tangent magnitude
    
    def set_position(self, x, y):
        """Update the position of the knot"""
        self.x = x
        self.y = y
    
    def set_tension(self, tension):
        """Update the tension of the knot"""
        self.tension = max(0.0, min(1.0, tension))
    
    def set_tangent(self, angle, magnitude=None):
        """
        Update the tangent angle and optionally the magnitude
        
        Args:
            angle: Tangent angle in radians
            magnitude: Tangent magnitude (if None, keep current value)
        """
        self.tangent_angle = angle
        if magnitude is not None:
            self.tangent_magnitude = max(0.1, magnitude)  # Ensure positive magnitude
    
    def get_tangent_vector(self):
        """
        Get the tangent vector based on angle and magnitude
        
        Returns:
            (dx, dy) tangent vector
        """
        if self.tangent_angle is None:
            return (0, 0)  # Auto-calculate later
        
        dx = self.tangent_magnitude * np.cos(self.tangent_angle)
        dy = self.tangent_magnitude * np.sin(self.tangent_angle)
        return (dx, dy)
    
    def to_dict(self):
        """Convert to dictionary for serialization"""
        return {
            'x': self.x,
            'y': self.y,
            'tension': self.tension,
            'tangent_angle': self.tangent_angle,
            'tangent_magnitude': self.tangent_magnitude
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create from dictionary (deserialization)"""
        knot = cls(data['x'], data['y'], data['tension'], data['tangent_angle'])
        knot.tangent_magnitude = data['tangent_magnitude']
        return knot

class NurbsCurve:
    """Class to represent a NURBS curve"""
    
    def __init__(self):
        """Initialize an empty NURBS curve"""
        self.knots = []
        self.bspline = None
        self._update_needed = True
    
    def add_knot(self, knot):
        """
        Add a knot to the curve
        
        Args:
            knot: NurbsKnot object
        """
        self.knots.append(knot)
        self._update_needed = True
    
    def remove_knot(self, index):
        """
        Remove a knot from the curve
        
        Args:
            index: Index of the knot to remove
        """
        if 0 <= index < len(self.knots):
            del self.knots[index]
            self._update_needed = True
    
    def update_knot(self, index, knot):
        """
        Update a knot in the curve
        
        Args:
            index: Index of the knot to update
            knot: New NurbsKnot object
        """
        if 0 <= index < len(self.knots):
            self.knots[index] = knot
            self._update_needed = True
    
    def _calculate_auto_tangents(self):
        """Calculate automatic tangents for knots that don't have manual ones"""
        n = len(self.knots)
        if n <= 1:
            return
        
        # For each knot
        for i in range(n):
            knot = self.knots[i]
            if knot.tangent_angle is not None:
                continue  # Skip knots with manual tangents
            
            # Get neighboring knots
            prev_knot = self.knots[i-1] if i > 0 else None
            next_knot = self.knots[i+1] if i < n-1 else None
            
            if prev_knot is None and next_knot is None:
                # Isolated knot, use horizontal tangent
                knot.tangent_angle = 0.0
            elif prev_knot is None:
                # First knot, use direction to next knot
                dx = next_knot.x - knot.x
                dy = next_knot.y - knot.y
                knot.tangent_angle = np.arctan2(dy, dx)
            elif next_knot is None:
                # Last knot, use direction from previous knot
                dx = knot.x - prev_knot.x
                dy = knot.y - prev_knot.y
                knot.tangent_angle = np.arctan2(dy, dx)
            else:
                # Middle knot, use average direction
                dx1 = knot.x - prev_knot.x
                dy1 = knot.y - prev_knot.y
                dx2 = next_knot.x - knot.x
                dy2 = next_knot.y - knot.y
                
                # Normalize vectors
                len1 = np.sqrt(dx1**2 + dy1**2)
                len2 = np.sqrt(dx2**2 + dy2**2)
                
                if len1 > 0 and len2 > 0:
                    dx1 /= len1
                    dy1 /= len1
                    dx2 /= len2
                    dy2 /= len2
                    
                    # Average direction
                    dx = (dx1 + dx2) / 2
                    dy = (dy1 + dy2) / 2
                    
                    # Apply tension to control curve smoothness
                    mag = np.sqrt(dx**2 + dy**2) * (1.0 - knot.tension)
                    
                    knot.tangent_angle = np.arctan2(dy, dx)
                    knot.tangent_magnitude = mag
    
    def update_curve(self):
        """Update the B-spline representation based on the current knots"""
        n = len(self.knots)
        if n < 2:
            self.bspline = None
            self._update_needed = False
            return
        
        # Calculate auto tangents where needed
        self._calculate_auto_tangents()
        
        # Extract points, tangents, and weights for interpolation
        points = np.array([(knot.x, knot.y) for knot in self.knots])
        
        # Create parameter values (cumulative chord length)
        t = np.zeros(n)
        for i in range(1, n):
            dx = points[i, 0] - points[i-1, 0]
            dy = points[i, 1] - points[i-1, 1]
            t[i] = t[i-1] + np.sqrt(dx**2 + dy**2)
        
        if t[-1] > 0:
            t /= t[-1]  # Normalize to [0, 1]
        
        # Use scipy's splprep for fitting a B-spline
        self.bspline, _ = interpolate.splprep([points[:, 0], points[:, 1]], 
                                             u=t, s=0, k=min(3, n-1))
        
        self._update_needed = False
    
    def evaluate(self, t):
        """
        Evaluate the curve at parameter t
        
        Args:
            t: Parameter value(s) in [0, 1]
            
        Returns:
            (x, y) coordinates on the curve
        """
        if self._update_needed or self.bspline is None:
            self.update_curve()
        
        if self.bspline is None:
            return None
        
        try:
            points = interpolate.splev(t, self.bspline)
            return np.column_stack(points)
        except:
            return None
    
    def sample(self, num_points=100):
        """
        Sample the curve at uniform parameter values
        
        Args:
            num_points: Number of sample points
            
        Returns:
            Array of (x, y) coordinates on the curve
        """
        if len(self.knots) < 2:
            return np.array([])
        
        t = np.linspace(0, 1, num_points)
        return self.evaluate(t)
    
    def adaptive_sample(self, max_error=0.5, min_points=10, max_points=1000):
        """
        Sample the curve adaptively based on curvature
        
        Args:
            max_error: Maximum allowed error between linear segments and curve
            min_points: Minimum number of points to sample
            max_points: Maximum number of points to sample
            
        Returns:
            Array of (x, y) coordinates on the curve
        """
        if len(self.knots) < 2:
            return np.array([])
        
        if self._update_needed or self.bspline is None:
            self.update_curve()
        
        if self.bspline is None:
            return np.array([])
        
        # Start with uniform sampling
        t_values = [0.0]
        points = [self.evaluate(0.0)[0]]
        
        # Adaptive refinement
        queue = [(0.0, 1.0)]  # (start_t, end_t) segments to check
        
        while queue and len(points) < max_points:
            t_start, t_end = queue.pop(0)
            
            # Evaluate at midpoint
            t_mid = (t_start + t_end) / 2
            p_start = self.evaluate(t_start)[0]
            p_end = self.evaluate(t_end)[0]
            p_mid_actual = self.evaluate(t_mid)[0]
            
            # Calculate linear interpolation at midpoint
            p_mid_linear = (p_start + p_end) / 2
            
            # Calculate error
            error = np.linalg.norm(p_mid_actual - p_mid_linear)
            
            if error > max_error:
                # Split segment and add to queue
                queue.append((t_start, t_mid))
                queue.append((t_mid, t_end))
                
                # Insert midpoint in the result
                idx = t_values.index(t_start) + 1
                t_values.insert(idx, t_mid)
                points.insert(idx, p_mid_actual)
        
        # Ensure we have at least min_points
        if len(points) < min_points:
            t_values = np.linspace(0, 1, min_points)
            points = self.evaluate(t_values)
        
        return np.array(points)
    
    def to_dict(self):
        """Convert to dictionary for serialization"""
        return {
            'knots': [knot.to_dict() for knot in self.knots]
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create from dictionary (deserialization)"""
        curve = cls()
        curve.knots = [NurbsKnot.from_dict(knot_data) for knot_data in data['knots']]
        curve._update_needed = True
        return curve
