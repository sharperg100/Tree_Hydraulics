# Forest Hydraulic Roughness
A python-based model for estimating Manning's *n* in riparian forests - see https://doi.org/10.1111/jfr3.12892.  

This model was created for the paper noted above, and evolved on an ad-hoc basis as ideas manifested. The code has not been cleaned up for broader use as yet. So, there are a few quirks and things that can be improved, like needing to manually create a results folder. Having moved on to other things, this is not a priority at the moment. Nevertheless, feel free to contact me if it is not working for you.  

## Dependencies
Python packages required include:
- scipy
- numpy
- pandas

## Model setup
A test model has been provided to demonstrate the model setup files (in the model folder). The various components and associated files are discussed below. 
- **_hydraulics.bat**: this is a batch file used to run the model. Two keys are passed to the python model through the batch file: the first being the name of the control file (ufm file) and the second being the folder for the project.
- **Dayboro_WTP_2009_0p6.ufm**: this the control file for the model, which contains all model commands.
- **channel_slopes.csv**: this file contains a list of the energy slopes to analyse.
- **Tree_db_2009_0p6.csv**: this is the tree database containing a list of the trees and their properties. 
- **Flow_depths.csv**: this file contains a list of the flow depths to analyse. 

## Control file (ufm - uniform flow model)
 
|Field | Description|
|------|------------|
|*!*|Used to add comments to the file|
|*Channel width ==*|Sets the channel width in metres|
|*Channel Length ==*|Sets the channel length in metres|
|*Channel Slopes (km) ==*|Sets the file path to  the csv file that lists the slopes to analyse. Slopes are: 1 m vertical drop in *x* km |
|*Channel Sidewalls ==*|*True* or *False*: sets whether to include side walls on the channel. For most applications this will be *False*.|
|*Channel Mannings n ==*|Sets the Manning's *n* of the forest floor.|
|*Tree DB ==*|Sets the file path to the tree database|
|*Set depths ==*|If set to *absolute*, the depths are in metres (the standard method). Otherwise, the depths are treated as a proportion of the tree height.|
|*Flow depths ==*|The path to the csv file listing the flow depths.|
|*Blockage == None*|Include this command to exclude tree blockage effects on the computed Manning's n; i.e. if tree blockage is not accounted for in the hydraulic model using storage and cell width reduction factors. However, this is not recommended and was included for testing only.|

## Tree databse
The tree databse is a csv file coltaining five columns as shown below.
- **ID**: a unique integer id for each tree or group of trees
- **Height**: The height of the tree or group of trees
- **Population**: The number of trees in the group of trees
- **GroundLevel**: Not used... started as an idea to include tree ground levels in the computation
- **Type**: Sets the type of tree. at the moment there is only one type of tree, which is *Casuarina-overstory*. 

## Outputs
The model produces results in a *results* folder. This folder must be manualy created by the user or the model will not run. Results are written as csv files listing the Manning's *n* for each flow depth analysed. A seperate csv file is created for each slope analysed. A seperate script, not inlcuded here as it is a bit raw, was used to load all the results into a dataframe and create plots of Manning's *n* for the paper. 

