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
    
    def update_curve(self, num_points=100):
            """
            Update the B-spline curve representation
            
            Args:
                num_points: Number of points to generate for the curve
            """
            if len(self.knots) < 2:
                self.curve_points = np.array([])
                return
            
            # Get control points
            control_points = np.array([[knot.x, knot.y] for knot in self.knots])
            
            if len(self.knots) == 2:
                # For 2 points, create a straight line
                t = np.linspace(0, 1, num_points)
                self.curve_points = np.array([
                    control_points[0] + t_val * (control_points[1] - control_points[0])
                    for t_val in t
                ])
                return
            
            # Handle manual tangents and tensions
            derivatives = []
            
            for i, knot in enumerate(self.knots):
                if knot.tangent_angle is not None:
                    # Manual tangent specified
                    dx = knot.tangent_magnitude * np.cos(knot.tangent_angle)
                    dy = knot.tangent_magnitude * np.sin(knot.tangent_angle)
                    derivatives.append([dx, dy])
                else:
                    # Auto tangent - calculate based on neighboring points and tension
                    if i == 0:
                        # First point - use direction to next point, modified by tension
                        direction = control_points[1] - control_points[0]
                        magnitude = np.linalg.norm(direction) * (1.0 - knot.tension)
                        if magnitude > 0:
                            direction = direction / np.linalg.norm(direction) * magnitude
                        derivatives.append(direction)
                    elif i == len(self.knots) - 1:
                        # Last point - use direction from previous point, modified by tension
                        direction = control_points[i] - control_points[i-1]
                        magnitude = np.linalg.norm(direction) * (1.0 - knot.tension)
                        if magnitude > 0:
                            direction = direction / np.linalg.norm(direction) * magnitude
                        derivatives.append(direction)
                    else:
                        # Middle point - use average direction, modified by tension
                        prev_dir = control_points[i] - control_points[i-1]
                        next_dir = control_points[i+1] - control_points[i]
                        
                        # Normalize directions
                        if np.linalg.norm(prev_dir) > 0:
                            prev_dir = prev_dir / np.linalg.norm(prev_dir)
                        if np.linalg.norm(next_dir) > 0:
                            next_dir = next_dir / np.linalg.norm(next_dir)
                        
                        # Average direction
                        avg_direction = (prev_dir + next_dir) / 2
                        
                        # Scale by distance and tension
                        scale = (np.linalg.norm(control_points[i+1] - control_points[i-1]) / 2) * (1.0 - knot.tension)
                        
                        if np.linalg.norm(avg_direction) > 0:
                            derivatives.append(avg_direction / np.linalg.norm(avg_direction) * scale)
                        else:
                            derivatives.append([0, 0])
            
            derivatives = np.array(derivatives)
            
            try:
                # Create parameter values
                t_knots = np.linspace(0, 1, len(control_points))
                
                # Use scipy's parametric spline with derivatives
                from scipy.interpolate import CubicHermiteSpline
                
                # Create cubic Hermite spline with position and derivative constraints
                cs_x = CubicHermiteSpline(t_knots, control_points[:, 0], derivatives[:, 0])
                cs_y = CubicHermiteSpline(t_knots, control_points[:, 1], derivatives[:, 1])
                
                # Generate curve points
                t = np.linspace(0, 1, num_points)
                x_curve = cs_x(t)
                y_curve = cs_y(t)
                
                self.curve_points = np.column_stack([x_curve, y_curve])
                
            except Exception as e:
                print(f"Error creating Hermite spline: {e}")
                # Fallback to simple interpolation
                try:
                    # Use scipy's splprep as fallback
                    tck, u = splprep([control_points[:, 0], control_points[:, 1]], s=0, k=min(3, len(control_points)-1))
                    
                    # Generate curve points
                    u_new = np.linspace(0, 1, num_points)
                    curve_points = splev(u_new, tck)
                    
                    self.curve_points = np.column_stack([curve_points[0], curve_points[1]])
                except Exception as e2:
                    print(f"Error creating fallback spline: {e2}")
                    # Final fallback - linear interpolation
                    t = np.linspace(0, 1, num_points)
                    self.curve_points = np.array([
                        np.interp(t, np.linspace(0, 1, len(control_points)), control_points[:, 0]),
                        np.interp(t, np.linspace(0, 1, len(control_points)), control_points[:, 1])
                    ]).T
    
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
