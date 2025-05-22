#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Image view widget for Plot Digitizer
"""

import numpy as np
from PyQt5.QtWidgets import (QGraphicsView, QGraphicsScene, QGraphicsPixmapItem,
                            QGraphicsEllipseItem, QGraphicsLineItem,
                            QGraphicsTextItem, QGraphicsPathItem)
from PyQt5.QtGui import (QPixmap, QImage, QPen, QColor, QBrush, QPainterPath,
                        QCursor, QPolygonF, QPainter)
from PyQt5.QtCore import Qt, QPointF, QRectF, pyqtSignal

class ImageView(QGraphicsView):
    """Widget for displaying and interacting with the plot image"""
    
    # Signals
    corner_points_changed = pyqtSignal(object)
    axis_points_changed = pyqtSignal(str, object)
    
    def __init__(self, parent=None):
        """Initialize the image view"""
        super().__init__(parent)
        
        # Create scene
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        
        # Image item
        self.image_item = None
        
        # Corner points for perspective correction
        self.corner_points = []
        self.corner_markers = []
        
        # Axis points
        self.x_axis_points = []
        self.y_axis_points = []
        self.x_axis_markers = []
        self.y_axis_markers = []
        
        # Curve points and markers
        self.curve_points = []
        self.curve_markers = []
        self.curve_path = None
        
        # Interaction state
        self.mode = "view"  # "view", "mark_corners", "mark_x_axis", "mark_y_axis", "edit_curve"
        self.current_point_index = -1
        
        # Setup view
        self.setRenderHint(QPainter.Antialiasing)
        self.setDragMode(self.ScrollHandDrag)
        self.setTransformationAnchor(self.AnchorUnderMouse)
        self.setResizeAnchor(self.AnchorUnderMouse)
        self.setMinimumSize(400, 300)
        
        # Connect signals
        self.setMouseTracking(True)
    
    def set_image(self, image):
        """
        Set the image to display
        
        Args:
            image: Numpy array or None
        """
        # Clear scene
        self.scene.clear()
        self.image_item = None
        self.corner_markers = []
        self.x_axis_markers = []
        self.y_axis_markers = []
        self.curve_markers = []
        self.curve_path = None
        
        if image is None:
            return
        
        # Convert numpy array to QImage
        if isinstance(image, np.ndarray):
            height, width = image.shape[:2]
            
            if len(image.shape) == 3 and image.shape[2] == 3:
                # RGB image
                qimage = QImage(image.data, width, height, width * 3, QImage.Format_RGB888)
            elif len(image.shape) == 3 and image.shape[2] == 4:
                # RGBA image
                qimage = QImage(image.data, width, height, width * 4, QImage.Format_RGBA8888)
            else:
                # Grayscale image
                qimage = QImage(image.data, width, height, width, QImage.Format_Grayscale8)
        else:
            qimage = QImage(image)
        
        # Create pixmap and add to scene
        pixmap = QPixmap.fromImage(qimage)
        self.image_item = QGraphicsPixmapItem(pixmap)
        self.scene.addItem(self.image_item)
        
        # Set scene rect to match the image
        self.scene.setSceneRect(self.image_item.boundingRect())
        
        # Reset view
        self.zoom_to_fit()
    
    def set_corner_points(self, points):
        """
        Set the corner points for perspective correction
        
        Args:
            points: Array of four (x, y) coordinates or None
        """
        # Clear existing markers
        for marker in self.corner_markers:
            self.scene.removeItem(marker)
        self.corner_markers = []
        
        # Reset corner points
        if points is None:
            self.corner_points = []
            return
        
        # Update corner points
        self.corner_points = points.tolist() if isinstance(points, np.ndarray) else points
        
        # Create markers
        for i, point in enumerate(self.corner_points):
            marker = self.create_point_marker(point[0], point[1], QColor(255, 0, 0))
            label = self.scene.addText(str(i+1))
            label.setPos(point[0], point[1])
            label.setDefaultTextColor(QColor(255, 0, 0))
            self.corner_markers.append(marker)
            self.corner_markers.append(label)
        
        # Emit signal
        self.corner_points_changed.emit(np.array(self.corner_points))
    
    def start_marking_corners(self):
        """Enter corner marking mode"""
        self.mode = "mark_corners"
        self.setCursor(Qt.CrossCursor)
        self.setDragMode(self.NoDrag)
        
        # Clear existing corner points
        self.set_corner_points(None)
    
    def start_marking_axis(self, axis_type):
        """
        Enter axis marking mode
        
        Args:
            axis_type: "x" or "y"
        """
        if axis_type == "x":
            self.mode = "mark_x_axis"
            
            # Clear existing x-axis points
            for marker in self.x_axis_markers:
                self.scene.removeItem(marker)
            self.x_axis_markers = []
            self.x_axis_points = []
        else:
            self.mode = "mark_y_axis"
            
            # Clear existing y-axis points
            for marker in self.y_axis_markers:
                self.scene.removeItem(marker)
            self.y_axis_markers = []
            self.y_axis_points = []
        
        self.setCursor(Qt.CrossCursor)
        self.setDragMode(self.NoDrag)
    
    def start_editing_curve(self, curve):
        """
        Enter curve editing mode
        
        Args:
            curve: NurbsCurve object
        """
        self.mode = "edit_curve"
        self.setCursor(Qt.CrossCursor)
        self.setDragMode(self.NoDrag)
        
        # Clear existing curve markers
        for marker in self.curve_markers:
            self.scene.removeItem(marker)
        self.curve_markers = []
        
        if self.curve_path is not None:
            self.scene.removeItem(self.curve_path)
            self.curve_path = None
        
        # Extract knot points from the curve
        self.curve_points = [(knot.x, knot.y) for knot in curve.knots]
        
        # Create markers for knot points
        for i, point in enumerate(self.curve_points):
            marker = self.create_point_marker(point[0], point[1], QColor(0, 0, 255))
            self.curve_markers.append(marker)
        
        # Draw the curve path
        self.update_curve_path(curve)
    
    def update_curve_path(self, curve):
        """
        Update the curve path display
        
        Args:
            curve: NurbsCurve object
        """
        if self.curve_path is not None:
            self.scene.removeItem(self.curve_path)
        
        # Sample the curve
        points = curve.sample(200)
        if points is None or len(points) < 2:
            self.curve_path = None
            return
        
        # Create a path
        path = QPainterPath()
        path.moveTo(points[0][0], points[0][1])
        
        for i in range(1, len(points)):
            path.lineTo(points[i][0], points[i][1])
        
        # Create path item
        self.curve_path = QGraphicsPathItem(path)
        self.curve_path.setPen(QPen(QColor(0, 128, 255), 2))
        self.scene.addItem(self.curve_path)
    
    def create_point_marker(self, x, y, color, size=8):
        """
        Create a marker for a point
        
        Args:
            x: X-coordinate
            y: Y-coordinate
            color: QColor for the marker
            size: Size of the marker
            
        Returns:
            QGraphicsEllipseItem for the marker
        """
        marker = QGraphicsEllipseItem(x - size/2, y - size/2, size, size)
        marker.setPen(QPen(color, 2))
        marker.setBrush(QBrush(color, Qt.SolidPattern))
        self.scene.addItem(marker)
        return marker
    
    def mousePressEvent(self, event):
        """Handle mouse press events"""
        if self.image_item is None:
            super().mousePressEvent(event)
            return
        
        # Get scene position
        pos = self.mapToScene(event.pos())
        x, y = pos.x(), pos.y()
        
        if self.mode == "mark_corners":
            # Add corner point
            if len(self.corner_points) < 4:
                self.corner_points.append([x, y])
                marker = self.create_point_marker(x, y, QColor(255, 0, 0))
                label = self.scene.addText(str(len(self.corner_points)))
                label.setPos(x, y)
                label.setDefaultTextColor(QColor(255, 0, 0))
                self.corner_markers.append(marker)
                self.corner_markers.append(label)
                
                # If we have 4 points, switch back to view mode and emit signal
                if len(self.corner_points) == 4:
                    self.mode = "view"
                    self.setCursor(Qt.ArrowCursor)
                    self.setDragMode(self.ScrollHandDrag)
                    self.corner_points_changed.emit(np.array(self.corner_points))
        
        elif self.mode == "mark_x_axis":
            # Add x-axis point
            if len(self.x_axis_points) < 2:
                self.x_axis_points.append([x, y])
                marker = self.create_point_marker(x, y, QColor(0, 255, 0))
                label = self.scene.addText("X" + str(len(self.x_axis_points)))
                label.setPos(x, y)
                label.setDefaultTextColor(QColor(0, 255, 0))
                self.x_axis_markers.append(marker)
                self.x_axis_markers.append(label)
                
                # If we have 2 points, switch back to view mode and emit signal
                if len(self.x_axis_points) == 2:
                    self.mode = "view"
                    self.setCursor(Qt.ArrowCursor)
                    self.setDragMode(self.ScrollHandDrag)
                    
                    # Update project's x-axis calibration
                    min_pixel = self.x_axis_points[0][0]
                    max_pixel = self.x_axis_points[1][0]
                    
                    # Update parent's project
                    self.parent().project.x_axis.min_pixel = min_pixel
                    self.parent().project.x_axis.max_pixel = max_pixel
                    
                    # Update axis calibration with current values from UI
                    self.parent().on_x_axis_changed()
                    
                    # Emit signal
                    self.axis_points_changed.emit("x", np.array(self.x_axis_points))
        
        elif self.mode == "mark_y_axis":
            # Add y-axis point
            if len(self.y_axis_points) < 2:
                self.y_axis_points.append([x, y])
                marker = self.create_point_marker(x, y, QColor(0, 255, 0))
                label = self.scene.addText("Y" + str(len(self.y_axis_points)))
                label.setPos(x, y)
                label.setDefaultTextColor(QColor(0, 255, 0))
                self.y_axis_markers.append(marker)
                self.y_axis_markers.append(label)
                
                # If we have 2 points, switch back to view mode and emit signal
                if len(self.y_axis_points) == 2:
                    self.mode = "view"
                    self.setCursor(Qt.ArrowCursor)
                    self.setDragMode(self.ScrollHandDrag)
                    
                    # Determine which point has the smaller Y pixel coordinate (higher on screen)
                    # and which has the larger Y pixel coordinate (lower on screen)
                    point1_y = self.y_axis_points[0][1]
                    point2_y = self.y_axis_points[1][1]
                    
                    if point1_y < point2_y:
                        # First point is higher on screen (smaller Y pixel = max value)
                        max_pixel = point1_y
                        min_pixel = point2_y
                    else:
                        # Second point is higher on screen
                        max_pixel = point2_y
                        min_pixel = point1_y
                    
                    # Update parent's project
                    self.parent().project.y_axis.min_pixel = min_pixel
                    self.parent().project.y_axis.max_pixel = max_pixel
                    
                    # Update axis calibration with current values from UI
                    self.parent().on_y_axis_changed()
                    
                    # Emit signal
                    self.axis_points_changed.emit("y", np.array(self.y_axis_points))
        
        elif self.mode == "edit_curve":
            # Check if clicking on an existing point
            for i, point in enumerate(self.curve_points):
                if abs(x - point[0]) < 10 and abs(y - point[1]) < 10:
                    self.current_point_index = i
                    break
            else:
                # Not clicking on an existing point, add a new one
                curve = self.parent().project.get_curve(self.parent().current_curve_index)
                if curve is None:
                    return
                
                # Add knot to the curve
                from utils.nurbs import NurbsKnot
                knot = NurbsKnot(x, y)
                curve.add_knot(knot)
                
                # Update curve display
                self.start_editing_curve(curve)
                
                # Update curve editor UI
                self.parent().curve_editor.update_knot_list()
        
        else:
            # View mode, use default behavior
            super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """Handle mouse move events"""
        if self.image_item is None:
            super().mouseMoveEvent(event)
            return
        
        # Get scene position
        pos = self.mapToScene(event.pos())
        x, y = pos.x(), pos.y()
        
        if self.mode == "edit_curve" and self.current_point_index >= 0 and event.buttons() & Qt.LeftButton:
            # Moving a curve point
            curve = self.parent().project.get_curve(self.parent().current_curve_index)
            if curve is None:
                return
            
            # Update knot position
            curve.knots[self.current_point_index].set_position(x, y)
            
            # Update curve display
            self.start_editing_curve(curve)
            
            # Update curve editor UI
            self.parent().curve_editor.update_knot_list()
        else:
            # Default behavior
            super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release events"""
        self.current_point_index = -1
        super().mouseReleaseEvent(event)
    
    def wheelEvent(self, event):
        """Handle mouse wheel events for zooming"""
        if event.angleDelta().y() > 0:
            self.zoom_in()
        else:
            self.zoom_out()
    
    def zoom_in(self):
        """Zoom in"""
        self.scale(1.2, 1.2)
    
    def zoom_out(self):
        """Zoom out"""
        self.scale(1/1.2, 1/1.2)
    
    def zoom_to_fit(self):
        """Zoom to fit the image in the view"""
        if self.image_item is None:
            return
        
        # Reset transformation
        self.resetTransform()
        
        # Get the image and view rects
        image_rect = self.image_item.boundingRect()
        view_rect = self.viewport().rect()
        
        # Calculate the scaling factors
        scale_x = view_rect.width() / image_rect.width()
        scale_y = view_rect.height() / image_rect.height()
        
        # Use the smaller scaling factor to ensure the entire image is visible
        scale = min(scale_x, scale_y) * 0.95
        
        # Apply the scaling
        self.scale(scale, scale)
        
        # Center the image
        self.centerOn(image_rect.center())
