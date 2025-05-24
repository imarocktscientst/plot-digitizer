# plot-digitizer

A Python application for extracting tabular data from plot images. This tool enables users to digitize data from images of graphs by tracing curves with NURBS curves and exporting the sampled data as CSV files.

## Features

- **Perspective Correction**: Automatically correct perspective distortion in photographed graphs
- **Axis Calibration**: Mark axis limits and specify scale types (linear or logarithmic)
- **NURBS Curve Tracing**: Manually trace curves using Non-Uniform Rational B-Spline curves
  - Add/remove knot points
  - Adjust knot tension
  - Control tangent direction and magnitude
- **Flexible Data Sampling**:
  - Uniform sampling by independent variable
  - Adaptive non-uniform sampling based on curvature
- **Data Export**:
  - CSV export in column or row format
  - Copy to clipboard
  - Statistical summary
- **Project Management**:
  - Save projects with source images and traced data
  - Reopen projects for further editing

## Requirements

- Python 3.6+
- PyQt5
- NumPy
- SciPy
- pandas
- OpenCV (cv2)

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/imarocktscientst/plot-digitizer.git
   cd plot-digitizer
   ```

2. Create a virtual environment (recommended):
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install PyQt5 numpy scipy pandas opencv-python
   ```

## Usage

### Running the Application

```
python main.py
```

### Workflow

1. **Load an Image**:
   - Select "File > Load Image" to load a plot image

2. **Perspective Correction** (if needed):
   - Go to the "Perspective" tab
   - Click "Mark Corners" and select the four corners of the plot area
   - Click "Apply Correction"

3. **Calibrate Axes**:
   - Go to the "Axes" tab
   - Set axis types (linear or logarithmic)
   - Click "Mark X-Axis Limits" and select the min and max points on the X-axis
   - Enter the actual min and max values for the X-axis
   - Repeat for the Y-axis

4. **Trace Curves**:
   - Go to the "Curves" tab
   - Click "Add" to create a new curve
   - Click "Edit Mode" to enter curve editing mode
   - Click on the image to add knot points along the curve
   - Adjust knot properties as needed
   - Disable "Edit Mode" when finished

5. **Export Data**:
   - Click "Export Data..." from the Curves tab or toolbar
   - Choose sampling method and parameters
   - Choose CSV format options
   - Click "Export to CSV..." to save the data

### Tips

- Zoom in/out using Ctrl+Mouse Wheel or the View menu
- Use "Mark Corners" to define the plot area, especially for photographed plots
- For logarithmic axes, mark the limits at decade points (e.g., 1, 10, 100)
- Adjust knot tension to control curve smoothness
- Use manual tangents for precise control at specific points
- Save your project frequently to avoid losing work

## Project File Format

Plot Digitizer uses `.pdp` files (Plot Digitizer Project) to store project data. These are actually directories containing:

- Project metadata in JSON format
- Source image file
- Transformed image (if perspective correction was applied)

## License

This project is licensed under the MIT License - see the LICENSE file for details.
