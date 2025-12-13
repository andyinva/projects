#!/usr/bin/env python3
"""
Generate a large, detailed image of the truck and trailer for modification.
This creates a high-resolution PNG image showing the truck and trailer from above.
"""

import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt, QPointF, QRectF
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QPolygonF, QImage
import math


class VehicleConfig:
    """Store configuration for truck and trailer"""
    def __init__(self):
        # Truck dimensions (in inches) - User's specific truck
        self.truck_length = 229.0
        self.truck_width = 79.0
        self.truck_wheelbase = 154.0 - 9.0
        self.truck_front_axle_offset = 9.0
        self.truck_hitch_offset = 237.0 - 154.0
        self.truck_num_rear_wheels = 4
        self.truck_wheel_diameter = 32.0

        # Trailer dimensions (in inches) - User's specific trailer
        self.trailer_length = 226.0
        self.trailer_width = 105.0
        self.trailer_tongue_length = 0.0
        self.trailer_num_axles = 1
        self.trailer_wheels_per_axle = 4
        self.trailer_axle_spacing = 0.0
        self.trailer_wheel_diameter = 29.0
        self.trailer_axle_from_end = 156.0


def draw_truck(painter, x, y, angle, scale, config):
    """Draw the truck with wheels"""
    painter.save()
    painter.translate(x, y)
    painter.rotate(-angle)

    length = config.truck_length * scale
    width = config.truck_width * scale
    wheelbase = config.truck_wheelbase * scale

    # Truck body
    pen = QPen(QColor(0, 100, 200))
    pen.setWidth(4)
    painter.setPen(pen)
    painter.setBrush(QColor(100, 150, 255, 150))

    rect = QRectF(-width/2, -length, width, length)
    painter.drawRect(rect)

    # Draw front axle line
    front_axle_pos = -length + config.truck_front_axle_offset * scale
    pen.setColor(QColor(0, 0, 0))
    pen.setWidth(2)
    painter.setPen(pen)
    painter.drawLine(QPointF(-width/2 - 10, front_axle_pos),
                    QPointF(width/2 + 10, front_axle_pos))

    # Draw rear axle line
    rear_axle_pos = -length + wheelbase
    painter.drawLine(QPointF(-width/2 - 10, rear_axle_pos),
                    QPointF(width/2 + 10, rear_axle_pos))

    # Draw wheels
    wheel_width = config.truck_wheel_diameter * scale * 0.3
    wheel_height = config.truck_wheel_diameter * scale

    # Front wheels (aligned with steering)
    painter.setBrush(QColor(0, 0, 0))
    painter.drawRect(QRectF(-width/2 - wheel_width, front_axle_pos - wheel_height/2,
                           wheel_width, wheel_height))
    painter.drawRect(QRectF(width/2, front_axle_pos - wheel_height/2,
                           wheel_width, wheel_height))

    # Rear wheels (multiple)
    num_wheels = config.truck_num_rear_wheels // 2
    for i in range(num_wheels):
        offset = i * 0.5 * scale
        # Left rear wheels
        painter.drawRect(QRectF(-width/2 - wheel_width, rear_axle_pos - wheel_height/2 + offset,
                               wheel_width, wheel_height))
        # Right rear wheels
        painter.drawRect(QRectF(width/2, rear_axle_pos - wheel_height/2 + offset,
                               wheel_width, wheel_height))

    # Draw front indicator (triangular arrow)
    arrow_size = 20
    painter.setBrush(QColor(0, 0, 150))
    painter.setPen(Qt.PenStyle.NoPen)
    front_arrow = QPolygonF([
        QPointF(0, -length - arrow_size),  # Tip pointing forward
        QPointF(-arrow_size/2, -length),   # Left base
        QPointF(arrow_size/2, -length)     # Right base
    ])
    painter.drawPolygon(front_arrow)

    # Add labels
    from PyQt6.QtGui import QFont
    font = QFont()
    font.setPointSize(16)
    font.setBold(True)
    painter.setFont(font)
    painter.setPen(QColor(255, 255, 255))
    text_rect = QRectF(-width/2, -length/2 - 20, width, 40)
    painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, "TRUCK")

    painter.restore()


def draw_trailer(painter, hitch_x, hitch_y, angle, scale, config):
    """Draw the trailer with wheels"""
    painter.save()
    painter.translate(hitch_x, hitch_y)
    painter.rotate(-angle)

    tongue_length = config.trailer_tongue_length * scale
    length = config.trailer_length * scale
    width = config.trailer_width * scale

    # Draw tongue
    pen = QPen(QColor(150, 75, 0))
    pen.setWidth(6)
    painter.setPen(pen)
    painter.drawLine(QPointF(0, 0), QPointF(0, -tongue_length))

    # Trailer body
    pen = QPen(QColor(150, 75, 0))
    pen.setWidth(4)
    painter.setPen(pen)
    painter.setBrush(QColor(200, 150, 100, 150))

    rect = QRectF(-width/2, -tongue_length - length, width, length)
    painter.drawRect(rect)

    # Draw axle position
    axle_pos = -tongue_length - config.trailer_axle_from_end * scale
    pen.setColor(QColor(0, 0, 0))
    pen.setWidth(2)
    painter.setPen(pen)
    painter.drawLine(QPointF(-width/2 - 10, axle_pos),
                    QPointF(width/2 + 10, axle_pos))

    # Draw wheels
    wheel_width = config.trailer_wheel_diameter * scale * 0.3
    wheel_height = config.trailer_wheel_diameter * scale

    painter.setBrush(QColor(0, 0, 0))
    wheels_per_side = config.trailer_wheels_per_axle // 2
    for i in range(wheels_per_side):
        offset = i * 0.5 * scale
        # Left wheels
        painter.drawRect(QRectF(-width/2 - wheel_width, axle_pos - wheel_height/2 + offset,
                               wheel_width, wheel_height))
        # Right wheels
        painter.drawRect(QRectF(width/2, axle_pos - wheel_height/2 + offset,
                               wheel_width, wheel_height))

    # Draw front indicator (triangular arrow at trailer front)
    arrow_size = 20
    painter.setBrush(QColor(120, 60, 0))
    painter.setPen(Qt.PenStyle.NoPen)
    trailer_front_y = -tongue_length - length
    front_arrow = QPolygonF([
        QPointF(0, trailer_front_y - arrow_size),  # Tip pointing forward
        QPointF(-arrow_size/2, trailer_front_y),   # Left base
        QPointF(arrow_size/2, trailer_front_y)     # Right base
    ])
    painter.drawPolygon(front_arrow)

    # Add labels
    from PyQt6.QtGui import QFont
    font = QFont()
    font.setPointSize(16)
    font.setBold(True)
    painter.setFont(font)
    painter.setPen(QColor(255, 255, 255))
    text_rect = QRectF(-width/2, -tongue_length - length/2 - 20, width, 40)
    painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, "TRAILER")

    painter.restore()


def draw_hitch_articulation(painter, truck_x, truck_y, truck_angle, hitch_x, hitch_y,
                           trailer_angle, scale, config):
    """Draw triangular articulation showing hitch connection"""
    # Calculate truck rear position
    truck_angle_rad = math.radians(truck_angle)
    wheelbase = config.truck_wheelbase * scale
    truck_length = config.truck_length * scale
    rear_axle_offset = truck_length - wheelbase
    truck_width = config.truck_width * scale

    # Truck rear center
    truck_rear_x = truck_x - rear_axle_offset * math.sin(truck_angle_rad)
    truck_rear_y = truck_y - rear_axle_offset * math.cos(truck_angle_rad)

    # Draw truck-side triangle
    painter.save()
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor(100, 100, 255, 120))

    left_x = truck_rear_x - (truck_width/2) * math.cos(truck_angle_rad)
    left_y = truck_rear_y + (truck_width/2) * math.sin(truck_angle_rad)
    right_x = truck_rear_x + (truck_width/2) * math.cos(truck_angle_rad)
    right_y = truck_rear_y - (truck_width/2) * math.sin(truck_angle_rad)

    truck_triangle = QPolygonF([
        QPointF(left_x, left_y),
        QPointF(right_x, right_y),
        QPointF(hitch_x, hitch_y)
    ])
    painter.drawPolygon(truck_triangle)
    painter.restore()

    # Draw trailer-side triangle
    painter.save()
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor(200, 150, 100, 120))

    trailer_angle_rad = math.radians(trailer_angle)
    tongue_length = config.trailer_tongue_length * scale
    trailer_width = config.trailer_width * scale

    trailer_front_x = hitch_x - tongue_length * math.sin(trailer_angle_rad)
    trailer_front_y = hitch_y - tongue_length * math.cos(trailer_angle_rad)

    left_x = trailer_front_x - (trailer_width/2) * math.cos(trailer_angle_rad)
    left_y = trailer_front_y + (trailer_width/2) * math.sin(trailer_angle_rad)
    right_x = trailer_front_x + (trailer_width/2) * math.cos(trailer_angle_rad)
    right_y = trailer_front_y - (trailer_width/2) * math.sin(trailer_angle_rad)

    trailer_triangle = QPolygonF([
        QPointF(left_x, left_y),
        QPointF(right_x, right_y),
        QPointF(hitch_x, hitch_y)
    ])
    painter.drawPolygon(trailer_triangle)
    painter.restore()

    # Draw hitch ball
    painter.save()
    pen = QPen(QColor(255, 255, 0))
    pen.setWidth(3)
    painter.setPen(pen)
    painter.setBrush(QColor(255, 0, 0))
    painter.drawEllipse(QPointF(hitch_x, hitch_y), 12, 12)
    painter.restore()


def get_hitch_position(truck_x, truck_y, truck_angle, scale, config):
    """Calculate the hitch position"""
    angle_rad = math.radians(truck_angle)
    wheelbase = config.truck_wheelbase * scale
    length = config.truck_length * scale
    hitch_offset = config.truck_hitch_offset * scale

    rear_axle_offset = length - wheelbase
    total_offset = rear_axle_offset + hitch_offset

    hitch_x = truck_x - total_offset * math.sin(angle_rad)
    hitch_y = truck_y - total_offset * math.cos(angle_rad)

    return hitch_x, hitch_y


def add_dimension_lines(painter, scale, config):
    """Add dimension annotations"""
    from PyQt6.QtGui import QFont
    font = QFont()
    font.setPointSize(12)
    painter.setFont(font)
    painter.setPen(QColor(0, 0, 0))

    # Add dimension text at bottom
    y_pos = 1400
    painter.drawText(50, y_pos, f"Truck Length: {config.truck_length}\"")
    painter.drawText(50, y_pos + 25, f"Truck Width: {config.truck_width}\"")
    painter.drawText(50, y_pos + 50, f"Truck Wheelbase: {config.truck_wheelbase}\"")
    painter.drawText(50, y_pos + 75, f"Hitch Offset: {config.truck_hitch_offset}\"")

    painter.drawText(400, y_pos, f"Trailer Length: {config.trailer_length}\"")
    painter.drawText(400, y_pos + 25, f"Trailer Width: {config.trailer_width}\"")
    painter.drawText(400, y_pos + 50, f"Trailer Axle from End: {config.trailer_axle_from_end}\"")

    painter.drawText(800, y_pos, f"Scale: {scale:.1f} pixels/inch")
    painter.drawText(800, y_pos + 25, "Total Length: {:.1f}\"".format(
        config.truck_length + config.trailer_length))


def generate_vehicle_image(output_filename="truck_trailer_diagram.png"):
    """Generate a large image of the truck and trailer"""

    # Create QApplication (required for Qt)
    app = QApplication(sys.argv)

    # Configuration
    config = VehicleConfig()

    # Scale: 3 pixels per inch for high resolution
    scale = 3.0

    # Image size (enough for truck + trailer + margins)
    total_length = (config.truck_length + config.trailer_length +
                   config.trailer_tongue_length) * scale
    max_width = max(config.truck_width, config.trailer_width) * scale

    image_width = int(max_width + 400)  # Extra margin
    image_height = int(total_length + 400)  # Extra margin

    # Create image
    image = QImage(image_width, image_height, QImage.Format.Format_ARGB32)
    image.fill(QColor(255, 255, 255))  # White background

    # Create painter
    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    # Position vehicles in center
    truck_x = image_width / 2
    truck_y = 200 + config.truck_length * scale
    truck_angle = 180  # Pointing down
    trailer_angle = 180  # Aligned with truck

    # Calculate hitch position
    hitch_x, hitch_y = get_hitch_position(truck_x, truck_y, truck_angle, scale, config)

    # Draw components
    draw_trailer(painter, hitch_x, hitch_y, trailer_angle, scale, config)
    draw_truck(painter, truck_x, truck_y, truck_angle, scale, config)
    draw_hitch_articulation(painter, truck_x, truck_y, truck_angle,
                          hitch_x, hitch_y, trailer_angle, scale, config)

    # Add dimension annotations
    add_dimension_lines(painter, scale, config)

    # Add title
    from PyQt6.QtGui import QFont
    font = QFont()
    font.setPointSize(24)
    font.setBold(True)
    painter.setFont(font)
    painter.setPen(QColor(0, 0, 0))
    title_rect = QRectF(0, 20, image_width, 50)
    painter.drawText(title_rect, Qt.AlignmentFlag.AlignCenter,
                    "Truck & Trailer Diagram - Top View")

    painter.end()

    # Save image
    success = image.save(output_filename)

    if success:
        print(f"Image saved successfully: {output_filename}")
        print(f"Image size: {image_width} x {image_height} pixels")
        print(f"Scale: {scale} pixels per inch")
    else:
        print(f"Failed to save image: {output_filename}")

    return success


if __name__ == "__main__":
    # Generate the image
    output_file = "truck_trailer_diagram.png"
    generate_vehicle_image(output_file)
