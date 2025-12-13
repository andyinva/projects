# Trailer Backup Guide

A PyQt6 application to help you practice and visualize backing up a truck with a travel trailer. The app provides real-time guidance and a simulation environment where you can practice maneuvering your specific truck and trailer configuration.

## Features

- **Custom Vehicle Configurations**: Enter the exact dimensions of your truck and trailer
  - Truck: length, width, wheelbase, hitch offset, number of rear wheels
  - Trailer: length, width, tongue length, number of axles, wheels per axle, axle spacing

- **Multiple Configuration Profiles**: Save different setups for different vehicles

- **Real-Time Visual Simulation**:
  - Top-down view showing truck outline, trailer outline, and wheel positions
  - Target parking space visualization
  - Grid reference for spatial awareness

- **Interactive Practice Mode**:
  - Use arrow keys to control the truck
  - ↑ : Move Forward
  - ↓ : Move Backward
  - ← : Steer Left
  - → : Steer Right

- **Backing Instructions**:
  - Real-time guidance on which way to steer
  - Clear reminders that steering right makes the trailer go left when backing
  - Distance and angle feedback to the target position

- **Realistic Physics**:
  - Simulates the actual behavior of a truck and trailer
  - Shows how steering affects both vehicles
  - Models the relationship between hitch point and trailer movement

## Installation

1. Make sure you have Python 3.8 or higher installed

2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Run the application:
```bash
python trailer_backup_guide.py
```

Or make it executable:
```bash
chmod +x trailer_backup_guide.py
./trailer_backup_guide.py
```

## Getting Started

1. **Create Your Configuration**:
   - Click "New" in the Configuration section
   - Enter your truck dimensions (measure or check manual)
   - Enter your trailer dimensions
   - Give it a descriptive name
   - Click OK to save

2. **Practice Backing**:
   - The green dashed outline shows your target parking space
   - Use arrow keys to control the truck
   - Watch the instruction panel for guidance
   - Remember: When backing, turn RIGHT to make the trailer go LEFT

3. **Tips for Success**:
   - Start with small steering inputs
   - Make corrections early rather than waiting for large angle differences
   - Keep an eye on both the truck and trailer positions
   - The wheels show you which direction the vehicle will move

## Understanding the Display

- **Blue vehicle**: Your truck with front wheels that turn
- **Brown vehicle**: Your trailer connected at the hitch (red dot)
- **Green dashed box**: Target parking space
- **Black rectangles**: Wheels (front wheels rotate with steering)
- **Grid**: Each square represents 10 feet

## Configuration Tips

For accurate simulation, measure:
- Truck length: From front bumper to back bumper
- Truck wheelbase: From center of front axle to center of rear axle
- Hitch offset: From rear axle to ball hitch
- Trailer tongue length: From hitch ball to front of trailer body
- Trailer length: Length of trailer body (not including tongue)

## Troubleshooting

**The vehicles don't move smoothly**:
- This is normal at low frame rates. The simulation updates 20 times per second.

**The trailer angle seems wrong**:
- Check that your tongue length and hitch offset measurements are accurate
- These measurements critically affect the turning behavior

**Configuration won't save**:
- Check that you have write permissions in your home directory
- Configurations are saved to: ~/.trailer_backup_configs.json

## How It Works

The app simulates the kinematics of a truck and trailer combination:

1. **Truck Movement**: Based on Ackermann steering geometry using the wheelbase
2. **Trailer Following**: The trailer pivots around the hitch point
3. **Angle Calculation**: Uses trigonometry to compute the trailer's angle change
4. **Visual Feedback**: Shows you exactly what's happening in real-time

The key insight: When backing, the trailer rotates opposite to your steering input because the hitch point becomes the pivot, and turning the truck rotates this pivot in the opposite direction relative to the trailer's path.

## License

Free to use for personal and educational purposes.
