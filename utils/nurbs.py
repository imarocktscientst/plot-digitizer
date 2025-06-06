#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enhanced NURBS curves implementation with proper tangent support
"""

import numpy as np
from scipy import interpolate

class NurbsKnot:
    """Class to represent a knot in a NURBS curve"""
    
    def __init__(self, x, y, tension=0.5, tangent_angle=None):
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
        self.tangent_magnitude_in = 50.0  # In handle magnitude
        self.tangent_magnitude_out = 50.0  # Out handle magnitude
        self.independent_handles = False  # If True, handles can have different angles
        
        # For independent handles mode
        self.tangent_angle_in = None  # Separate angle for in handle
        
        # Tangent handle positions (for graphical editing)
        self.in_handle_x = None
        self.in_handle_y = None
        self.out_handle_x = None
        self.out_handle_y = None
        
        # Update handle positions
        self._update_handles()
    
    def set_position(self, x, y):
        """Update the position of the knot"""
        dx = x - self.x
        dy = y - self.y
        self.x = x
        self.y = y
        
        # Move handles with the knot
        if self.in_handle_x is not None:
            self.in_handle_x += dx
            self.in_handle_y += dy
        if self.out_handle_x is not None:
            self.out_handle_x += dx
            self.out_handle_y += dy
    
    def set_tension(self, tension):
        """Update the tension of the knot"""
        self.tension = max(0.0, min(1.0, tension))
        self._update_handles()
    
    def set_tangent(self, angle, magnitude_out=None, magnitude_in=None):
        """
        Update the tangent angle and optionally the magnitudes
        
        Args:
            angle: Tangent angle in radians (for out handle)
            magnitude_out: Out handle magnitude (if None, keep current value)
            magnitude_in: In handle magnitude (if None, keep current value)
        """
        self.tangent_angle = angle
        if magnitude_out is not None:
            self.tangent_magnitude_out = max(1.0, magnitude_out)
        if magnitude_in is not None:
            self.tangent_magnitude_in = max(1.0, magnitude_in)
        
        # If not in independent mode, clear the separate in angle
        if not self.independent_handles:
            self.tangent_angle_in = None
        
        self._update_handles()
    
    def set_handle_position(self, handle_type, x, y):
        """
        Set handle position directly (for graphical editing)
        
        Args:
            handle_type: 'in' or 'out'
            x, y: Handle position
        """
        if handle_type == 'in':
            self.in_handle_x = x
            self.in_handle_y = y
            # Calculate angle and magnitude from handle position
            dx = x - self.x
            dy = y - self.y
            self.tangent_magnitude_in = np.sqrt(dx**2 + dy**2)
            
            if self.tangent_magnitude_in > 0:
                if self.independent_handles:
                    # Store angle from knot to in handle
                    self.tangent_angle_in = np.arctan2(dy, dx)
                else:
                    # In colinear mode, adjusting in handle updates the main angle
                    # The out handle should point opposite to the in handle
                    self.tangent_angle = np.arctan2(-dy, -dx)
                    # Update out handle position to maintain colinearity
                    self._update_out_handle()
                    
        elif handle_type == 'out':
            self.out_handle_x = x
            self.out_handle_y = y
            # Calculate angle and magnitude from handle position
            dx = x - self.x
            dy = y - self.y
            self.tangent_magnitude_out = np.sqrt(dx**2 + dy**2)
            
            if self.tangent_magnitude_out > 0:
                # Out handle angle (from knot to handle)
                self.tangent_angle = np.arctan2(dy, dx)
                
                if not self.independent_handles:
                    # Update in handle position to maintain colinearity
                    self._update_in_handle()
    
    def _update_handles(self):
        """Update handle positions based on tangent angles and magnitudes"""
        if self.tangent_angle is not None:
            # Apply tension to magnitudes
            effective_mag_out = self.tangent_magnitude_out * (1.0 - self.tension * 0.8)
            effective_mag_in = self.tangent_magnitude_in * (1.0 - self.tension * 0.8)
            
            # Out handle uses the main tangent angle
            dx_out = effective_mag_out * np.cos(self.tangent_angle)
            dy_out = effective_mag_out * np.sin(self.tangent_angle)
            self.out_handle_x = self.x + dx_out
            self.out_handle_y = self.y + dy_out
            
            # In handle calculation
            if self.independent_handles and self.tangent_angle_in is not None:
                # Use independent angle for in handle (angle from knot to handle)
                dx_in = effective_mag_in * np.cos(self.tangent_angle_in)
                dy_in = effective_mag_in * np.sin(self.tangent_angle_in)
                self.in_handle_x = self.x + dx_in
                self.in_handle_y = self.y + dy_in
            else:
                # In handle points in opposite direction (colinear)
                self.in_handle_x = self.x - dx_out * (effective_mag_in / effective_mag_out)
                self.in_handle_y = self.y - dy_out * (effective_mag_in / effective_mag_out)
    
    def _update_in_handle(self):
        """Update only the in handle position (maintaining colinearity)"""
        if self.tangent_angle is not None:
            effective_mag_in = self.tangent_magnitude_in * (1.0 - self.tension * 0.8)
            # In handle points in opposite direction
            dx = effective_mag_in * np.cos(self.tangent_angle + np.pi)
            dy = effective_mag_in * np.sin(self.tangent_angle + np.pi)
            self.in_handle_x = self.x + dx
            self.in_handle_y = self.y + dy
    
    def _update_out_handle(self):
        """Update only the out handle position (maintaining colinearity)"""
        if self.tangent_angle is not None:
            effective_mag_out = self.tangent_magnitude_out * (1.0 - self.tension * 0.8)
            # Out handle uses the main tangent angle
            dx = effective_mag_out * np.cos(self.tangent_angle)
            dy = effective_mag_out * np.sin(self.tangent_angle)
            self.out_handle_x = self.x + dx
            self.out_handle_y = self.y + dy
    
    def get_tangent_vector(self, direction='out'):
        """
        Get the tangent vector
        
        Args:
            direction: 'in' or 'out' for incoming or outgoing tangent
            
        Returns:
            (dx, dy) tangent vector for the curve at this knot
        """
        if self.tangent_angle is None:
            return (0, 0)  # Auto-calculate later
        
        if direction == 'in':
            # Apply tension to magnitude
            effective_magnitude = self.tangent_magnitude_in * (1.0 - self.tension * 0.8)
            
            if self.independent_handles and self.tangent_angle_in is not None:
                # Use independent in angle
                # The in handle points at angle tangent_angle_in from the knot
                # The tangent vector should point from the in handle towards the knot
                dx = effective_magnitude * np.cos(self.tangent_angle_in + np.pi)
                dy = effective_magnitude * np.sin(self.tangent_angle_in + np.pi)
                return (dx, dy)
            else:
                # Colinear mode: in tangent should have same direction as out tangent
                # This ensures smooth continuity through the knot
                dx = effective_magnitude * np.cos(self.tangent_angle)
                dy = effective_magnitude * np.sin(self.tangent_angle)
                return (dx, dy)
        else:
            # Out tangent
            effective_magnitude = self.tangent_magnitude_out * (1.0 - self.tension * 0.8)
            dx = effective_magnitude * np.cos(self.tangent_angle)
            dy = effective_magnitude * np.sin(self.tangent_angle)
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
        knot = cls(data['x'], data['y'], data['tension'], data.get('tangent_angle'))
        knot.tangent_magnitude = data.get('tangent_magnitude', 50.0)
        return knot


class NurbsCurve:
    """Class to represent a NURBS curve using Hermite interpolation"""
    
    def __init__(self):
        """Initialize an empty NURBS curve"""
        self.knots = []
        self._hermite_segments = []
        self._update_needed = True
    
    def add_knot(self, knot):
        """Add a knot to the curve"""
        # Insert knot at appropriate position to maintain x-order
        if not self.knots or knot.x >= self.knots[-1].x:
            self.knots.append(knot)
        else:
            # Find insertion point
            for i, k in enumerate(self.knots):
                if knot.x < k.x:
                    self.knots.insert(i, knot)
                    break
        self._update_needed = True
    
    def remove_knot(self, index):
        """Remove a knot from the curve"""
        if 0 <= index < len(self.knots):
            del self.knots[index]
            self._update_needed = True
    
    def _calculate_auto_tangents(self):
        """Calculate automatic tangents for knots that don't have manual ones"""
        n = len(self.knots)
        if n <= 1:
            return
        
        for i in range(n):
            knot = self.knots[i]
            if knot.tangent_angle is not None:
                continue  # Skip knots with manual tangents
            
            # Get neighboring knots
            prev_knot = self.knots[i-1] if i > 0 else None
            next_knot = self.knots[i+1] if i < n-1 else None
            
            if prev_knot is None and next_knot is None:
                # Single knot
                knot.tangent_angle = 0.0
                knot.tangent_magnitude_in = 50.0
                knot.tangent_magnitude_out = 50.0
            elif prev_knot is None:
                # First knot
                dx = next_knot.x - knot.x
                dy = next_knot.y - knot.y
                knot.tangent_angle = np.arctan2(dy, dx)
                mag = np.sqrt(dx**2 + dy**2) * 0.3
                knot.tangent_magnitude_in = mag
                knot.tangent_magnitude_out = mag
            elif next_knot is None:
                # Last knot
                dx = knot.x - prev_knot.x
                dy = knot.y - prev_knot.y
                knot.tangent_angle = np.arctan2(dy, dx)
                mag = np.sqrt(dx**2 + dy**2) * 0.3
                knot.tangent_magnitude_in = mag
                knot.tangent_magnitude_out = mag
            else:
                # Middle knot - use Catmull-Rom tangent
                dx = next_knot.x - prev_knot.x
                dy = next_knot.y - prev_knot.y
                
                if abs(dx) > 0.001:
                    knot.tangent_angle = np.arctan2(dy, dx)
                    # Magnitude based on distances to neighbors
                    d1 = np.sqrt((knot.x - prev_knot.x)**2 + (knot.y - prev_knot.y)**2)
                    d2 = np.sqrt((next_knot.x - knot.x)**2 + (next_knot.y - knot.y)**2)
                    knot.tangent_magnitude_in = d1 * 0.3
                    knot.tangent_magnitude_out = d2 * 0.3
                else:
                    knot.tangent_angle = np.pi/2 if dy > 0 else -np.pi/2
                    knot.tangent_magnitude_in = 50.0
                    knot.tangent_magnitude_out = 50.0
            
            knot._update_handles()
    
    def _hermite_interpolate(self, p0, p1, t0, t1, t):
        """
        Hermite interpolation between two points
        
        Args:
            p0, p1: Start and end points (x, y)
            t0, t1: Start and end tangent vectors (dx, dy)
            t: Parameter in [0, 1]
            
        Returns:
            Interpolated point (x, y)
        """
        # Hermite basis functions
        h00 = 2*t**3 - 3*t**2 + 1
        h10 = t**3 - 2*t**2 + t
        h01 = -2*t**3 + 3*t**2
        h11 = t**3 - t**2
        
        # Interpolate
        x = h00 * p0[0] + h10 * t0[0] + h01 * p1[0] + h11 * t1[0]
        y = h00 * p0[1] + h10 * t0[1] + h01 * p1[1] + h11 * t1[1]
        
        return (x, y)
    
    def update_curve(self):
        """Update the curve segments based on current knots"""
        n = len(self.knots)
        if n < 2:
            self._hermite_segments = []
            self._update_needed = False
            return
        
        # Calculate auto tangents where needed
        self._calculate_auto_tangents()
        
        # Create Hermite segments between consecutive knots
        self._hermite_segments = []
        
        for i in range(n - 1):
            k0 = self.knots[i]
            k1 = self.knots[i + 1]
            
            # Get tangent vectors
            t0 = k0.get_tangent_vector('out')
            t1 = k1.get_tangent_vector('in')
            
            self._hermite_segments.append({
                'p0': (k0.x, k0.y),
                'p1': (k1.x, k1.y),
                't0': t0,
                't1': t1
            })
        
        self._update_needed = False
    
    def evaluate(self, t):
        """
        Evaluate the curve at parameter t
        
        Args:
            t: Parameter value(s) in [0, 1] or array of values
            
        Returns:
            (x, y) coordinates on the curve or array of coordinates
        """
        if self._update_needed:
            self.update_curve()
        
        if not self._hermite_segments:
            return None
        
        # Handle both single value and array input
        t_array = np.atleast_1d(t)
        results = []
        
        n_segments = len(self._hermite_segments)
        
        for t_val in t_array:
            # Map t to segment
            if t_val <= 0:
                seg = self._hermite_segments[0]
                results.append(seg['p0'])
            elif t_val >= 1:
                seg = self._hermite_segments[-1]
                results.append(seg['p1'])
            else:
                # Find which segment t falls into
                segment_idx = int(t_val * n_segments)
                if segment_idx >= n_segments:
                    segment_idx = n_segments - 1
                
                # Local t within the segment
                local_t = (t_val * n_segments) - segment_idx
                
                seg = self._hermite_segments[segment_idx]
                point = self._hermite_interpolate(
                    seg['p0'], seg['p1'], seg['t0'], seg['t1'], local_t)
                results.append(point)
        
        # Return single value or array based on input
        if len(results) == 1 and np.isscalar(t):
            return results[0]
        else:
            return np.array(results)
    
    def sample(self, num_points=100):
        """Sample the curve at uniform parameter values"""
        if len(self.knots) < 2:
            return np.array([])
        
        t = np.linspace(0, 1, num_points)
        points = self.evaluate(t)
        return points if points is not None else np.array([])
    
    def adaptive_sample(self, max_error=0.5, min_points=10, max_points=1000):
        """Sample the curve adaptively based on curvature"""
        if len(self.knots) < 2:
            return np.array([])
        
        if self._update_needed:
            self.update_curve()
        
        if not self._hermite_segments:
            return np.array([])
        
        # Start with endpoints of each segment
        sample_points = []
        sample_params = []
        
        n_segments = len(self._hermite_segments)
        
        # Add initial points at segment boundaries
        for i in range(n_segments + 1):
            t = i / n_segments
            sample_params.append(t)
            if i < n_segments:
                sample_points.append(self._hermite_segments[i]['p0'])
            else:
                sample_points.append(self._hermite_segments[-1]['p1'])
        
        # Adaptive refinement
        i = 0
        while i < len(sample_params) - 1 and len(sample_params) < max_points:
            t1 = sample_params[i]
            t2 = sample_params[i + 1]
            p1 = sample_points[i]
            p2 = sample_points[i + 1]
            
            # Check midpoint
            t_mid = (t1 + t2) / 2
            p_mid = self.evaluate(t_mid)
            
            # Linear interpolation at midpoint
            p_linear = ((np.array(p1) + np.array(p2)) / 2).tolist()
            
            # Calculate error
            error = np.sqrt((p_mid[0] - p_linear[0])**2 + (p_mid[1] - p_linear[1])**2)
            
            if error > max_error:
                # Insert midpoint
                sample_params.insert(i + 1, t_mid)
                sample_points.insert(i + 1, p_mid)
            else:
                i += 1
        
        # Ensure minimum points
        while len(sample_points) < min_points:
            # Find largest gap
            max_gap = 0
            max_gap_idx = 0
            for i in range(len(sample_params) - 1):
                gap = sample_params[i + 1] - sample_params[i]
                if gap > max_gap:
                    max_gap = gap
                    max_gap_idx = i
            
            # Insert point in largest gap
            t_new = (sample_params[max_gap_idx] + sample_params[max_gap_idx + 1]) / 2
            p_new = self.evaluate(t_new)
            sample_params.insert(max_gap_idx + 1, t_new)
            sample_points.insert(max_gap_idx + 1, p_new)
        
        return np.array(sample_points)
    
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