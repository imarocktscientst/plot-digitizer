#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enhanced image view widget with graphical tangent handles
"""

import numpy as np
from PyQt5.QtWidgets import (QGraphicsView, QGraphicsScene, QGraphicsPixmapItem,
                            QGraphicsEllipseItem, QGraphicsLineItem,
                            QGraphicsTextItem, QGraphicsPathItem)
from PyQt5.QtGui import (QPixmap, QImage, QPen, QColor, QBrush, QPainterPath,
                        QCursor, QPolygonF, QPainter)
from PyQt5.QtCore import Qt, QPointF, QRectF, pyqtSignal

class TangentHandle(QGraphicsEllipseItem):
    """A draggable tangent handle"""
    
    def __init__(self, handle_type='out', size=8):
        # Store the size for later use
        self.handle_size = size
        self.handle_type = handle_type  # 'in' or 'out'
        
        # Set color based on handle type
        if handle_type == 'in':
            color = QColor(255, 100, 100)  # Red for in handles
        else:
            color = QColor(100, 200, 255)  # Blue for out handles
        
        # Create ellipse with size
        super().__init__(0, 0, size, size)
        self.setPen(QPen(color, 2))
        self.setBrush(QBrush(color, Qt.SolidPattern))
        self.setFlag(self.ItemIsMovable, True)
        self.setFlag(self.ItemSendsGeometryChanges, True)
        self.setCursor(Qt.SizeAllCursor)
        self.setZValue(10)  # Above curve and knot points
        
        self.knot = None
        self.tangent_line = None
        self.parent_view = None
    
    def get_center(self):
        """Get the center position of the handle in scene coordinates"""
        pos = self.scenePos()
        return (pos.x() + self.handle_size/2, pos.y() + self.handle_size/2)
    
    def set_center(self, x, y):
        """Set the position so the center is at (x, y)"""
        self.setPos(x - self.handle_size/2, y - self.handle_size/2)
    
    def itemChange(self, change, value):
        """Handle item changes"""
        if change == self.ItemPositionChange and self.knot:
            # Calculate the new center position
            new_pos = value
            center_x = new_pos.x() + self.handle_size / 2
            center_y = new_pos.y() + self.handle_size / 2
            
            # Update knot handle position
            self.knot.set_handle_position(self.handle_type, center_x, center_y)
            
            # Update tangent line
            if self.tangent_line:
                if self.handle_type == 'in':
                    self.tangent_line.setLine(center_x, center_y, self.knot.x, self.knot.y)
                else:
                    self.tangent_line.setLine(self.knot.x, self.knot.y, center_x, center_y)
            
            # Update curve
            if self.parent_view:
                self.parent_view.update_curve_from_handles()
        
        return super().itemChange(change, value)


class ImageView(QGraphicsView):
    """Enhanced widget for displaying and interacting with the plot image"""
    
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
        
        # Curve points, markers, and tangent handles
        self.curve_points = []
        self.curve_markers = []
        self.curve_path = None
        self.tangent_handles = []  # List of TangentHandle objects
        self.tangent_lines = []    # Lines connecting handles to knots
        self.current_curve = None  # Reference to current NurbsCurve
        
        # Interaction state
        self.mode = "view"  # "view", "mark_corners", "mark_x_axis", "mark_y_axis", "edit_curve"
        self.current_point_index = -1
        self.dragging_knot = False
        
        # Setup view
        self.setRenderHint(QPainter.Antialiasing)
        self.setDragMode(self.ScrollHandDrag)
        self.setTransformationAnchor(self.AnchorUnderMouse)
        self.setResizeAnchor(self.AnchorUnderMouse)
        self.setMinimumSize(400, 300)
        
        # Connect signals
        self.setMouseTracking(True)
    
    def set_image(self, image):
        """Set the image to display"""
        # Clear scene
        self.scene.clear()
        self.image_item = None
        self.corner_markers = []
        self.x_axis_markers = []
        self.y_axis_markers = []
        self.curve_markers = []
        self.curve_path = None
        self.tangent_handles = []
        self.tangent_lines = []
        
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
        """Set the corner points for perspective correction"""
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
        """Enter axis marking mode"""
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
        """Enter curve editing mode with tangent handles"""
        self.mode = "edit_curve"
        self.setCursor(Qt.CrossCursor)
        self.setDragMode(self.NoDrag)
        self.current_curve = curve
        
        # Clear existing curve graphics
        self._clear_curve_graphics()
        
        # Extract knot points from the curve
        self.curve_points = [(knot.x, knot.y) for knot in curve.knots]
        
        # Create markers for knot points and tangent handles
        for i, knot in enumerate(curve.knots):
            # Create knot marker
            marker = self.create_point_marker(knot.x, knot.y, QColor(0, 0, 255))
            marker.setZValue(5)  # Above curve but below handles
            self.curve_markers.append(marker)
            
            # Create tangent handles if knot has manual tangent
            if knot.tangent_angle is not None:
                # Always create out handle
                out_handle = TangentHandle('out')
                out_handle.knot = knot
                out_handle.parent_view = self
                out_handle.set_center(knot.out_handle_x, knot.out_handle_y)
                
                # Out tangent line
                out_line = QGraphicsLineItem(knot.x, knot.y, knot.out_handle_x, knot.out_handle_y)
                out_line.setPen(QPen(QColor(100, 200, 255), 1, Qt.DashLine))
                out_line.setZValue(1)
                
                # Store reference
                out_handle.tangent_line = out_line
                
                # Add to scene
                self.scene.addItem(out_line)
                self.scene.addItem(out_handle)
                
                self.tangent_handles.append(out_handle)
                self.tangent_lines.append(out_line)
                
                # Only create in handle if independent handles mode is enabled
                if knot.independent_handles:
                    in_handle = TangentHandle('in')
                    in_handle.knot = knot
                    in_handle.parent_view = self
                    in_handle.set_center(knot.in_handle_x, knot.in_handle_y)
                    
                    # In tangent line
                    in_line = QGraphicsLineItem(knot.in_handle_x, knot.in_handle_y, knot.x, knot.y)
                    in_line.setPen(QPen(QColor(255, 100, 100), 1, Qt.DashLine))
                    in_line.setZValue(1)
                    
                    # Store reference
                    in_handle.tangent_line = in_line
                    
                    # Add to scene
                    self.scene.addItem(in_line)
                    self.scene.addItem(in_handle)
                    
                    self.tangent_handles.append(in_handle)
                    self.tangent_lines.append(in_line)
        
        # Draw the curve path
        self.update_curve_path(curve)
    
    def _clear_curve_graphics(self):
        """Clear all curve-related graphics"""
        for marker in self.curve_markers:
            self.scene.removeItem(marker)
        self.curve_markers = []
        
        for handle in self.tangent_handles:
            self.scene.removeItem(handle)
        self.tangent_handles = []
        
        for line in self.tangent_lines:
            self.scene.removeItem(line)
        self.tangent_lines = []
        
        if self.curve_path is not None:
            self.scene.removeItem(self.curve_path)
            self.curve_path = None
    
    def update_curve_from_handles(self):
        """Update curve when tangent handles are moved"""
        if self.current_curve and not self.dragging_knot:
            self.current_curve.update_curve()
            self.update_curve_path(self.current_curve)
            
            # Notify curve editor to update UI
            if hasattr(self.parent(), 'curve_editor'):
                self.parent().curve_editor.update_properties_ui()
    
    def update_curve_path(self, curve):
        """Update the curve path display"""
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
        self.curve_path.setZValue(2)  # Above image but below knots
        self.scene.addItem(self.curve_path)
    
    def create_point_marker(self, x, y, color, size=8):
        """Create a marker for a point"""
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
            self._handle_corner_marking(x, y)
        
        elif self.mode == "mark_x_axis":
            self._handle_x_axis_marking(x, y)
        
        elif self.mode == "mark_y_axis":
            self._handle_y_axis_marking(x, y)
        
        elif self.mode == "edit_curve":
            # Check if clicking on an existing knot point
            for i, point in enumerate(self.curve_points):
                if abs(x - point[0]) < 10 and abs(y - point[1]) < 10:
                    self.current_point_index = i
                    self.dragging_knot = True
                    return
            
            # Not clicking on an existing point, add a new one
            if self.current_curve:
                from utils.nurbs import NurbsKnot
                knot = NurbsKnot(x, y)
                self.current_curve.add_knot(knot)
                
                # Update display
                self.start_editing_curve(self.current_curve)
                
                # Update curve editor UI
                self.parent().curve_editor.update_knot_list()
        
        else:
            # View mode
            super().mousePressEvent(event)
    
    def _handle_corner_marking(self, x, y):
        """Handle corner point marking"""
        if len(self.corner_points) < 4:
            self.corner_points.append([x, y])
            marker = self.create_point_marker(x, y, QColor(255, 0, 0))
            label = self.scene.addText(str(len(self.corner_points)))
            label.setPos(x, y)
            label.setDefaultTextColor(QColor(255, 0, 0))
            self.corner_markers.append(marker)
            self.corner_markers.append(label)
            
            if len(self.corner_points) == 4:
                self.mode = "view"
                self.setCursor(Qt.ArrowCursor)
                self.setDragMode(self.ScrollHandDrag)
                self.corner_points_changed.emit(np.array(self.corner_points))
    
    def _handle_x_axis_marking(self, x, y):
        """Handle X-axis point marking"""
        if len(self.x_axis_points) < 2:
            self.x_axis_points.append([x, y])
            marker = self.create_point_marker(x, y, QColor(0, 255, 0))
            label = self.scene.addText("X" + str(len(self.x_axis_points)))
            label.setPos(x, y)
            label.setDefaultTextColor(QColor(0, 255, 0))
            self.x_axis_markers.append(marker)
            self.x_axis_markers.append(label)
            
            if len(self.x_axis_points) == 2:
                self.mode = "view"
                self.setCursor(Qt.ArrowCursor)
                self.setDragMode(self.ScrollHandDrag)
                
                # Update project's x-axis calibration
                min_pixel = self.x_axis_points[0][0]
                max_pixel = self.x_axis_points[1][0]
                
                self.parent().project.x_axis.min_pixel = min_pixel
                self.parent().project.x_axis.max_pixel = max_pixel
                self.parent().on_x_axis_changed()
                
                self.axis_points_changed.emit("x", np.array(self.x_axis_points))
    
    def _handle_y_axis_marking(self, x, y):
        """Handle Y-axis point marking"""
        if len(self.y_axis_points) < 2:
            self.y_axis_points.append([x, y])
            marker = self.create_point_marker(x, y, QColor(0, 255, 0))
            label = self.scene.addText("Y" + str(len(self.y_axis_points)))
            label.setPos(x, y)
            label.setDefaultTextColor(QColor(0, 255, 0))
            self.y_axis_markers.append(marker)
            self.y_axis_markers.append(label)
            
            if len(self.y_axis_points) == 2:
                self.mode = "view"
                self.setCursor(Qt.ArrowCursor)
                self.setDragMode(self.ScrollHandDrag)
                
                # Determine which point is min/max
                point1_y = self.y_axis_points[0][1]
                point2_y = self.y_axis_points[1][1]
                
                if point1_y < point2_y:
                    max_pixel = point1_y
                    min_pixel = point2_y
                else:
                    max_pixel = point2_y
                    min_pixel = point1_y
                
                self.parent().project.y_axis.min_pixel = min_pixel
                self.parent().project.y_axis.max_pixel = max_pixel
                self.parent().on_y_axis_changed()
                
                self.axis_points_changed.emit("y", np.array(self.y_axis_points))
    
    def mouseMoveEvent(self, event):
        """Handle mouse move events"""
        if self.image_item is None:
            super().mouseMoveEvent(event)
            return
        
        # Get scene position
        pos = self.mapToScene(event.pos())
        x, y = pos.x(), pos.y()
        
        if self.mode == "edit_curve" and self.dragging_knot and self.current_point_index >= 0:
            # Moving a curve knot point
            if self.current_curve and self.current_point_index < len(self.current_curve.knots):
                knot = self.current_curve.knots[self.current_point_index]
                
                # Calculate movement delta
                old_x, old_y = knot.x, knot.y
                dx = x - old_x
                dy = y - old_y
                
                # Update knot position
                knot.set_position(x, y)
                
                # Update the visual position of the knot marker
                if self.current_point_index < len(self.curve_markers):
                    marker = self.curve_markers[self.current_point_index]
                    marker_size = marker.rect().width()
                    marker.setPos(x - marker_size/2, y - marker_size/2)
                
                # Update tangent handles if they exist for this knot
                if knot.tangent_angle is not None:
                    # Find the handles for this knot
                    for handle in self.tangent_handles:
                        if handle.knot == knot:
                            if handle.handle_type == 'in':
                                handle.set_center(knot.in_handle_x, knot.in_handle_y)
                            else:
                                handle.set_center(knot.out_handle_x, knot.out_handle_y)
                    
                    # Update tangent lines
                    for i, line in enumerate(self.tangent_lines):
                        line_data = line.line()
                        # Check if this line is connected to the moved knot
                        if (abs(line_data.x1() - old_x) < 1 and abs(line_data.y1() - old_y) < 1):
                            # This is an outgoing line
                            line.setLine(x, y, line_data.x2() + dx, line_data.y2() + dy)
                        elif (abs(line_data.x2() - old_x) < 1 and abs(line_data.y2() - old_y) < 1):
                            # This is an incoming line
                            line.setLine(line_data.x1() + dx, line_data.y1() + dy, x, y)
                
                # Update curve path
                self.current_curve.update_curve()
                self.update_curve_path(self.current_curve)
                
                # Update curve editor UI
                self.parent().curve_editor.update_knot_list()
        else:
            super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release events"""
        self.current_point_index = -1
        self.dragging_knot = False
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
        
        # Use the smaller scaling factor
        scale = min(scale_x, scale_y) * 0.95
        
        # Apply the scaling
        self.scale(scale, scale)
        
        # Center the image
        self.centerOn(image_rect.center())