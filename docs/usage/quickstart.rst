Quick Start
============

EViz is a comprehensive Python-based visualization library originally designed for Earth System Models 
developed at NASA. It processes various model-generated output formats and produces high-quality 
diagnostic plots for data analysis and validation.

Installation from source
------------------------

1. First you need to download and set up Anaconda or Miniconda on your computer.

Note that ``EViz`` has been tested with Python version >= 3.8

2. Get the source code:

   For read-only access (HTTPS):
   
   .. code-block::
      
      git clone https://github.com/cacruz/eviz.git
   
   For developers with SSH access:
   
   .. code-block::
      
      git clone git@github.com:cacruz/eviz.git

3. cd into the code repo: 

.. code-block::
   
   cd eviz 


4. Create the Python environment:

.. code-block::
   
   conda env create -f environment.yaml


Enter *y* when prompted. This will download all the required packages needed to run the ``EViz`` tools and install
them in a separate environment called *viz*. This may take a minute or two, so please be patient.

5. Once the installation has finished building, *activate* the installed environment by running:

.. code-block::
   
   conda activate viz

6. Install EViz in development mode:

.. code-block::
   
   pip install -e .

7. Verify the installation by running:

.. code-block::
   
   python -c "import eviz; print('EViz installation successful')"


Sample data
-----------

On NASA's DISCOVER supercomputing system (part of the NASA Center for Climate Simulation at Goddard Space Flight Center), 
we provide sample data representative of the data sources supported by the EViz tools. 
The data is located here:

.. code-block::

   /discover/nobackup/projects/jh_tutorials/eviz/sample_data

Therein you will find datasets collected from various data sources that are used to produce the visualizations
described in this guide.

You can also get the sample data from NASA's NCCS (NASA Center for Climate Simulation) data portal:

.. code-block::

    https://portal.nccs.nasa.gov/datashare/astg/eviz/sample_data/

Web-based plots
---------------

This is the code that we use to host visualization on a web platform. We encourage developers to try it out
and experiment with setting up your own web platform.

To share your visualizations on a website, ``EViz`` offers a tool to generate plots accessible via a web browser.
This functionality utilizes the streamlit package, which should already be included in the ``viz`` environment.

To use the web interface, from the EViz project root directory run:

.. code-block::

    streamlit run sviz/sviz.py

This command will launch a web-based interface to run EViz and display the static plots on your local host.

Supported Data Sources
----------------------

EViz supports various data formats and access methods:

**File Formats:**
- NetCDF files (most common Earth system model output)
- GRIB files (meteorological data)
- HDF files 
- Zarr files
- CSV files

**Access Methods:**
- Local files on your system
- Remote files via OPeNDAP URLs

**Data Source Detection:**
EViz identifies data sources by file extension. If a file has no extension, EViz assumes it's a NetCDF4 file.

Basic Usage Example
-------------------

Once installation is complete, you can create your first visualization:

.. code-block::

    # Basic command-line usage
    python autoviz.py -s gridded -c config/
    
    # Process a specific file with variables
    python autoviz.py --file data.nc --vars temp,precip

For additional information please look at the streamlit documentation (https://streamlit.io/).
