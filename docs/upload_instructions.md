# GitHub Releases Image Upload Instructions

## Overview
This guide explains how to upload example images to GitHub Releases and use them in documentation.

## Step-by-Step Process

### 1. Generate Example Images
Run your EViz commands to generate example plots:

```bash
# Examples - run these to generate images
python autoviz.py -s gridded -f $EVIZ_CONFIG_PATH/gridded/xy.yaml
python autoviz.py -s gridded -f $EVIZ_CONFIG_PATH/gridded/xt.yaml
python autoviz.py -s wrf -f config/wrf/wrf.yaml
# etc.
```

Save the generated images to `docs/examples/sample_images/` with descriptive names.

### 2. Create a GitHub Release

**Option A: Via GitHub Web Interface**
1. Go to your repository: https://github.com/cacruz/eviz-dev
2. Click "Releases" → "Create a new release"
3. Tag version: `docs-images-v1.0` (or similar)
4. Release title: "Documentation Images v1.0"
5. Description: "Sample output images for EViz documentation examples"

**Option B: Via GitHub CLI** (if you have `gh` installed)
```bash
gh release create docs-images-v1.0 \
  --title "Documentation Images v1.0" \
  --notes "Sample output images for EViz documentation examples"
```

### 3. Upload Images to Release

**Via GitHub Web Interface:**
1. In the release creation/editing page
2. Drag and drop images from `docs/examples/sample_images/`
3. Or click "Attach binaries" and select files

**Via GitHub CLI:**
```bash
# Upload all images at once
gh release upload docs-images-v1.0 docs/examples/sample_images/**/*.png
gh release upload docs-images-v1.0 docs/examples/sample_images/**/*.jpg
gh release upload docs-images-v1.0 docs/examples/sample_images/**/*.gif
```

### 4. Get CDN URLs
After upload, each image gets a CDN URL in this format:
```
https://github.com/cacruz/eviz-dev/releases/download/docs-images-v1.0/filename.png
```

### 5. Update Documentation
Replace image references in your `.md` files:

```markdown
![XY Plot Example](https://github.com/cacruz/eviz-dev/releases/download/docs-images-v1.0/xy_plot_basic_temperature.png)
```

### 6. Clean Up Local Files
After confirming images work in documentation:
```bash
rm -rf docs/examples/sample_images/*.png
rm -rf docs/examples/sample_images/*.jpg  
rm -rf docs/examples/sample_images/*.gif
```

## URL Structure Examples

For release tag `docs-images-v1.0` and file `xy_plot_basic.png`:
```
https://github.com/cacruz/eviz-dev/releases/download/docs-images-v1.0/xy_plot_basic.png
```

## Tips

### Naming Convention
Use descriptive, unique names:
- `xy_plot_basic_temperature.png`
- `xt_timeseries_point_selection.png`
- `yz_profile_atmosphere.png`
- `wrf_precipitation_map.png`
- `airnow_stations_map.png`

### Image Optimization
Before upload, consider optimizing images:
```bash
# Install optimization tools
brew install imageoptim-cli  # macOS
# or
sudo apt install optipng    # Linux

# Optimize PNGs
optipng -o7 *.png

# Or use online tools like tinypng.com
```

### Version Management
- Use semantic versioning for releases: `docs-images-v1.0`, `docs-images-v1.1`
- Update all documentation URLs when creating new releases
- Keep old releases for backwards compatibility

### GitHub Bandwidth
- GitHub provides unlimited bandwidth for public repos
- Images are served via CDN (fast worldwide)
- No storage limits for release assets