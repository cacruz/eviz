# Model-Specific Examples

This section demonstrates visualization of output from specific data sources supported by EViz.
These sources are identifified by using specially-named options, e.g. `lis`, `wrf`, and `crest`, for example.

## LIS Model

### NASA Land Information System
Process LIS (Land Information System) model output:

```bash
python autoviz.py -s lis -f $EVIZ_CONFIG_PATH/lis/lis.yaml
```

**What this does:**
- Handles LIS land surface model outputs
- Visualizes land surface variables and fluxes
- Supports multi-model ensemble comparisons

**LIS model characteristics:**
- NASA's high-resolution land surface modeling framework
- Variables: soil moisture, evapotranspiration, snow depth, etc
- Regional scale applications

## WRF Model

### Weather Research and Forecasting Model
Visualize WRF model output:

```bash
python autoviz.py -s wrf -f $EVIZ_CONFIG_PATH/wrf/wrf.yaml
```

**What this does:**
- Processes WRF atmospheric model output
- Creates meteorological visualizations
- Handles complex WRF coordinate systems and projections

**WRF model characteristics:**
- High-resolution numerical weather prediction
- Atmospheric chemistry and physics
- Nested domain capabilities
- Variables: temperature, precipitation, wind, chemical species

## Gridded Reanalysis/Forecast Data

### GRIB Format Data
Process meteorological GRIB files:

```bash
python autoviz.py -s grib $EVIZ_CONFIG_PATH/grib/grib.yaml
```

**What this does:**
- Processes ERA5 output in GRIB format
- Common for operational weather data

**Data characteristics:**
- Regular lat/lon grids
- Multiple pressure levels
- Standard meteorological variables

## CREST Framework

### Basic CREST Visualization
Visualize CREST (Coupled Reusable Earth System Tensor) framework output:

```bash
python autoviz.py -s crest $EVIZ_CONFIG_PATH/crest/crest.yaml
```

## Model-Specific Features

### Coordinate System Handling
EViz automatically handles model-specific coordinate systems:
- **CREST**: Geographic lat/lon coordinates
- **LIS**: Various projections, often Lambert Conformal Conic
- **WRF**: Staggered grids, map projections, terrain-following coordinates

### Variable Name Translation
EViz uses metadata mapping to translate between:
- Model-specific variable names
- Standard names for plotting
- Units conversion when needed

### Domain Information
EViz automatically detects:
- **Regional models**: CREST, LIS regional runs, WRF domains
- **Grid specifications**: Resolution, extent, projection
- **Temporal coverage**: Model run periods and output frequency

## Advanced Model Analysis

### Multi-Model Comparisons
Compare outputs from different models:
- Configure multiple data sources in YAML
- Use comparison plotting modes
- Generate side-by-side or difference plots

### Validation Studies
Combine model output with observations:
- Overlay model results with observational data
- Statistical comparison metrics
- Taylor diagrams and scatter plots

### Correlation Analysis
Analyze relationships between model variables:
- Spatial correlation patterns
- Temporal correlation analysis
- Multi-variable correlation matrices

## Configuration Best Practices

### Model-Specific Settings
- **File paths**: Use absolute paths or environment variables
- **Time selection**: Account for model output frequency
- **Spatial subsetting**: Define analysis regions appropriately
- **Variable selection**: Choose meaningful model outputs

### Performance Optimization
- **Chunking**: For large model files
- **Temporal averaging**: Reduce data volume when appropriate
- **Spatial subsampling**: For quick overview plots