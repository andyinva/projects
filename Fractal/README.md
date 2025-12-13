# Fractal Explorer

An interactive fractal viewer built with PyQt6 that lets you explore the infinite beauty of Mandelbrot and Julia sets.

## Features

- **Smooth Color Gradients**: Beautiful, smooth color transitions based on iteration counts using advanced coloring algorithms
- **Click-to-Zoom**: Left-click to zoom in, right-click to zoom out - explore infinite fractal detail
- **Interactive Julia Sets**: Real-time parameter adjustment with preset patterns
- **Dual Fractal Modes**: Switch between Mandelbrot and Julia sets
- **Performance Optimized**: Uses NumPy for fast calculations

## Installation

```bash
pip install -r requirements.txt
```

## Usage

Run the program:
```bash
python3 fractal_explorer.py
```

### Controls

- **Left Mouse Click**: Zoom in at the clicked point
- **Right Mouse Click**: Zoom out
- **Fractal Type**: Switch between Mandelbrot and Julia sets
- **Julia Parameters**: Adjust C real and imaginary values in real-time
- **Presets**: Try beautiful pre-configured Julia set patterns:
  - Dendrite
  - Siegel Disk
  - Spiral
  - Douady Rabbit
  - Dragon
- **Max Iterations**: Adjust detail level (64-1024)
- **Reset View**: Return to the default view

## The Mathematics

### Mandelbrot Set
The Mandelbrot set is defined by iterating the formula:
```
z(n+1) = z(n)² + c
```
where z starts at 0 and c is the complex coordinate of each pixel.

### Julia Set
Julia sets use the same formula but with a fixed c value:
```
z(n+1) = z(n)² + c
```
where z starts at the pixel coordinate and c is a constant you can adjust.

### Smooth Coloring
Instead of simple iteration counting, this viewer uses smooth coloring with the formula:
```
smoothed = i + 1 - log2(log2(|z|))
```
This creates beautiful gradient transitions instead of distinct bands.

## Interesting Locations to Explore

### Mandelbrot Set
- Default view: The entire set
- Try zooming into the edge of the main bulb
- Explore the "seahorse valley" at approximately (-0.75, 0.1)
- Find mini-Mandelbrots along the edges

### Julia Set Presets
Each preset creates a completely different fractal structure - experiment with slight variations!

## Tips

- Higher iteration counts reveal more detail but render slower
- The patterns are truly infinite - you can keep zooming forever
- Small parameter changes in Julia sets can create dramatically different patterns
- The Mandelbrot set is a "map" of all Julia sets

## Technical Details

- Built with PyQt6 for the GUI
- NumPy for fast array calculations
- Smooth coloring algorithm for gradient rendering
- Logarithmic escape time calculation for accuracy

Enjoy exploring the infinite beauty of fractals!
