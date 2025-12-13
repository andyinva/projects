#!/usr/bin/env python3
"""
Trailer Backup Guide - PyQt6 Application
Helps practice and visualize backing up a trailer with real-time guidance
"""

import sys
import json
import math
from pathlib import Path
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QPushButton, QLabel, QLineEdit,
                             QComboBox, QGroupBox, QGridLayout, QMessageBox,
                             QDialog, QDialogButtonBox, QSpinBox, QDoubleSpinBox,
                             QTextEdit, QScrollArea)
from PyQt6.QtCore import Qt, QTimer, QPointF, QRectF, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QPolygonF, QPainterPath


class VehicleConfig:
    """Store configuration for truck and trailer"""
    def __init__(self, name="Default"):
        self.name = name
        # Truck dimensions (in inches) - User's specific truck
        self.truck_length = 229.0  # Total truck length
        self.truck_width = 79.0  # Outside tire to outside tire
        self.truck_wheelbase = 154.0 - 9.0  # Distance from front axle (A) to rear axle (B)
        self.truck_front_axle_offset = 9.0  # Distance from front to front axle center
        self.truck_hitch_offset = 237.0 - 154.0  # Distance from rear axle to ball hitch
        self.truck_num_rear_wheels = 4  # Total rear wheels (set B - non-turning)
        self.truck_wheel_diameter = 32.0  # Wheel diameter
        self.steering_wheel_diameter = 15.5  # Steering wheel diameter

        # Trailer dimensions (in inches) - User's specific trailer
        self.trailer_length = 226.0  # From end of trailer to center of ball joint
        self.trailer_width = 105.0  # Outside tire to outside tire
        self.trailer_tongue_length = 0.0  # Ball joint is at the front of trailer measurement
        self.trailer_num_axles = 1  # One axle location mentioned
        self.trailer_wheels_per_axle = 4  # Assuming dual wheels on each side
        self.trailer_axle_spacing = 0.0  # Single axle
        self.trailer_wheel_diameter = 29.0  # Wheel diameter
        self.trailer_axle_from_end = 156.0  # Distance from end to wheel center

    def to_dict(self):
        return {
            'name': self.name,
            'truck_length': self.truck_length,
            'truck_width': self.truck_width,
            'truck_wheelbase': self.truck_wheelbase,
            'truck_front_axle_offset': self.truck_front_axle_offset,
            'truck_hitch_offset': self.truck_hitch_offset,
            'truck_num_rear_wheels': self.truck_num_rear_wheels,
            'truck_wheel_diameter': self.truck_wheel_diameter,
            'steering_wheel_diameter': self.steering_wheel_diameter,
            'trailer_length': self.trailer_length,
            'trailer_width': self.trailer_width,
            'trailer_tongue_length': self.trailer_tongue_length,
            'trailer_num_axles': self.trailer_num_axles,
            'trailer_wheels_per_axle': self.trailer_wheels_per_axle,
            'trailer_axle_spacing': self.trailer_axle_spacing,
            'trailer_wheel_diameter': self.trailer_wheel_diameter,
            'trailer_axle_from_end': self.trailer_axle_from_end,
        }

    @classmethod
    def from_dict(cls, data):
        config = cls(data.get('name', 'Default'))
        for key, value in data.items():
            if hasattr(config, key):
                setattr(config, key, value)
        return config


class ConfigDialog(QDialog):
    """Dialog for editing vehicle configurations"""
    def __init__(self, config=None, parent=None):
        super().__init__(parent)
        self.config = config if config else VehicleConfig()
        self.setWindowTitle("Vehicle Configuration")
        self.setModal(True)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Name
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Configuration Name:"))
        self.name_input = QLineEdit(self.config.name)
        name_layout.addWidget(self.name_input)
        layout.addLayout(name_layout)

        # Truck Group
        truck_group = QGroupBox("Truck Dimensions (inches)")
        truck_layout = QGridLayout()

        self.truck_length = QDoubleSpinBox()
        self.truck_length.setRange(100, 400)
        self.truck_length.setValue(self.config.truck_length)
        self.truck_length.setSingleStep(1.0)
        truck_layout.addWidget(QLabel("Length:"), 0, 0)
        truck_layout.addWidget(self.truck_length, 0, 1)

        self.truck_width = QDoubleSpinBox()
        self.truck_width.setRange(50, 150)
        self.truck_width.setValue(self.config.truck_width)
        self.truck_width.setSingleStep(1.0)
        truck_layout.addWidget(QLabel("Width:"), 1, 0)
        truck_layout.addWidget(self.truck_width, 1, 1)

        self.truck_wheelbase = QDoubleSpinBox()
        self.truck_wheelbase.setRange(50, 250)
        self.truck_wheelbase.setValue(self.config.truck_wheelbase)
        self.truck_wheelbase.setSingleStep(1.0)
        truck_layout.addWidget(QLabel("Wheelbase:"), 2, 0)
        truck_layout.addWidget(self.truck_wheelbase, 2, 1)

        self.truck_hitch_offset = QDoubleSpinBox()
        self.truck_hitch_offset.setRange(0, 100)
        self.truck_hitch_offset.setValue(self.config.truck_hitch_offset)
        self.truck_hitch_offset.setSingleStep(1.0)
        truck_layout.addWidget(QLabel("Hitch Offset:"), 3, 0)
        truck_layout.addWidget(self.truck_hitch_offset, 3, 1)

        self.truck_num_rear_wheels = QSpinBox()
        self.truck_num_rear_wheels.setRange(2, 6)
        self.truck_num_rear_wheels.setValue(self.config.truck_num_rear_wheels)
        truck_layout.addWidget(QLabel("Rear Wheels:"), 4, 0)
        truck_layout.addWidget(self.truck_num_rear_wheels, 4, 1)

        truck_group.setLayout(truck_layout)
        layout.addWidget(truck_group)

        # Trailer Group
        trailer_group = QGroupBox("Trailer Dimensions (inches)")
        trailer_layout = QGridLayout()

        self.trailer_length = QDoubleSpinBox()
        self.trailer_length.setRange(100, 400)
        self.trailer_length.setValue(self.config.trailer_length)
        self.trailer_length.setSingleStep(1.0)
        trailer_layout.addWidget(QLabel("Length:"), 0, 0)
        trailer_layout.addWidget(self.trailer_length, 0, 1)

        self.trailer_width = QDoubleSpinBox()
        self.trailer_width.setRange(50, 150)
        self.trailer_width.setValue(self.config.trailer_width)
        self.trailer_width.setSingleStep(1.0)
        trailer_layout.addWidget(QLabel("Width:"), 1, 0)
        trailer_layout.addWidget(self.trailer_width, 1, 1)

        self.trailer_tongue_length = QDoubleSpinBox()
        self.trailer_tongue_length.setRange(1, 10)
        self.trailer_tongue_length.setValue(self.config.trailer_tongue_length)
        self.trailer_tongue_length.setSingleStep(0.5)
        trailer_layout.addWidget(QLabel("Tongue Length:"), 2, 0)
        trailer_layout.addWidget(self.trailer_tongue_length, 2, 1)

        self.trailer_num_axles = QSpinBox()
        self.trailer_num_axles.setRange(1, 4)
        self.trailer_num_axles.setValue(self.config.trailer_num_axles)
        trailer_layout.addWidget(QLabel("Number of Axles:"), 3, 0)
        trailer_layout.addWidget(self.trailer_num_axles, 3, 1)

        self.trailer_wheels_per_axle = QSpinBox()
        self.trailer_wheels_per_axle.setRange(2, 6)
        self.trailer_wheels_per_axle.setValue(self.config.trailer_wheels_per_axle)
        trailer_layout.addWidget(QLabel("Wheels per Axle:"), 4, 0)
        trailer_layout.addWidget(self.trailer_wheels_per_axle, 4, 1)

        self.trailer_axle_spacing = QDoubleSpinBox()
        self.trailer_axle_spacing.setRange(1, 10)
        self.trailer_axle_spacing.setValue(self.config.trailer_axle_spacing)
        self.trailer_axle_spacing.setSingleStep(0.5)
        trailer_layout.addWidget(QLabel("Axle Spacing:"), 5, 0)
        trailer_layout.addWidget(self.trailer_axle_spacing, 5, 1)

        trailer_group.setLayout(trailer_layout)
        layout.addWidget(trailer_group)

        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self.setLayout(layout)

    def get_config(self):
        """Get the configuration from the dialog"""
        self.config.name = self.name_input.text()
        self.config.truck_length = self.truck_length.value()
        self.config.truck_width = self.truck_width.value()
        self.config.truck_wheelbase = self.truck_wheelbase.value()
        self.config.truck_hitch_offset = self.truck_hitch_offset.value()
        self.config.truck_num_rear_wheels = self.truck_num_rear_wheels.value()
        self.config.trailer_length = self.trailer_length.value()
        self.config.trailer_width = self.trailer_width.value()
        self.config.trailer_tongue_length = self.trailer_tongue_length.value()
        self.config.trailer_num_axles = self.trailer_num_axles.value()
        self.config.trailer_wheels_per_axle = self.trailer_wheels_per_axle.value()
        self.config.trailer_axle_spacing = self.trailer_axle_spacing.value()
        return self.config


class SteeringWheelWidget(QWidget):
    """Widget to display steering wheel position"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(150, 170)  # Increased height for text below
        self.setMaximumSize(150, 170)
        self.steering_angle = 0  # Current steering angle in degrees

    def set_steering_angle(self, angle):
        """Update the steering wheel angle"""
        self.steering_angle = angle
        self.update()

    def paintEvent(self, event):
        """Draw the steering wheel"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Center of widget - adjusted to leave room for text below
        center_x = self.width() // 2
        center_y = 75  # Fixed position, leaving room below
        radius = 65  # Fixed radius

        # Draw outer wheel
        pen = QPen(QColor(0, 0, 0))
        pen.setWidth(8)
        painter.setPen(pen)
        painter.setBrush(QColor(60, 60, 60))
        painter.drawEllipse(center_x - radius, center_y - radius, radius * 2, radius * 2)

        # Draw center hub
        hub_radius = 20
        painter.setBrush(QColor(40, 40, 40))
        painter.drawEllipse(center_x - hub_radius, center_y - hub_radius, hub_radius * 2, hub_radius * 2)

        # Rotate for steering angle
        painter.save()
        painter.translate(center_x, center_y)
        painter.rotate(-self.steering_angle)

        # Draw spokes
        pen.setWidth(4)
        painter.setPen(pen)
        painter.setBrush(QColor(80, 80, 80))
        for i in range(4):
            angle_rad = math.radians(i * 90)
            x1 = hub_radius * math.cos(angle_rad)
            y1 = hub_radius * math.sin(angle_rad)
            x2 = radius * math.cos(angle_rad)
            y2 = radius * math.sin(angle_rad)
            painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))

        # Draw top indicator (shows which way is "up")
        painter.setBrush(QColor(255, 0, 0))
        painter.setPen(Qt.PenStyle.NoPen)
        indicator = QPolygonF([
            QPointF(0, -radius - 5),
            QPointF(-8, -radius + 5),
            QPointF(8, -radius + 5)
        ])
        painter.drawPolygon(indicator)

        painter.restore()

        # Draw angle text below the wheel
        painter.setPen(QColor(0, 0, 0))
        from PyQt6.QtGui import QFont
        font = QFont()
        font.setPointSize(12)
        font.setBold(True)
        painter.setFont(font)

        angle_text = f"{self.steering_angle:.0f}°"
        if self.steering_angle > 0:
            angle_text += " RIGHT"
        elif self.steering_angle < 0:
            angle_text += " LEFT"
        else:
            angle_text = "STRAIGHT"

        # Draw text below the steering wheel
        text_rect = QRectF(0, 150, self.width(), 20)
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, angle_text)


class SimulationCanvas(QWidget):
    """Canvas for drawing the truck, trailer, and parking space"""

    # Signals for communication with main window
    steering_changed = pyqtSignal(float)  # steering angle
    instructions_changed = pyqtSignal(str)  # instruction text
    adjustment_made = pyqtSignal(str)  # Adjustment log entry

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(800, 600)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        # Simulation state - will be set by reset_position()
        self.truck_x = 0
        self.truck_y = 0
        self.truck_angle = 90  # degrees, 90 is pointing up
        self.steering_angle = 0  # degrees

        self.trailer_angle = 90  # degrees

        # Target parking space - fixed position at bottom center
        self.target_x = 0  # Will be set after widget is shown
        self.target_y = 0  # Will be set after widget is shown
        self.target_angle = 90

        # Scale: pixels per inch - increased for better visibility
        self.scale = 1.5  # Larger scale to see proportions better (463 inches total needs ~695 pixels)

        self.config = VehicleConfig()

        # Adjustment tracking
        self.adjustment_log = []

        # Session tracking
        self.session_active = False
        self.session_start_time = None

        # Keyboard handling
        self.keys_pressed = set()

        # Timer for continuous movement
        self.move_timer = QTimer()
        self.move_timer.timeout.connect(self.handle_movement)
        self.move_timer.setInterval(50)  # 50ms = 20 FPS

        # Set focus to receive keyboard events
        self.setFocus()

    def showEvent(self, event):
        """Initialize positions when widget is first shown"""
        super().showEvent(event)
        # Always reset position on show to ensure proper initialization
        self.reset_position()

    def set_config(self, config):
        """Set the vehicle configuration"""
        self.config = config
        self.update()

    def paintEvent(self, event):
        """Draw the simulation"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Background
        painter.fillRect(self.rect(), QColor(240, 240, 240))

        # Draw grid
        self.draw_grid(painter)

        # Draw target parking space
        self.draw_target(painter)

        # Draw trailer first (behind truck)
        self.draw_trailer(painter)

        # Draw truck
        self.draw_truck(painter)

        # Draw hitch articulation (on top to show connection)
        self.draw_hitch_articulation(painter)

    def draw_grid(self, painter):
        """Draw a grid for reference"""
        pen = QPen(QColor(200, 200, 200))
        pen.setWidth(1)
        painter.setPen(pen)

        # Draw vertical lines every 120 inches (10 feet)
        grid_spacing = int(120 * self.scale)
        for x in range(0, self.width(), grid_spacing):
            painter.drawLine(x, 0, x, self.height())

        # Draw horizontal lines every 120 inches (10 feet)
        for y in range(0, self.height(), grid_spacing):
            painter.drawLine(0, y, self.width(), y)

    def draw_target(self, painter):
        """Draw the target parking space - 3-sided U-shape open at bottom"""
        painter.save()
        painter.translate(self.target_x, self.target_y)
        painter.rotate(-self.target_angle)

        # Draw 3-sided parking space (open at bottom for entry)
        pen = QPen(QColor(0, 200, 0))
        pen.setWidth(3)
        pen.setStyle(Qt.PenStyle.SolidLine)
        painter.setPen(pen)

        total_length = (self.config.trailer_length + self.config.trailer_tongue_length) * self.scale
        half_width = self.config.trailer_width * self.scale / 2

        # Draw back wall (top of space)
        painter.drawLine(QPointF(-half_width, -total_length), QPointF(half_width, -total_length))

        # Draw left side wall
        painter.drawLine(QPointF(-half_width, -total_length), QPointF(-half_width, 0))

        # Draw right side wall
        painter.drawLine(QPointF(half_width, -total_length), QPointF(half_width, 0))

        # BOTTOM is OPEN for entry

        painter.restore()

    def draw_truck(self, painter):
        """Draw the truck with wheels"""
        painter.save()
        painter.translate(self.truck_x, self.truck_y)
        painter.rotate(-self.truck_angle)

        length = self.config.truck_length * self.scale
        width = self.config.truck_width * self.scale
        wheelbase = self.config.truck_wheelbase * self.scale

        # Truck body
        pen = QPen(QColor(0, 0, 200))
        pen.setWidth(2)
        painter.setPen(pen)
        painter.setBrush(QColor(100, 100, 255, 100))

        rect = QRectF(-width/2, -length, width, length)
        painter.drawRect(rect)

        # Draw wheels
        wheel_width = 0.8 * self.scale
        wheel_height = 2 * self.scale

        # Front wheels (steerable)
        painter.save()
        painter.translate(0, -length)
        painter.rotate(-self.steering_angle)
        painter.setBrush(QColor(0, 0, 0))
        # Left front wheel
        painter.drawRect(QRectF(-width/2 - wheel_width, -wheel_height/2, wheel_width, wheel_height))
        # Right front wheel
        painter.drawRect(QRectF(width/2, -wheel_height/2, wheel_width, wheel_height))
        painter.restore()

        # Rear wheels
        rear_axle_pos = -length + wheelbase
        num_wheels = self.config.truck_num_rear_wheels // 2
        painter.setBrush(QColor(0, 0, 0))
        for i in range(num_wheels):
            offset = i * 0.5 * self.scale
            # Left rear wheels
            painter.drawRect(QRectF(-width/2 - wheel_width, rear_axle_pos - wheel_height/2 + offset,
                                   wheel_width, wheel_height))
            # Right rear wheels
            painter.drawRect(QRectF(width/2, rear_axle_pos - wheel_height/2 + offset,
                                   wheel_width, wheel_height))

        # Draw front indicator (triangular arrow)
        arrow_size = 10
        painter.setBrush(QColor(0, 0, 150))
        painter.setPen(Qt.PenStyle.NoPen)
        front_arrow = QPolygonF([
            QPointF(0, -length - arrow_size),  # Tip pointing forward
            QPointF(-arrow_size/2, -length),   # Left base
            QPointF(arrow_size/2, -length)     # Right base
        ])
        painter.drawPolygon(front_arrow)

        painter.restore()

    def draw_trailer(self, painter):
        """Draw the trailer with wheels"""
        # Calculate hitch position
        hitch_x, hitch_y = self.get_hitch_position()

        painter.save()
        painter.translate(hitch_x, hitch_y)
        painter.rotate(-self.trailer_angle)

        tongue_length = self.config.trailer_tongue_length * self.scale
        length = self.config.trailer_length * self.scale
        width = self.config.trailer_width * self.scale

        # Draw tongue
        pen = QPen(QColor(150, 75, 0))
        pen.setWidth(3)
        painter.setPen(pen)
        painter.drawLine(QPointF(0, 0), QPointF(0, -tongue_length))

        # Trailer body
        pen = QPen(QColor(150, 75, 0))
        pen.setWidth(2)
        painter.setPen(pen)
        painter.setBrush(QColor(200, 150, 100, 100))

        rect = QRectF(-width/2, -tongue_length - length, width, length)
        painter.drawRect(rect)

        # Draw axles and wheels
        wheel_width = 0.8 * self.scale
        wheel_height = 2 * self.scale
        painter.setBrush(QColor(0, 0, 0))

        # Position axles
        if self.config.trailer_num_axles == 1:
            axle_positions = [-tongue_length - length/2]
        else:
            total_spacing = self.config.trailer_axle_spacing * self.scale * (self.config.trailer_num_axles - 1)
            start_pos = -tongue_length - length/2 - total_spacing/2
            axle_positions = [start_pos + i * self.config.trailer_axle_spacing * self.scale
                            for i in range(self.config.trailer_num_axles)]

        for axle_pos in axle_positions:
            wheels_per_side = self.config.trailer_wheels_per_axle // 2
            for i in range(wheels_per_side):
                offset = i * 0.5 * self.scale
                # Left wheels
                painter.drawRect(QRectF(-width/2 - wheel_width, axle_pos - wheel_height/2 + offset,
                                       wheel_width, wheel_height))
                # Right wheels
                painter.drawRect(QRectF(width/2, axle_pos - wheel_height/2 + offset,
                                       wheel_width, wheel_height))

        # Draw front indicator (triangular arrow at trailer front)
        arrow_size = 10
        painter.setBrush(QColor(120, 60, 0))
        painter.setPen(Qt.PenStyle.NoPen)
        trailer_front_y = -tongue_length - length
        front_arrow = QPolygonF([
            QPointF(0, trailer_front_y - arrow_size),  # Tip pointing forward
            QPointF(-arrow_size/2, trailer_front_y),   # Left base
            QPointF(arrow_size/2, trailer_front_y)     # Right base
        ])
        painter.drawPolygon(front_arrow)

        painter.restore()

    def draw_hitch_articulation(self, painter):
        """Draw triangular articulation showing hitch connection"""
        # Get hitch position
        hitch_x, hitch_y = self.get_hitch_position()

        # Calculate truck rear position
        truck_angle_rad = math.radians(self.truck_angle)
        wheelbase = self.config.truck_wheelbase * self.scale
        truck_length = self.config.truck_length * self.scale
        hitch_offset = self.config.truck_hitch_offset * self.scale
        rear_axle_offset = truck_length - wheelbase
        truck_width = self.config.truck_width * self.scale

        # Truck rear center (where triangle starts from)
        truck_rear_x = self.truck_x - rear_axle_offset * math.sin(truck_angle_rad)
        truck_rear_y = self.truck_y - rear_axle_offset * math.cos(truck_angle_rad)

        # Draw truck-side triangle (from truck rear to hitch)
        painter.save()
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(100, 100, 255, 120))  # Semi-transparent blue

        # Calculate truck rear corners
        left_x = truck_rear_x - (truck_width/2) * math.cos(truck_angle_rad)
        left_y = truck_rear_y + (truck_width/2) * math.sin(truck_angle_rad)
        right_x = truck_rear_x + (truck_width/2) * math.cos(truck_angle_rad)
        right_y = truck_rear_y - (truck_width/2) * math.sin(truck_angle_rad)

        truck_triangle = QPolygonF([
            QPointF(left_x, left_y),     # Left rear corner
            QPointF(right_x, right_y),   # Right rear corner
            QPointF(hitch_x, hitch_y)    # Hitch ball
        ])
        painter.drawPolygon(truck_triangle)
        painter.restore()

        # Draw trailer-side triangle (from trailer front to hitch)
        painter.save()
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(200, 150, 100, 120))  # Semi-transparent brown

        trailer_angle_rad = math.radians(self.trailer_angle)
        tongue_length = self.config.trailer_tongue_length * self.scale
        trailer_width = self.config.trailer_width * self.scale

        # Trailer front center (where tongue meets trailer body)
        trailer_front_x = hitch_x - tongue_length * math.sin(trailer_angle_rad)
        trailer_front_y = hitch_y - tongue_length * math.cos(trailer_angle_rad)

        # Calculate trailer front corners
        left_x = trailer_front_x - (trailer_width/2) * math.cos(trailer_angle_rad)
        left_y = trailer_front_y + (trailer_width/2) * math.sin(trailer_angle_rad)
        right_x = trailer_front_x + (trailer_width/2) * math.cos(trailer_angle_rad)
        right_y = trailer_front_y - (trailer_width/2) * math.sin(trailer_angle_rad)

        trailer_triangle = QPolygonF([
            QPointF(left_x, left_y),     # Left front corner
            QPointF(right_x, right_y),   # Right front corner
            QPointF(hitch_x, hitch_y)    # Hitch ball
        ])
        painter.drawPolygon(trailer_triangle)
        painter.restore()

        # Draw hitch ball on top (larger and more prominent)
        painter.save()
        pen = QPen(QColor(255, 255, 0))  # Yellow outline
        pen.setWidth(2)
        painter.setPen(pen)
        painter.setBrush(QColor(255, 0, 0))  # Red center
        painter.drawEllipse(QPointF(hitch_x, hitch_y), 6, 6)
        painter.restore()

    def get_hitch_position(self):
        """Calculate the hitch position in screen coordinates"""
        angle_rad = math.radians(self.truck_angle)
        wheelbase = self.config.truck_wheelbase * self.scale
        front_axle_offset = self.config.truck_front_axle_offset * self.scale
        hitch_offset = self.config.truck_hitch_offset * self.scale

        # truck_x, truck_y is at the rear bumper center of the truck (y=0 in local coords)
        # Rear axle is at: front_axle_offset + wheelbase from the front
        # Since truck front is at y=-length, rear axle is at: -length + front_axle_offset + wheelbase
        # Which simplifies to: -(length - front_axle_offset - wheelbase) from y=0
        # Or: rear_bumper_to_rear_axle distance forward from the rear bumper

        # Distance from rear bumper to rear axle
        length = self.config.truck_length * self.scale
        rear_bumper_to_rear_axle = length - front_axle_offset - wheelbase

        # Hitch is hitch_offset BEHIND the rear axle
        # So from rear bumper: forward to rear axle, then back by hitch_offset
        total_offset_from_rear = rear_bumper_to_rear_axle - hitch_offset

        # Move from truck rear position along truck direction
        hitch_x = self.truck_x - total_offset_from_rear * math.sin(angle_rad)
        hitch_y = self.truck_y - total_offset_from_rear * math.cos(angle_rad)

        return hitch_x, hitch_y

    def move_forward(self, distance):
        """Move the truck forward by distance (in feet)"""
        distance_pixels = distance * self.scale
        angle_rad = math.radians(self.truck_angle)

        self.truck_x += distance_pixels * math.sin(angle_rad)
        self.truck_y += distance_pixels * math.cos(angle_rad)

        # Update truck angle based on steering
        if abs(self.steering_angle) > 0.1:
            wheelbase = self.config.truck_wheelbase
            turning_radius = wheelbase / math.tan(math.radians(abs(self.steering_angle)))
            angle_change = math.degrees(distance / turning_radius)
            if self.steering_angle > 0:
                self.truck_angle += angle_change
            else:
                self.truck_angle -= angle_change

        # Update trailer angle
        self.update_trailer_angle(distance)

        self.update()

    def move_backward(self, distance):
        """Move the truck backward by distance (in feet)"""
        distance_pixels = distance * self.scale
        angle_rad = math.radians(self.truck_angle)

        self.truck_x -= distance_pixels * math.sin(angle_rad)
        self.truck_y -= distance_pixels * math.cos(angle_rad)

        # Update truck angle based on steering (reversed when backing)
        if abs(self.steering_angle) > 0.1:
            wheelbase = self.config.truck_wheelbase
            turning_radius = wheelbase / math.tan(math.radians(abs(self.steering_angle)))
            angle_change = math.degrees(distance / turning_radius)
            if self.steering_angle > 0:
                self.truck_angle -= angle_change
            else:
                self.truck_angle += angle_change

        # Update trailer angle
        self.update_trailer_angle(-distance)

        self.update()

    def update_trailer_angle(self, distance):
        """Update trailer angle based on movement - proper trailer kinematics"""
        # The trailer follows the hitch point, with its axle tracking behind
        # Key insight: The trailer rotates based on the angle between:
        # 1. The direction from trailer axle to hitch (current trailer orientation)
        # 2. The direction the hitch is moving (truck's direction)

        # Get angle difference between truck and trailer
        angle_diff = self.truck_angle - self.trailer_angle

        # Normalize angle difference to -180 to 180
        while angle_diff > 180:
            angle_diff -= 360
        while angle_diff < -180:
            angle_diff += 360

        # The effective length is from hitch to trailer axle
        # This is the distance from hitch ball to the point where trailer wheels touch ground
        trailer_length_to_axle = self.config.trailer_length - self.config.trailer_axle_from_end
        effective_length = self.config.trailer_tongue_length + trailer_length_to_axle

        if abs(effective_length) > 0.1:
            # When the truck moves, the hitch point moves in the truck's direction
            # The trailer must rotate to keep its axle following behind the hitch
            # Formula: angle_change = (distance / effective_length) * sin(angle_diff)
            angle_change = math.degrees(distance * math.sin(math.radians(angle_diff)) / effective_length)
            self.trailer_angle += angle_change

    def steer(self, angle):
        """Set steering angle (negative = left, positive = right)"""
        old_angle = self.steering_angle
        self.steering_angle = max(-45, min(45, angle))

        # Log significant steering changes (more than 5 degrees)
        if abs(self.steering_angle - old_angle) > 5:
            direction = "RIGHT" if self.steering_angle > old_angle else "LEFT"
            log_entry = f"Steer {direction} to {self.steering_angle:.0f}°"
            self.adjustment_made.emit(log_entry)

        self.update()

    def start_session(self):
        """Start a new practice session"""
        from datetime import datetime
        self.session_active = True
        self.session_start_time = datetime.now()
        self.adjustment_log.clear()
        log_entry = "SESSION STARTED"
        self.adjustment_made.emit(log_entry)
        self.reset_position()
        # Ensure canvas has keyboard focus
        self.setFocus()
        self.activateWindow()

    def stop_session(self):
        """Stop the current practice session"""
        from datetime import datetime
        if self.session_active and self.session_start_time:
            duration = datetime.now() - self.session_start_time
            minutes = int(duration.total_seconds() // 60)
            seconds = int(duration.total_seconds() % 60)
            log_entry = f"SESSION ENDED - Duration: {minutes}m {seconds}s"
            self.adjustment_made.emit(log_entry)
        self.session_active = False
        self.session_start_time = None

    def reset_position(self):
        """Reset to starting position - top right of screen"""
        # Start with truck and trailer at a slight angle
        # This ensures both vehicles are clearly visible and separate
        # Position them so they're connected at the hitch

        self.truck_angle = 165  # Pointing down and slightly left
        self.trailer_angle = 180  # Pointing straight down
        self.steering_angle = 0

        # Calculate truck position
        # Place truck near top-right with enough room
        truck_length = self.config.truck_length * self.scale
        self.truck_x = self.width() - 250
        self.truck_y = truck_length + 150  # Room for truck to be visible

        # Ensure parking space is set (in case widget was resized)
        self.target_x = self.width() // 2  # Center horizontally
        self.target_y = self.height() - 200  # Near bottom with margin
        self.target_angle = 90  # Parking space opening toward bottom

        print(f"Reset: truck at ({self.truck_x}, {self.truck_y}), canvas size: ({self.width()}, {self.height()})")
        print(f"Truck angle: {self.truck_angle}°, Trailer angle: {self.trailer_angle}°")
        self.update()

    def keyPressEvent(self, event):
        """Handle key press events"""
        self.keys_pressed.add(event.key())

        if not self.move_timer.isActive():
            self.move_timer.start()

        event.accept()

    def keyReleaseEvent(self, event):
        """Handle key release events"""
        self.keys_pressed.discard(event.key())

        if not self.keys_pressed:
            self.move_timer.stop()

        event.accept()

    def mousePressEvent(self, event):
        """Ensure focus when clicked"""
        self.setFocus()
        event.accept()

    def handle_movement(self):
        """Handle continuous movement based on pressed keys"""
        move_distance = 2.0  # inches per frame (adjusted for inch scale)
        steer_change = 2  # degrees per frame

        # Forward/Backward
        if Qt.Key.Key_Up in self.keys_pressed:
            self.move_forward(move_distance)
        elif Qt.Key.Key_Down in self.keys_pressed:
            self.move_backward(move_distance)

        # Steering
        if Qt.Key.Key_Left in self.keys_pressed:
            self.steer(self.steering_angle - steer_change)
        elif Qt.Key.Key_Right in self.keys_pressed:
            self.steer(self.steering_angle + steer_change)
        else:
            # Return to center when no steering input
            if abs(self.steering_angle) > steer_change:
                if self.steering_angle > 0:
                    self.steer(self.steering_angle - steer_change)
                else:
                    self.steer(self.steering_angle + steer_change)
            else:
                self.steer(0)

        # Emit signal for steering label update
        self.steering_changed.emit(self.steering_angle)

        # Update instructions
        self.update_instructions()

    def update_instructions(self):
        """Update backing instructions based on current state"""
        # Calculate angle difference between trailer and target
        angle_diff = self.target_angle - self.trailer_angle

        # Normalize to -180 to 180
        while angle_diff > 180:
            angle_diff -= 360
        while angle_diff < -180:
            angle_diff += 360

        # Calculate distance to target
        dx = self.target_x - self.get_hitch_position()[0]
        dy = self.target_y - self.get_hitch_position()[1]
        distance = math.sqrt(dx*dx + dy*dy) / self.scale

        # Generate instruction
        if distance < 60:  # 60 inches = 5 feet
            instruction = "✓ Great! You're at the target position!"
        elif abs(angle_diff) < 5:
            instruction = f"Keep going straight!\nDistance to target: {distance:.0f} in"
        elif angle_diff > 5:
            instruction = (
                f"To turn trailer LEFT:\n"
                f"Steer RIGHT (→) while backing up (↓)\n"
                f"Angle to correct: {abs(angle_diff):.1f}°\n"
                f"Distance: {distance:.0f} in"
            )
        else:
            instruction = (
                f"To turn trailer RIGHT:\n"
                f"Steer LEFT (←) while backing up (↓)\n"
                f"Angle to correct: {abs(angle_diff):.1f}°\n"
                f"Distance: {distance:.0f} in"
            )

        # Emit signal for instruction label update
        self.instructions_changed.emit(instruction)


class TrailerBackupGuide(QMainWindow):
    """Main application window"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Trailer Backup Guide")
        self.setGeometry(100, 100, 1200, 800)

        self.config_file = Path.home() / '.trailer_backup_configs.json'
        self.configs = {}
        self.current_config_name = None

        self.load_configs()

        self.init_ui()

    def init_ui(self):
        """Initialize the user interface"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout()

        # Left panel - controls
        left_panel = QWidget()
        left_layout = QVBoxLayout()

        # Configuration selection
        config_group = QGroupBox("Configuration")
        config_layout = QVBoxLayout()

        config_select_layout = QHBoxLayout()
        self.config_combo = QComboBox()
        self.config_combo.currentTextChanged.connect(self.on_config_changed)
        config_select_layout.addWidget(QLabel("Select:"))
        config_select_layout.addWidget(self.config_combo)
        config_layout.addLayout(config_select_layout)

        config_buttons = QHBoxLayout()
        new_btn = QPushButton("New")
        new_btn.clicked.connect(self.new_config)
        config_buttons.addWidget(new_btn)

        edit_btn = QPushButton("Edit")
        edit_btn.clicked.connect(self.edit_config)
        config_buttons.addWidget(edit_btn)

        delete_btn = QPushButton("Delete")
        delete_btn.clicked.connect(self.delete_config)
        config_buttons.addWidget(delete_btn)

        config_layout.addLayout(config_buttons)
        config_group.setLayout(config_layout)
        left_layout.addWidget(config_group)

        # Session Control
        session_group = QGroupBox("Practice Session")
        session_layout = QVBoxLayout()

        self.start_session_btn = QPushButton("Start Session")
        self.start_session_btn.clicked.connect(self.start_session)
        self.start_session_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; font-weight: bold; padding: 10px; }")
        session_layout.addWidget(self.start_session_btn)

        self.stop_session_btn = QPushButton("Stop Session")
        self.stop_session_btn.clicked.connect(self.stop_session)
        self.stop_session_btn.setEnabled(False)
        self.stop_session_btn.setStyleSheet("QPushButton { background-color: #f44336; color: white; font-weight: bold; padding: 10px; }")
        session_layout.addWidget(self.stop_session_btn)

        session_group.setLayout(session_layout)
        left_layout.addWidget(session_group)

        # Controls
        controls_group = QGroupBox("Controls")
        controls_layout = QVBoxLayout()

        controls_layout.addWidget(QLabel("Arrow Keys:"))
        controls_layout.addWidget(QLabel("  ↑ : Move Forward"))
        controls_layout.addWidget(QLabel("  ↓ : Move Backward"))
        controls_layout.addWidget(QLabel("  ← : Steer Left"))
        controls_layout.addWidget(QLabel("  → : Steer Right"))

        reset_btn = QPushButton("Reset Position")
        reset_btn.clicked.connect(self.reset_simulation)
        controls_layout.addWidget(reset_btn)

        controls_group.setLayout(controls_layout)
        left_layout.addWidget(controls_group)

        # Instructions
        self.instructions_group = QGroupBox("Backing Instructions")
        instructions_layout = QVBoxLayout()
        self.instruction_label = QLabel("Ready to practice!")
        self.instruction_label.setWordWrap(True)
        instructions_layout.addWidget(self.instruction_label)
        self.instructions_group.setLayout(instructions_layout)
        left_layout.addWidget(self.instructions_group)

        # Steering Wheel Visualization
        steering_group = QGroupBox("Steering Wheel")
        steering_layout = QVBoxLayout()
        self.steering_wheel = SteeringWheelWidget()
        steering_layout.addWidget(self.steering_wheel, alignment=Qt.AlignmentFlag.AlignCenter)
        steering_group.setLayout(steering_layout)
        left_layout.addWidget(steering_group)

        # Adjustment Log
        log_group = QGroupBox("Adjustments Log")
        log_layout = QVBoxLayout()
        self.adjustment_log = QTextEdit()
        self.adjustment_log.setReadOnly(True)
        self.adjustment_log.setMaximumHeight(150)
        log_layout.addWidget(self.adjustment_log)
        clear_log_btn = QPushButton("Clear Log")
        clear_log_btn.clicked.connect(self.clear_adjustment_log)
        log_layout.addWidget(clear_log_btn)
        log_group.setLayout(log_layout)
        left_layout.addWidget(log_group)

        left_layout.addStretch()
        left_panel.setLayout(left_layout)
        left_panel.setMaximumWidth(300)

        main_layout.addWidget(left_panel)

        # Right panel - simulation canvas
        self.canvas = SimulationCanvas()
        main_layout.addWidget(self.canvas)

        # Connect canvas signals
        self.canvas.steering_changed.connect(self.on_steering_changed)
        self.canvas.instructions_changed.connect(self.on_instructions_changed)
        self.canvas.adjustment_made.connect(self.on_adjustment_made)

        central_widget.setLayout(main_layout)

        self.update_config_list()

    def on_steering_changed(self, angle):
        """Update steering wheel visualization when canvas emits signal"""
        self.steering_wheel.set_steering_angle(angle)

    def on_instructions_changed(self, instruction):
        """Update instruction label when canvas emits signal"""
        self.instruction_label.setText(instruction)

    def on_adjustment_made(self, log_entry):
        """Add entry to adjustment log"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.adjustment_log.append(f"[{timestamp}] {log_entry}")

    def clear_adjustment_log(self):
        """Clear the adjustment log"""
        self.adjustment_log.clear()

    def start_session(self):
        """Start a new practice session"""
        self.canvas.start_session()
        self.start_session_btn.setEnabled(False)
        self.stop_session_btn.setEnabled(True)

    def stop_session(self):
        """Stop the current practice session"""
        self.canvas.stop_session()
        self.start_session_btn.setEnabled(True)
        self.stop_session_btn.setEnabled(False)

    def reset_simulation(self):
        """Reset the simulation"""
        self.canvas.reset_position()
        self.canvas.update_instructions()

    def load_configs(self):
        """Load saved configurations"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                    for name, config_data in data.items():
                        self.configs[name] = VehicleConfig.from_dict(config_data)
            except Exception as e:
                print(f"Error loading configs: {e}")

        # Create default config if none exist
        if not self.configs:
            self.configs['Default'] = VehicleConfig('Default')
            self.save_configs()

    def save_configs(self):
        """Save configurations to file"""
        try:
            data = {name: config.to_dict() for name, config in self.configs.items()}
            with open(self.config_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to save configs: {e}")

    def update_config_list(self):
        """Update the configuration combo box"""
        current = self.config_combo.currentText()
        self.config_combo.clear()
        self.config_combo.addItems(sorted(self.configs.keys()))

        if current and current in self.configs:
            self.config_combo.setCurrentText(current)
        elif self.configs:
            self.config_combo.setCurrentText(list(self.configs.keys())[0])

    def on_config_changed(self, name):
        """Handle configuration selection change"""
        if name and name in self.configs:
            self.current_config_name = name
            self.canvas.set_config(self.configs[name])
            self.reset_simulation()

    def new_config(self):
        """Create a new configuration"""
        dialog = ConfigDialog(VehicleConfig("New Config"), self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            config = dialog.get_config()
            if config.name in self.configs:
                reply = QMessageBox.question(
                    self, "Overwrite?",
                    f"Configuration '{config.name}' already exists. Overwrite?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.No:
                    return

            self.configs[config.name] = config
            self.save_configs()
            self.update_config_list()
            self.config_combo.setCurrentText(config.name)

    def edit_config(self):
        """Edit the current configuration"""
        name = self.config_combo.currentText()
        if not name:
            return

        config = self.configs[name]
        dialog = ConfigDialog(config, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_config = dialog.get_config()

            # If name changed, remove old and add new
            if new_config.name != name:
                del self.configs[name]

            self.configs[new_config.name] = new_config
            self.save_configs()
            self.update_config_list()
            self.config_combo.setCurrentText(new_config.name)

    def delete_config(self):
        """Delete the current configuration"""
        name = self.config_combo.currentText()
        if not name:
            return

        if len(self.configs) <= 1:
            QMessageBox.warning(self, "Cannot Delete",
                              "Cannot delete the last configuration.")
            return

        reply = QMessageBox.question(
            self, "Delete Configuration",
            f"Delete configuration '{name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            del self.configs[name]
            self.save_configs()
            self.update_config_list()


def main():
    app = QApplication(sys.argv)
    window = TrailerBackupGuide()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
