#!/usr/bin/env python3
"""
Fractal Explorer - Interactive Mandelbrot and Julia Set Viewer
Features:
- Smooth color gradients based on iteration counts
- Click-to-zoom functionality for infinite detail exploration
- Real-time parameter adjustment for Julia sets
- Toggle between Mandelbrot and Julia set modes
"""

import sys
import math
import numpy as np
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QPushButton, QLabel, QSlider,
                             QComboBox, QDoubleSpinBox, QGroupBox)
from PyQt6.QtCore import Qt, QTimer, QPoint
from PyQt6.QtGui import QImage, QPainter, QPixmap, QColor, QCursor


class FractalCanvas(QWidget):
    """Canvas widget for rendering fractals"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(800, 600)
        self.image = None
        self.fractal_type = "mandelbrot"

        # Julia set parameters
        self.julia_c_real = -0.7
        self.julia_c_imag = 0.27015

        # View parameters
        self.center_x = -0.5
        self.center_y = 0.0
        self.zoom = 1.0

        # Rendering parameters
        self.max_iterations = 256
        self.color_scheme = "smooth"

        # Callback for zoom changes
        self.zoom_changed_callback = None

        # Set cursor for precise clicking
        self.setCursor(QCursor(Qt.CursorShape.CrossCursor))

    def set_fractal_type(self, fractal_type):
        """Switch between Mandelbrot and Julia sets"""
        self.fractal_type = fractal_type
        if fractal_type == "mandelbrot":
            self.center_x = -0.5
            self.center_y = 0.0
            self.zoom = 1.0
        else:  # julia
            self.center_x = 0.0
            self.center_y = 0.0
            self.zoom = 1.0
        self.render_fractal()

    def set_julia_params(self, c_real, c_imag):
        """Update Julia set parameters"""
        self.julia_c_real = c_real
        self.julia_c_imag = c_imag
        if self.fractal_type == "julia":
            self.render_fractal()

    def set_max_iterations(self, iterations):
        """Update maximum iteration count"""
        self.max_iterations = iterations
        self.render_fractal()

    def reset_view(self):
        """Reset view to default"""
        if self.fractal_type == "mandelbrot":
            self.center_x = -0.5
            self.center_y = 0.0
        else:
            self.center_x = 0.0
            self.center_y = 0.0
        self.zoom = 1.0
        self.render_fractal()

    def calculate_mandelbrot(self, width, height):
        """Calculate Mandelbrot set with smooth coloring"""
        # Calculate the complex plane bounds
        aspect_ratio = width / height
        view_width = 3.5 / self.zoom
        view_height = view_width / aspect_ratio

        x_min = self.center_x - view_width / 2
        x_max = self.center_x + view_width / 2
        y_min = self.center_y - view_height / 2
        y_max = self.center_y + view_height / 2

        # Create coordinate arrays
        x = np.linspace(x_min, x_max, width)
        y = np.linspace(y_min, y_max, height)
        X, Y = np.meshgrid(x, y)
        C = X + 1j * Y

        # Initialize arrays
        Z = np.zeros_like(C, dtype=np.complex128)
        M = np.zeros(C.shape, dtype=float)

        # Iterate
        for i in range(self.max_iterations):
            # Calculate which points haven't diverged
            mask = np.abs(Z) <= 2

            # Update Z for non-diverged points
            Z[mask] = Z[mask]**2 + C[mask]

            # Smooth coloring: record iteration + fractional part
            newly_diverged = (np.abs(Z) > 2) & (M == 0)
            if np.any(newly_diverged):
                M[newly_diverged] = i + 1 - np.log2(np.log2(np.abs(Z[newly_diverged])))

        # Normalize to 0-1 range
        M[M == 0] = self.max_iterations
        M = M / self.max_iterations

        return M

    def calculate_julia(self, width, height):
        """Calculate Julia set with smooth coloring"""
        # Calculate the complex plane bounds
        aspect_ratio = width / height
        view_width = 3.5 / self.zoom
        view_height = view_width / aspect_ratio

        x_min = self.center_x - view_width / 2
        x_max = self.center_x + view_width / 2
        y_min = self.center_y - view_height / 2
        y_max = self.center_y + view_height / 2

        # Create coordinate arrays
        x = np.linspace(x_min, x_max, width)
        y = np.linspace(y_min, y_max, height)
        X, Y = np.meshgrid(x, y)
        Z = X + 1j * Y

        # Julia set constant
        C = self.julia_c_real + 1j * self.julia_c_imag

        # Initialize result array
        M = np.zeros(Z.shape, dtype=float)

        # Iterate
        for i in range(self.max_iterations):
            # Calculate which points haven't diverged
            mask = np.abs(Z) <= 2

            # Update Z for non-diverged points
            Z[mask] = Z[mask]**2 + C

            # Smooth coloring
            newly_diverged = (np.abs(Z) > 2) & (M == 0)
            if np.any(newly_diverged):
                M[newly_diverged] = i + 1 - np.log2(np.log2(np.abs(Z[newly_diverged])))

        # Normalize to 0-1 range
        M[M == 0] = self.max_iterations
        M = M / self.max_iterations

        return M

    def apply_color_gradient(self, M):
        """Apply smooth color gradient to the fractal data"""
        height, width = M.shape
        image = np.zeros((height, width, 3), dtype=np.uint8)

        if self.color_scheme == "smooth":
            # Beautiful gradient: deep blue -> cyan -> yellow -> orange -> black
            for i in range(height):
                for j in range(width):
                    value = M[i, j]

                    if value >= 1.0:
                        # Set color
                        image[i, j] = [0, 0, 0]
                    else:
                        # Create smooth color transitions
                        # Use multiple color bands
                        t = value * 6  # 6 color bands

                        if t < 1:
                            # Dark blue to bright blue
                            r = int(0 * (1-t) + 0 * t)
                            g = int(7 * (1-t) + 100 * t)
                            b = int(100 * (1-t) + 255 * t)
                        elif t < 2:
                            t = t - 1
                            # Bright blue to cyan
                            r = int(0 * (1-t) + 0 * t)
                            g = int(100 * (1-t) + 255 * t)
                            b = int(255 * (1-t) + 255 * t)
                        elif t < 3:
                            t = t - 2
                            # Cyan to green
                            r = int(0 * (1-t) + 0 * t)
                            g = int(255 * (1-t) + 255 * t)
                            b = int(255 * (1-t) + 0 * t)
                        elif t < 4:
                            t = t - 3
                            # Green to yellow
                            r = int(0 * (1-t) + 255 * t)
                            g = int(255 * (1-t) + 255 * t)
                            b = int(0 * (1-t) + 0 * t)
                        elif t < 5:
                            t = t - 4
                            # Yellow to orange/red
                            r = int(255 * (1-t) + 255 * t)
                            g = int(255 * (1-t) + 69 * t)
                            b = int(0 * (1-t) + 0 * t)
                        else:
                            t = t - 5
                            # Orange to dark red
                            r = int(255 * (1-t) + 139 * t)
                            g = int(69 * (1-t) + 0 * t)
                            b = int(0 * (1-t) + 0 * t)

                        image[i, j] = [r, g, b]

        elif self.color_scheme == "classic":
            # Classic black and white with blue tint
            for i in range(height):
                for j in range(width):
                    value = M[i, j]
                    if value >= 1.0:
                        image[i, j] = [0, 0, 0]
                    else:
                        intensity = int(255 * (1 - value))
                        image[i, j] = [intensity // 3, intensity // 2, intensity]

        return image

    def render_fractal(self):
        """Render the fractal to an image"""
        width = self.width()
        height = self.height()

        if width <= 0 or height <= 0:
            return

        # Calculate fractal
        if self.fractal_type == "mandelbrot":
            M = self.calculate_mandelbrot(width, height)
        else:
            M = self.calculate_julia(width, height)

        # Apply color gradient
        image_data = self.apply_color_gradient(M)

        # Convert to QImage
        self.image = QImage(image_data.data, width, height,
                           width * 3, QImage.Format.Format_RGB888)
        self.update()

    def mousePressEvent(self, event):
        """Handle mouse clicks for zooming"""
        if event.button() == Qt.MouseButton.LeftButton:
            # Zoom in by factor of 2
            self.zoom_at_point(event.pos(), 2.0)
        elif event.button() == Qt.MouseButton.RightButton:
            # Zoom out by factor of 2
            self.zoom_at_point(event.pos(), 0.5)

    def zoom_at_point(self, point, zoom_factor):
        """Zoom in or out at a specific point"""
        # Convert pixel coordinates to complex plane coordinates
        width = self.width()
        height = self.height()
        aspect_ratio = width / height
        view_width = 3.5 / self.zoom
        view_height = view_width / aspect_ratio

        # Calculate the complex coordinate of the click
        x_frac = point.x() / width
        y_frac = point.y() / height

        x_min = self.center_x - view_width / 2
        y_min = self.center_y - view_height / 2

        click_x = x_min + x_frac * view_width
        click_y = y_min + y_frac * view_height

        # Update center to clicked point
        self.center_x = click_x
        self.center_y = click_y

        # Update zoom
        self.zoom *= zoom_factor

        # Notify zoom change (for slider update)
        if self.zoom_changed_callback:
            self.zoom_changed_callback(self.zoom)

        # Re-render
        self.render_fractal()

    def resizeEvent(self, event):
        """Handle widget resize"""
        self.render_fractal()

    def paintEvent(self, event):
        """Paint the fractal image"""
        if self.image:
            painter = QPainter(self)
            painter.drawImage(0, 0, self.image)


class FractalExplorer(QMainWindow):
    """Main window for the Fractal Explorer application"""

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Fractal Explorer")
        self.setGeometry(100, 100, 1200, 800)

        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # Create fractal canvas
        self.canvas = FractalCanvas()
        main_layout.addWidget(self.canvas, stretch=3)

        # Create control panel
        control_panel = self.create_control_panel()
        main_layout.addWidget(control_panel, stretch=1)

        # Set up zoom callback to sync slider with click-zoom
        self.canvas.zoom_changed_callback = self.update_zoom_slider

        # Initial render
        QTimer.singleShot(100, self.canvas.render_fractal)

    def create_control_panel(self):
        """Create the control panel with all controls"""
        panel = QWidget()
        layout = QVBoxLayout(panel)

        # Title
        title = QLabel("Fractal Explorer")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)

        # Fractal type selector
        type_group = QGroupBox("Fractal Type")
        type_layout = QVBoxLayout()

        self.type_combo = QComboBox()
        self.type_combo.addItems(["Mandelbrot Set", "Julia Set"])
        self.type_combo.currentTextChanged.connect(self.on_fractal_type_changed)
        type_layout.addWidget(self.type_combo)

        type_group.setLayout(type_layout)
        layout.addWidget(type_group)

        # Julia set parameters
        self.julia_group = QGroupBox("Julia Set Parameters")
        julia_layout = QVBoxLayout()

        # Real part
        julia_layout.addWidget(QLabel("C Real:"))
        self.julia_real_spin = QDoubleSpinBox()
        self.julia_real_spin.setRange(-2.0, 2.0)
        self.julia_real_spin.setSingleStep(0.01)
        self.julia_real_spin.setValue(-0.7)
        self.julia_real_spin.setDecimals(5)
        self.julia_real_spin.valueChanged.connect(self.on_julia_params_changed)
        julia_layout.addWidget(self.julia_real_spin)

        # Imaginary part
        julia_layout.addWidget(QLabel("C Imaginary:"))
        self.julia_imag_spin = QDoubleSpinBox()
        self.julia_imag_spin.setRange(-2.0, 2.0)
        self.julia_imag_spin.setSingleStep(0.01)
        self.julia_imag_spin.setValue(0.27015)
        self.julia_imag_spin.setDecimals(5)
        self.julia_imag_spin.valueChanged.connect(self.on_julia_params_changed)
        julia_layout.addWidget(self.julia_imag_spin)

        # Preset Julia sets
        julia_layout.addWidget(QLabel("Presets:"))
        preset_combo = QComboBox()
        preset_combo.addItems([
            "Dendrite (-0.7, 0.27015)",
            "Siegel Disk (-0.391, -0.587)",
            "Spiral (-0.4, 0.6)",
            "Douady Rabbit (-0.123, 0.745)",
            "Dragon (0.285, 0.01)"
        ])
        preset_combo.currentTextChanged.connect(self.on_preset_changed)
        julia_layout.addWidget(preset_combo)

        self.julia_group.setLayout(julia_layout)
        self.julia_group.setEnabled(False)
        layout.addWidget(self.julia_group)

        # Rendering parameters
        render_group = QGroupBox("Rendering")
        render_layout = QVBoxLayout()

        # Max iterations
        render_layout.addWidget(QLabel("Max Iterations:"))
        self.iter_slider = QSlider(Qt.Orientation.Horizontal)
        self.iter_slider.setMinimum(64)
        self.iter_slider.setMaximum(1024)
        self.iter_slider.setValue(256)
        self.iter_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.iter_slider.setTickInterval(128)
        self.iter_slider.valueChanged.connect(self.on_iterations_changed)
        render_layout.addWidget(self.iter_slider)

        self.iter_label = QLabel("256")
        render_layout.addWidget(self.iter_label)

        render_group.setLayout(render_layout)
        layout.addWidget(render_group)

        # View controls
        view_group = QGroupBox("View Controls")
        view_layout = QVBoxLayout()

        # Zoom slider
        view_layout.addWidget(QLabel("Zoom Level:"))
        self.zoom_slider = QSlider(Qt.Orientation.Horizontal)
        self.zoom_slider.setMinimum(0)
        self.zoom_slider.setMaximum(200)  # 0 to 20 in log2 scale
        self.zoom_slider.setValue(0)  # log2(1.0) = 0
        self.zoom_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.zoom_slider.setTickInterval(20)
        self.zoom_slider.valueChanged.connect(self.on_zoom_changed)
        view_layout.addWidget(self.zoom_slider)

        self.zoom_label = QLabel("1.0x")
        self.zoom_label.setStyleSheet("font-size: 10px;")
        view_layout.addWidget(self.zoom_label)

        reset_btn = QPushButton("Reset View")
        reset_btn.clicked.connect(lambda: self.on_reset_view())
        view_layout.addWidget(reset_btn)

        info_label = QLabel("Left-click: Zoom In\nRight-click: Zoom Out")
        info_label.setStyleSheet("font-size: 10px; color: gray;")
        view_layout.addWidget(info_label)

        view_group.setLayout(view_layout)
        layout.addWidget(view_group)

        # Instructions
        instructions = QLabel(
            "Explore the infinite beauty of fractals!\n\n"
            "Click on the fractal to zoom in and\n"
            "discover intricate patterns at every scale.\n\n"
            "Try different Julia set parameters\n"
            "for unique, mesmerizing patterns."
        )
        instructions.setWordWrap(True)
        instructions.setStyleSheet("font-size: 10px; color: gray; padding: 10px;")
        layout.addWidget(instructions)

        layout.addStretch()

        return panel

    def on_fractal_type_changed(self, text):
        """Handle fractal type change"""
        if text == "Mandelbrot Set":
            self.canvas.set_fractal_type("mandelbrot")
            self.julia_group.setEnabled(False)
        else:
            self.canvas.set_fractal_type("julia")
            self.julia_group.setEnabled(True)

    def on_julia_params_changed(self):
        """Handle Julia parameter changes"""
        c_real = self.julia_real_spin.value()
        c_imag = self.julia_imag_spin.value()
        self.canvas.set_julia_params(c_real, c_imag)

    def on_preset_changed(self, text):
        """Handle Julia preset selection"""
        presets = {
            "Dendrite (-0.7, 0.27015)": (-0.7, 0.27015),
            "Siegel Disk (-0.391, -0.587)": (-0.391, -0.587),
            "Spiral (-0.4, 0.6)": (-0.4, 0.6),
            "Douady Rabbit (-0.123, 0.745)": (-0.123, 0.745),
            "Dragon (0.285, 0.01)": (0.285, 0.01)
        }

        if text in presets:
            c_real, c_imag = presets[text]
            self.julia_real_spin.setValue(c_real)
            self.julia_imag_spin.setValue(c_imag)

    def on_iterations_changed(self, value):
        """Handle max iterations change"""
        self.iter_label.setText(str(value))
        self.canvas.set_max_iterations(value)

    def on_zoom_changed(self, value):
        """Handle zoom slider change"""
        # Convert slider value (0-200) to zoom using log2 scale
        # slider value 0 = zoom 1.0 (2^0)
        # slider value 10 = zoom 1.0 (2^1)
        # slider value 200 = zoom 1048576 (2^20)
        zoom = 2 ** (value / 10.0)
        self.canvas.zoom = zoom

        # Update label with formatted zoom level
        if zoom < 10:
            self.zoom_label.setText(f"{zoom:.2f}x")
        elif zoom < 1000:
            self.zoom_label.setText(f"{zoom:.1f}x")
        else:
            self.zoom_label.setText(f"{zoom:.0f}x")

        self.canvas.render_fractal()

    def on_reset_view(self):
        """Handle reset view button click"""
        self.canvas.reset_view()
        # Reset zoom slider to 0 (zoom level 1.0)
        self.zoom_slider.blockSignals(True)  # Prevent triggering on_zoom_changed
        self.zoom_slider.setValue(0)
        self.zoom_slider.blockSignals(False)
        self.zoom_label.setText("1.0x")

    def update_zoom_slider(self, zoom):
        """Update zoom slider when zoom changes via clicking"""
        # Convert zoom to slider value using log2 scale
        slider_value = int(math.log2(zoom) * 10)

        # Clamp to slider range
        slider_value = max(0, min(200, slider_value))

        # Update slider without triggering valueChanged signal
        self.zoom_slider.blockSignals(True)
        self.zoom_slider.setValue(slider_value)
        self.zoom_slider.blockSignals(False)

        # Update label
        if zoom < 10:
            self.zoom_label.setText(f"{zoom:.2f}x")
        elif zoom < 1000:
            self.zoom_label.setText(f"{zoom:.1f}x")
        else:
            self.zoom_label.setText(f"{zoom:.0f}x")


def main():
    """Main entry point"""
    app = QApplication(sys.argv)

    # Set application style
    app.setStyle('Fusion')

    window = FractalExplorer()
    window.show()

    sys.exit(app.exec())


if __name__ == '__main__':
    main()
