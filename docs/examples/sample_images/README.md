# Sample Images for Documentation

This directory is for temporary storage of example images before uploading to GitHub Releases.

## Directory Structure
- `gridded/` - XY, XT, YZ plot examples
- `observational/` - AirNow, OMI, GRIB examples  
- `model_specific/` - CREST, LIS, WRF examples

## Upload Process
1. Generate example plots using EViz
2. Save images with descriptive names in appropriate subdirectories
3. Upload to GitHub Release as described in upload_instructions.md
4. Update documentation files with CDN links
5. Delete local images (they'll be served from GitHub)

## Naming Convention
Use descriptive names like:
- `xy_plot_basic_temperature.png`
- `xt_timeseries_point_selection.png`
- `wrf_precipitation_map.png`