# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added

### Deprecated

### Fixed

- `CITATION.cff` and `README.rst` updated with the DOI minted for v0.9.6
  (`10.5281/zenodo.22063198`, concept DOI `10.5281/zenodo.22063197`), resolving the
  Known Issue noted in the [0.9.6] release: the GitHub → Zenodo webhook fired
  correctly on that release and produced a properly-versioned archive.

### Removed

### Known Issues

---

## [0.9.6] - 2026-08-22

[Compare changes](https://github.com/cacruz/eviz/compare/v0.9.5...v0.9.6)

### Summary

Housekeeping release ahead of restarting active development: fixes stale/incorrect
metadata across the project's public release files and establishes proper Zenodo
archival via GitHub's release integration.

### Added

- ORCID iD for Carlos Cruz in `CITATION.cff`.
- `pyproject.toml` dependencies now include `holoviews`, `hvplot`, `seaborn`,
  `datashader`, `requests`, `Pillow`, and `python-dateutil`, which `eviz/lib` imports
  directly but which were previously undeclared, so `pip install -e .` now yields a
  working install on its own.

### Fixed

- `LICENSE`: removed leftover template brackets and extended the copyright year range.
- `CITATION.cff`: version/date were stale (pointed at 0.9.4); now tracks the current
  release. Stale `doi:` field removed pending a correctly-versioned Zenodo record (see
  Known Issues).
- `CONTRIBUTING.rst`: development setup instructions cloned `eviz` but `cd`'d into
  `eviz-dev`.
- `CHANGELOG.md`: added the missing `[0.9.5]` compare link.

### Removed

- `xesmf`, `pyhdf`, `pydap`, and `networkx` dropped from `environment.yaml` and
  `pyproject.toml`: none are imported anywhere in `eviz/` (regridding uses
  `scipy.interpolate`; OpenDAP access uses xarray's `netcdf4` engine; HDF4 sources are
  routed through the generic h5py-based reader). Documented as reserved-for-future in
  a comment rather than silently dropped.

### Known Issues

* Incomplete functionality in **hvplot** backend
* **Units module** requires more comprehensive testing
* **Tropopause height overlay** not working (fix in progress)
* **GRIB class** not fully tested; may not behave as expected
* **Style sheets** need further refinement
* Prior Zenodo DOIs (`10.5281/zenodo.7098329` and `10.5281/zenodo.20417921`) were
  created manually, outside GitHub's release integration, and are not properly
  versioned. This release is intended to be the first one archived automatically via
  the GitHub → Zenodo webhook; the resulting concept DOI should replace both in
  future citations.

---

## [0.9.5] - 2026-05-28

[Compare changes](https://github.com/cacruz/eviz/compare/v0.9.4...v0.9.5)

### Summary

Adds an extensible extra coordinate slot system for non-standard NetCDF
dimensions (e.g., `bnds=2` in satellite-derived files, such as FLDAS). This enables the coordinate detection step to recognize auxiliary dimensions beyond the standard xc/yc/zc/tc set.

### Added

- `extra:` section in `config/meta_coordinates.yaml` with two initial slots:
  `bc` (bands: `bnds`, `band`, `bands`) and `bounds` (cell boundaries:
  `bnds`, `bounds`, `nv`, `nbnd`). New model entries follow the existing
  YAML pattern with no code changes required.
- Dotted-path query support in `_get_model_dim_name()` across
  `base.py`, `processor.py`, and `config_manager.py`
  (e.g., `_get_model_dim_name("extra.bc", dims)`).
- `_get_extra_dim_names(available_dims)` helper on `DataSource` returns
  all matched extra dims as a `dict[slot, dim_name | None]` in one call.
- `_resolve_coord_value()` helper extracted on `DataSource` to consolidate
  the str/list/dict coord resolution logic.
- 47 new unit tests across the three modified modules.

### Deprecated

### Fixed

### Removed
- Tutorial documentation
  
### Known Issues
* Incomplete functionality in **hvplot** backend
* **Units module** requires more comprehensive testing
* **Tropopause height overlay** not working (fix in progress)
* **GRIB class** not fully tested; may not behave as expected
* **Style sheets** need further refinement

---

## [0.9.4] - 2026-02-24

[Compare changes](https://github.com/cacruz/eviz/compare/v0.9.3...v0.9.4)

### Summary

This minor release removes a backend functionality that is no longer supported

### Added

### Deprecated

### Fixed

### Removed

- Altair backend: eviz/lib/autoviz/plotting/backends/altair/ 
- Updated 
  - eviz/lib/autoviz/plotting/factory.py 
  - eviz/lib/autoviz/utils.py 
  - Documentation

### Known Issues

* Incomplete functionality in **hvplot** backend
* **Units module** requires more comprehensive testing
* **Tropopause height overlay** not working (fix in progress)
* **GRIB class** not fully tested; may not behave as expected
* **Style sheets** need further refinement


---

## [0.9.3] - 2025-11-07

[Compare changes](https://github.com/cacruz/eviz/compare/v0.9.2...v0.9.3)

### Summary

This minor release resolves numerous plotting issues that have accumulated over time.

### Added

Tests:

* lib/autoviz/backends/matplotlib/test_metric_plot.py
* lib/autoviz/backends/matplotlib/test_xy_plot.py
* lib/autoviz/plotting/test_plot_manager.py

### Deprecated

### Fixed
* Add RMSE calculation enhancement
* Fix hvplot backend tuple unpacking
* Fix correlation plot processing
* Fix time-level display to show datetime
* Make Cartopy-controlled features configurable
* Fix box plot DateTime error
* Remove unnecessary statistics computation from ZARR's data source method
* Allow for different time_lev formats
* Fix issue when selecting conus extent
* Manage clevs more consistently
* Crest error messages for supported plot types
* Fix support for comparing fields with different names.
* Fix filename creation issue
* Add descriptive filenames
* Add new tests

### Removed

### Known Issues

* Incomplete functionality in **hvplot/Altair** backends (`yzplot`)
* **Units module** requires more comprehensive testing
* **Tropopause height overlay** not working (fix in progress)
* **GRIB class** not fully tested; may not behave as expected
* **Style sheets** need further refinement

---

## [0.9.2] - 2025-10-15

[Compare changes](https://github.com/cacruz/eviz/compare/v0.9.1...v0.9.2)

### Summary

This release introduces categorical and tabular plotting capabilities, JSON data file support, and major documentation and formatting improvements.

### Added

* Support for **categorical/tabular dataset plotting**, including:

  * Histogram plots
  * Line plots
  * Bar plots
  * Pie charts
  * Scatter plots
  * Box plots
  * *Note: These are currently available only in the Matplotlib backend.*
* **JSON data file support** with automatic nested dictionary normalization:

  * Data transformed to Pandas DataFrames using `pd.read_json(..., lines=True)`
  * Nested dictionaries automatically flattened (e.g., `{deltas: {time: 0.27}}` → `deltas_time`)
* Example configurations for categorical datasets under `config/examples/categorical/`
* Comprehensive unit tests for categorical plotting and JSON reading

### Changed

* Reformatted all code to conform to **PEP 8** standards
* Updated documentation for consistency and clarity
* Converted all docstrings to **NumPy-style** for uniformity
* Unified `scatter_plot.py` to support both categorical and gridded data
* Unified `box_plot.py` to support both categorical and gridded data

### Fixed

* Indentation errors introduced by the automated docstring conversion script

### Known Issues

* Incomplete functionality in **hvplot/Altair** backends (`yzplot`)
* **Units module** requires more comprehensive testing
* **Tropopause height overlay** not working (fix in progress)
* **GRIB class** not fully tested; may not behave as expected
* **Style sheets** need further refinement

---

## [0.9.1] - 2025-09-10

[Compare changes](https://github.com/cacruz/eviz/compare/v0.9.0...v0.9.1)

### Summary

This release refactors configuration modules, introduces new visualization style sheets, and enhances performance for high-resolution datasets.

### Added

* Style sheets for multiple configurations (`eviz/lib/styles`):

  * Options: `default` (Matplotlib defaults), `publication`, `darkmode`, and `transparent`
  * Set via the `style` option under the `visualization` subsection in config files
* Caching of airmass files used in certain unit conversions
* Added `yzplot` functionality to **hvplot** and **Altair** backends
* Implemented a data-coarsening algorithm for high-resolution data in Matplotlib plots

  * *Significantly improves plotting performance for very large datasets*
* Updated documentation, especially the usage section

### Changed

* Refactored configuration modules:

  * Removed reliance on private attributes
  * Added `visualization` subsection under `output` configuration
  * Set the `backend` option in this new subsection (see sample specs)
* Updated all configuration files and removed hardwired paths

### Fixed

* Corrected unit conversions:

  * Mixing ratio ↔ Dobson Units (DU)
  * Mixing ratio ↔ Parts per Billion (PPB)
* Fixed minor correlation plot issues
* Fixed simple plot logic errors

### Removed

* Removed legacy module `eviz/lib/autoviz/plotter.py`

### Known Issues

* Issues remain in **hvplot/Altair** backends (`yzplot` functionality)
* **Units module** requires additional testing
* **Tropopause height overlay** not working (fix in progress)
* **GRIB class** not fully tested and may not function correctly
* **Style sheets** need additional refinement

---

## [0.9.0] - 2025-06-30

[Compare changes](https://github.com/cacruz/eviz/compare/v0.6.3...v0.9.0)

### Summary

This version represents a significant rewrite of v0.6.3, introducing a new modular architecture, an extensible backend system, and broader CREST integration.

### Added

* **New modular directory structure:**

  * Separated core code into `autoviz`, `config`, and `data` modules
  * Defined data sources, factories, and pipeline-based workflow under `data` module
* **Configuration improvements:**

  * Split `config.py` into smaller, maintainable components
  * Added a configuration adapter bridging the config system with the processing pipeline
* **Backend system** with `plot_backend` option in YAML files:

  * Supported backends: `matplotlib` (default), `hvplot`, and `altair`
* **CREST framework support**, including:

  * Box plots and correlation maps
  * *Note: CREST is an AI-enabled Earth System Modeling framework.*
* **GRIB data source class** with meta-coordinate support
* **Side-by-side comparison plots** for 2D and line plots
* **Matplotlib rcParams** configurable via YAML specs
* Automatic **OpenDAP** data access when URLs are provided
* Expanded documentation and tutorials

### Changed

* Increased unit test coverage (~25% → ~37%)
* Improved `metadump.py` and added more tests
* Enhanced coordinate standardization and validation

### Fixed

* Numerous issues resolved through architectural redesign
* Fixed `regrid()` function and associated interpolation issues
* Corrected various plotting and rendering problems

### Removed

* **iViz** application code (interactivity now optional within eViz)
* Renamed **generic data source** to `gridded` to clarify purpose
* Removed `const.py` class-based constants; replaced with dedicated modules for constants and environment-dependent paths

### Known Issues

* **hvplot/Altair** backends not fully supported for all plot types
* Distorted colorbars for side-by-side plots with individual colorbars
* Figure aesthetics may require manual tuning in some specs
* **Units module** not fully tested; some conversions may fail
* **Tropopause height overlay** not working (fix in progress)
* **GRIB class** not fully verified

---

*(Earlier releases omitted for brevity — all preserved below.)*

---

## [0.6.3] - 2024-12-23

## [0.6.2] - 2024-09-30

## [0.6.1] - 2024-09-04

## [0.6.0] - 2024-08-05

## [0.5.0] - 2024-01-30

## [0.4.0] - 2023-06-16

## [0.3.0] - 2023-05-31

## [0.2.2] - 2023-02-23

## [0.2.1] - 2023-02-21

## [0.2.0] - 2023-01-25

## [0.1.0] - 2022-07-06

---

### Note

Releases **0.1.0 through 0.6.3** were maintained in a private repository prior to the public release.

---

### Version Links

[0.9.6]: https://github.com/cacruz/eviz/compare/v0.9.5...v0.9.6
[0.9.5]: https://github.com/cacruz/eviz/compare/v0.9.4...v0.9.5
[0.9.4]: https://github.com/cacruz/eviz/compare/v0.9.3...v0.9.4
[0.9.3]: https://github.com/cacruz/eviz/compare/v0.9.2...v0.9.3
[0.9.2]: https://github.com/cacruz/eviz/compare/v0.9.1...v0.9.2
[0.9.1]: https://github.com/cacruz/eviz/compare/v0.9.0...v0.9.1
[0.9.0]: https://github.com/cacruz/eviz/compare/v0.6.3...v0.9.0

