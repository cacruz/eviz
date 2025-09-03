# Gridded Data Examples

This section demonstrates how to visualize gridded scientific data using EViz's autoviz command-line interface.

## 2D Spatial Maps (xy plots)

### Basic Spatial Plot
Create a simple 2D map of your gridded data:

```bash
python autoviz.py -s gridded -f $EVIZ_CONFIG_PATH/gridded/xy.yaml
```

**What this does:**
- Plots data as a 2D spatial map 
- Uses default projection and styling
- Generates images for all time steps in the dataset

**Expected output:**
![Basic XY Plot](https://github.com/cacruz/eviz-dev/releases/download/docs-images-v1.0/xy_plot_basic_temperature.png)

*Example showing temperature distribution across a spatial domain*

### Vertical Sum Aggregation
Sum all vertical levels into a single 2D map:

```bash
python autoviz.py -s gridded -f $EVIZ_CONFIG_PATH/gridded/xy_zsum.yaml
```

**What this does:**
- Aggregates data across all vertical levels using summation
- Useful for column-integrated quantities (e.g., total precipitable water)

### Vertical Average
Average across vertical levels:

```bash
python autoviz.py -s gridded -f $EVIZ_CONFIG_PATH/gridded/xy_zave.yaml
```

**What this does:**
- Computes the mean across vertical levels
- Good for getting representative values at different altitudes

### Specific Vertical Levels
Plot only certain vertical levels:

```bash
python autoviz.py -s gridded -f $EVIZ_CONFIG_PATH/gridded/xy_zlevs.yaml
```

**What this does:**
- Extracts and plots specific pressure/height levels
- Configure levels in the YAML file

### Custom Projection
Apply map projection transformations:

```bash
python autoviz.py -s gridded -f $EVIZ_CONFIG_PATH/gridded/xy_proj.yaml
```

**What this does:**
- Reprojects data to different coordinate systems
- Useful for regional studies or specific map projections

**Expected output:**
![Projected Map](https://github.com/cacruz/eviz-dev/releases/download/docs-images-v1.0/xy_plot_projection_lambert.png)

*Example showing data reprojected to Lambert Conformal Conic*

### Regional Focus with Projection
Combine projection with geographic extent:

```bash
python autoviz.py -s gridded -f $EVIZ_CONFIG_PATH/gridded/xy_extent-proj.yaml
```

**What this does:**
- Applies both projection and geographic subsetting
- Focus on specific regions with appropriate projection

## Time Series (xt plots)

### Basic Time Series
Extract time series at specific points:

```bash
python autoviz.py -s gridded -f $EVIZ_CONFIG_PATH/gridded/xt.yaml
```

**What this does:**
- Creates time series plots at specified locations
- Useful for temporal analysis at key sites

**Expected output:**
![Time Series Plot](https://github.com/cacruz/eviz-dev/releases/download/docs-images-v1.0/xt_timeseries_basic.png)

*Example showing temperature time series at selected grid points*

### Point Selection Time Series
Time series with interactive point selection:

```bash
python autoviz.py -s gridded -f $EVIZ_CONFIG_PATH/gridded/xt_point_sel.yaml
```

**What this does:**
- Allows selection of multiple points for comparison
- Good for multi-site analysis

### Unit Conversion
Convert temperature units (Kelvin to Celsius):

```bash
python autoviz.py -s gridded -f $EVIZ_CONFIG_PATH/gridded/xt_KtoC.yaml
```

**What this does:**
- Automatically converts K to °C
- Demonstrates EViz's unit conversion capabilities

### Trend Analysis
Add trend lines to time series:

```bash
python autoviz.py -s gridded -f $EVIZ_CONFIG_PATH/gridded/xt_trendline.yaml
```

**What this does:**
- Fits and displays linear trends
- Includes trend statistics in the plot

## Vertical Profiles (yz plots)

### Basic Vertical Profile
Create altitude/pressure vs. variable plots:

```bash
python autoviz.py -s gridded -f $EVIZ_CONFIG_PATH/gridded/yz.yaml
```

**What this does:**
- Plots vertical distribution of variables
- Useful for atmospheric/oceanic profile analysis

**Expected output:**
![Vertical Profile](https://github.com/cacruz/eviz-dev/releases/download/docs-images-v1.0/yz_profile_atmosphere.png)

*Example showing atmospheric temperature profile*

### Time-Averaged Profile
Average profiles over time:

```bash
python autoviz.py -s gridded -f $EVIZ_CONFIG_PATH/gridded/yz_tave.yaml
```

**What this does:**
- Computes mean vertical profiles
- Reduces temporal variability to show average structure

### Vertical Profile Analysis
Detailed vertical structure analysis:

```bash
python autoviz.py -s gridded -f $EVIZ_CONFIG_PATH/gridded/yz_profile.yaml
```

**What this does:**
- Enhanced vertical profiling with additional analysis
- May include gradient calculations or layer identification

## Configuration Tips

- **YAML files** control plot appearance, data processing, and output options
- **Modify configuration files** to customize colors, titles, units, and processing
- **Check config templates** in `$EVIZ_CONFIG_PATH/gridded/` for examples
- **Use absolute paths** in configuration files for reliable data access