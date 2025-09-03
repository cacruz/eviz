# Model-Specific Examples

This section demonstrates visualization of output from specific Earth System Models supported by EViz.

## CREST Model

### Basic CREST Visualization
Visualize CREST (Coupled Routing and Excess Storage) model output:

```bash
python autoviz.py -s crest $EVIZ_CONFIG_PATH/crest/crest_corr.yaml
```

**What this does:**
- Processes CREST hydrological model output
- Creates spatial maps of hydrological variables
- Supports correlation analysis between variables

**CREST model characteristics:**
- Distributed hydrological modeling system
- Outputs include soil moisture, runoff, streamflow
- High spatial resolution for watershed studies

### Alternative CREST Command
Alternative syntax for CREST data:

```bash
python autoviz.py -s config/crest/crest_corr.yaml
```

**Note:** This demonstrates EViz's flexible command syntax for model specification.

## LIS Model

### NASA Land Information System
Process LIS (Land Information System) model output:

```bash
python autoviz.py -s lis -f config/lis/lis.yaml
```

**What this does:**
- Handles LIS land surface model outputs
- Visualizes land surface variables and fluxes
- Supports multi-model ensemble comparisons

**LIS model characteristics:**
- NASA's high-resolution land surface modeling framework
- Variables: soil moisture, evapotranspiration, snow depth
- Global to regional scale applications

## WRF Model

### Weather Research and Forecasting Model
Visualize WRF model output:

```bash
python autoviz.py -s wrf -f config/wrf/wrf.yaml
```

**What this does:**
- Processes WRF atmospheric model output
- Creates meteorological visualizations
- Handles complex WRF coordinate systems and projections

**Expected output:**
![WRF Precipitation](https://github.com/cacruz/eviz-dev/releases/download/docs-images-v1.0/wrf_precipitation_map.png)

*Example showing WRF-simulated precipitation with terrain*

**WRF model characteristics:**
- High-resolution numerical weather prediction
- Atmospheric chemistry and physics
- Nested domain capabilities
- Variables: temperature, precipitation, wind, chemical species

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