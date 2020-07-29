This project, which integrates GRASS GIS into the framework of a Python web application, was developed for the module 
GEO450 of the M.Sc. Geoinformatics at the Friedrich-Schiller-University Jena.

By providing a local directory with a time series of Radar satellite imagery in GeoTIFF format a Flask application will 
be deployed locally (in the web browser). This application can then be used to: 
   - Get a tabular overview of the entire dataset 
   - Get a tabular overview of extracted metadata for each individual file (incl. a simple visualization on a Leaflet map) 
   - Extract and visualize a time series plot for any given coordinate on an interactive Leaflet map (see Preview down below!) 
   - (Other features that utilize GRASS GIS in the backend might be added in the future)

---

### Setup / Requirements

- Install a stable version of [GRASS GIS (7.8.*)](https://grass.osgeo.org/download/)
- Download / Clone this repository
- Open `config.py` and update the variable `data_dir` with the location of locally stored Radar imagery in GeoTIFF format       
    - The filenaming scheme used by [pyroSAR](https://github.com/johntruckenbrodt/pyroSAR) is expected. A different naming 
    scheme will lead to some of the extracted metadata to not make sense or it will lead to an error during initialization 
    of the application. (For more information about pyroSAR's naming scheme see [here](https://pyrosar.readthedocs.io/en/latest/general/filenaming.html) or [here](https://www.researchgate.net/profile/John_Truckenbrodt/publication/334258406_PYROSAR_A_FRAMEWORK_FOR_LARGE-SCALE_SAR_SATELLITE_DATA_PROCESSING/links/5d1f4071a6fdcc2462c1ff1b/PYROSAR-A-FRAMEWORK-FOR-LARGE-SCALE-SAR-SATELLITE-DATA-PROCESSING.pdf))
    - The name of this project is a bit misleading... Radar sensors other than Sentinel-1 should work as well :)
- Open terminal and navigate to the repository ('Anaconda Prompt' is recommended on Windows to use Conda)
- Set up and activate a Conda environment:
    - `conda env create -f environment.yml`
    - `conda activate S1GRASS_env`
- Use `flask run` to start the local deployment
- Open the link suggested by Flask in your browser (should be `http://localhost:5000/` by default). This will trigger 
the initialization of the backend (SQLite & GRASS). Open the terminal again to see what's going on in the background. 
The application will be ready in the web browser once the backend finished doing its thing. 

---

### Preview

The raster file being visualized on this webpage is an average of all individual scenes that are located in the provided 
data directory at any given time and will always be updated if more scenes are being added (or removed). 
When any point on the map is clicked on, GRASS GIS is used to extract the backscatter value from each file for the given 
coordinate, which is then plotted using Bokeh.  

![S1GRASS Demo](demo/demo.gif)
