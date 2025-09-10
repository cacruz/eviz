# Observational Data Examples

This section shows how to visualize various observational datasets using EViz.
These sources are identifified by using the `-s obs` option.

## Air Quality Data

### AirNow Ground Observations
Visualize EPA AirNow air quality monitoring data:

```bash
python autoviz.py -s obs $EVIZ_CONFIG_PATH/obs/airnow.yaml
```

**What this does:**
- Plots ground-based air quality measurements
- Creates station maps with color-coded measurements
- Useful for air quality assessment and validation
- Note data is in CSV format

**Expected output:**
![AirNow Stations](https://github.com/cacruz/eviz-dev/releases/download/docs-images-v0.9/airnow_stations_map.png)

*Example showing PM2.5 measurements at monitoring station over CONUS*

**Data characteristics:**
- Point measurements at monitoring stations
- Multiple pollutants (PM2.5, O3, NO2, etc.)
- Hourly temporal resolution

## Satellite Data

### OMI Satellite Data
Process Ozone Monitoring Instrument data:

```bash
python autoviz.py -s obs $EVIZ_CONFIG_PATH/obs/omi.yaml
```

**What this does:**
- Visualizes satellite-based atmospheric measurements
- Creates maps of column-integrated quantities
- Excellent for large-scale pollution monitoring

**Data characteristics:**
- Global coverage with daily revisit
- Column measurements (e.g., tropospheric NO2, SO2)
- Pixel-based spatial structure

## Configuration Notes

### Data Format Considerations
- **Point data** (AirNow): Requires station locations and interpolation settings
- **Swath data** (OMI): May need regridding for regular visualization
- **Gridded data** (GRIB): Direct plotting with minimal preprocessing

### Common Configuration Options
- **Spatial extent**: Define regions of interest
- **Time selection**: Choose specific dates/times
- **Variable selection**: Pick which measurements to plot
- **Quality control**: Apply data filtering criteria
- **Interpolation**: Settings for sparse observational data

### Output Formats
All observational data examples can generate:
- **Static images**: PNG files for publications
- **Animated sequences**: GIF files for temporal evolution
- **Interactive plots**: When using hvplot backend