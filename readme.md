# Instructions for running subsidence scripts
The following instructions will guide the user in running the subsidence scripts <br/>
The script subsidence_pipeline.py will create the vertical displacement files for every two pairs.
The script subsidence2timeseries.py will create images that show the cumulative vertical motion for a point that is closest to the point provided to the script.
All downloaded SAR data should be saved in a directory called 'input'. Scripts should be saved in a 'scripts' directory at the same level as input.
The subsidence_pipeline.py will create a directory called 'output' at the same level as the 'input' and the 'scripts' folder that contains IBEAM and NetCDF results
for vertical motion.
### Prerequisites
+ Ubuntu 20.04 LTS
+ Python3 for ubuntu [anaconda 3](https://docs.anaconda.com/anaconda/install/linux/)
+ Snappy api for ubuntu [snappy api](https://senbox.atlassian.net/wiki/spaces/SNAP/pages/19300362/How+to+use+the+SNAP+API+from+Python).
+ Snaphu for linux with 'sudo apt-get install snaphu' in the commandline

### Usage
+ Install all the prerequisites
+ Increase memory for SNAP using this [forum](https://forum.step.esa.int/t/increase-snappy-memory-beginner/6269)
+ Create environments with the provided yaml files and activate
+ Configure your snap to work with this specific environment
+ Obtain SLC SAR IW (VV and VH) for a specific path from [Vertex](https://search.asf.alaska.edu/#/). Use their python script download option for multiple downloads.

