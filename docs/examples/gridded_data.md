# Gridded Data Examples

This section demonstrates how to visualize `gridded` scientific data source using EViz's autoviz command-line interface.
These sources are identifified by using the `-s gridded` option.

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
![Basic XY Plot](https://github.com/cacruz/eviz-dev/releases/download/docs-images-v0.9.1/xy_plot_basic_temperature.png)

*Example showing temperature distribution across a spatial domain*

### Vertical Sum Aggregation
Sum all vertical levels into a single 2D map:

```bash
python autoviz.py -s gridded -f $EVIZ_CONFIG_PATH/gridded/xy_zsum.yaml
```

**What this does:**
- Aggregates data across all vertical levels using summation
- Automatically converts units from mol/mol to DU
- Useful for column-integrated quantities (e.g., total precipitable water)

**Expected output:**
![Basic XY Plot (Column Sum)](https://github.com/cacruz/eviz-dev/releases/download/docs-images-v0.9.1/xy_plot_vertical_sum.png)

*Example showing column-integrated Ozone field**

### Vertical Average
Average across vertical levels:

```bash
python autoviz.py -s gridded -f $EVIZ_CONFIG_PATH/gridded/xy_zave.yaml
```

**What this does:**
- Computes the mean across vertical levels
- Good for getting representative values at different altitudes


**Expected output:**
![Basic XY Plot (Column Average)](https://github.com/cacruz/eviz-dev/releases/download/docs-images-v0.9.1/xy_plot_vertical_avg.png)

*Example showing column-mean Ozone field**


### Specific Vertical Levels
Plot only certain vertical levels:

```bash
python autoviz.py -s gridded -f $EVIZ_CONFIG_PATH/gridded/xy_zlevs.yaml
```

**What this does:**
- Extracts and plots specific pressure/height levels
- Configure levels in the YAML file

**Expected output:**
![Basic XY Plot (at Specified Level)](https://github.com/cacruz/eviz-dev/releases/download/docs-images-v0.9.1/xy_plot_vertical_levs.png)

*Example showing Ozone distribution at a specific vertical level*

### Custom Projection
Apply map projection transformations:

```bash
python autoviz.py -s gridded -f $EVIZ_CONFIG_PATH/gridded/xy_proj.yaml
```

**What this does:**
- Reprojects data to different coordinate systems
- Useful for regional studies or specific map projections

**Expected output:**
![Projected Map](https://github.com/cacruz/eviz-dev/releases/download/docs-images-v0.9.1/xy_plot_robinson_projection.png)

*Example showing global temperature map with Robinson projection*

### Regional Focus with Projection
Combine projection with geographic extent:

```bash
python autoviz.py -s gridded -f $EVIZ_CONFIG_PATH/gridded/xy_extent-proj.yaml
```

**What this does:**
- Applies both projection and geographic subsetting
- Focus on specific regions (CONUS) with appropriate projection

**Expected output:**
![Projected Map over CONUS](https://github.com/cacruz/eviz-dev/releases/download/docs-images-v0.9.1/xy_plot_conus_lambert_projection.png)

*Example showing temperature distribution in the CONUS with Lambert Conformal projection*


## Time Series (xt plots)

### Basic Time Series
Extract time series from data:

```bash
python autoviz.py -s gridded -f $EVIZ_CONFIG_PATH/gridded/xt.yaml
```

**What this does:**
- Creates basic time series plots averaged over all locations
- Useful for temporal analysis 

**Expected output:**
![Time Series Plot](https://github.com/cacruz/eviz-dev/releases/download/docs-images-v0.9.1/temperature_timeseries_basic.png)

*Example showing a basic temperature time series*

### Point Selection Time Series
Time series with point selection:

```bash
python autoviz.py -s gridded -f $EVIZ_CONFIG_PATH/gridded/xt_point_sel.yaml
```

**What this does:**
- Allows selection of multiple points - maybe useful for comparison
- Adds a custom title (set in SPECS file)
- Good for multi-site analysis

**Expected output:**
![Time Series Plot](https://github.com/cacruz/eviz-dev/releases/download/docs-images-v0.9.1/temperature_timeseries_at_nyc.png)

*Example showing a basic temperature time serie at a selected point (NYC)*


### Unit Conversion
Convert temperature units (Kelvin to Celsius):

```bash
python autoviz.py -s gridded -f $EVIZ_CONFIG_PATH/gridded/xt_KtoC.yaml
```

**What this does:**
- Automatically converts K to °C
- Demonstrates EViz's unit conversion capabilities

**Expected output:**
![Time Series Plot](https://github.com/cacruz/eviz-dev/releases/download/docs-images-v0.9.1/temperature_timeseries_at_nyc_inC.png)

*Same as before but different units for temperature*

### Trend Analysis
Add trend lines to time series:

```bash
python autoviz.py -s gridded -f $EVIZ_CONFIG_PATH/gridded/xt_trendline.yaml
```

**What this does:**
- Fits and displays linear trends

**Expected output:**
![Time Series Plot](https://github.com/cacruz/eviz-dev/releases/download/docs-images-v0.9.1/temperature_timeseries_trendline.png)

*Example showing a basic temperature time series with a trendline*

### Time Series Plot with Rolling Window
Smoothing a time series:

```bash
python autoviz.py -s gridded -f $EVIZ_CONFIG_PATH/gridded/xt_rolling_window.yaml
```

**What this does:**
- Fits and displays timeseries with a rolling window of size 12

**Expected output:**
![Time Series Plot](https://github.com/cacruz/eviz-dev/releases/download/docs-images-v0.9.1/temperature_timeseries_rolling_window.png)

*Example showing a basic temperature time series with a rolling window of size 12*


## Vertical Profiles (yz plots)

### Zonal Mean
Average a 3D field over longitude 

```bash
python autoviz.py -s gridded -f $EVIZ_CONFIG_PATH/gridded/yz.yaml
```

**What this does:**
- Plots zonal mean of a 3D field
- Uses default projection and styling

**Expected output:**
![Zonal Mean](https://github.com/cacruz/eviz-dev/releases/download/docs-images-v0.9.1/temperature_zonal_mean.png)

*Example showing atmospheric temperature zonal mean*


### Vertical Profile
Create altitude/pressure vs. variable plots:

```bash
python autoviz.py -s gridded -f $EVIZ_CONFIG_PATH/gridded/yz_profile.yaml
```

**What this does:**
- Plots vertical distribution of a 3D variable
- Useful for atmospheric/oceanic profile analysis

**Expected output:**
![Vertical Profile](https://github.com/cacruz/eviz-dev/releases/download/docs-images-v0.9.1/temperature_profile.png)

*Example showing atmospheric temperature vertical profile*

## Configuration Tips

- **YAML files** control plot appearance, data processing, and output options
- **Modify configuration files** to customize colors, titles, units, and processing
- **Check config templates** in `$EVIZ_CONFIG_PATH/gridded/` for examples
- **Use absolute paths** in configuration files for reliable data access