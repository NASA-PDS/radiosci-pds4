# pds4
This set of scripts and associated libraries will create labels for Radio Science data products from NASA's Deep Space Network in Planetary Data System Version 4 (PDS4) XML format. This set labels:
* Deep Space Network **TRK-2-34** Tracking and Navigation Data Files [^1] as *Product_Observational*
* Deep Space Network **TRK-2-23** Media Calibration Data Files [^2] as *Product_Ancillary*
* Deep Space Network **0222_Science** Open Loop Data Files [^3] as *Product_Observational* (under development, limited functionality)
* CCSDS **TDM** Tracking Data Message Files as *Product_Observational* (limited to basic radiometric data types: uplink, doppler, ranging, signal power) - this has only been tested on TDMs derived from **TRK-2-34** files.
* Utility programs for manipulation of other PDS4 files

These utilities are provided to the community by the Planetary Data System Radio Science Sub Node (RSSN) within the Planetary Radar and Radio Sciences Group (332K) at the Jet Propulsion Laboratory, California Institute of Technology.

## Requirements
These utilities are written in Python. Although any version of Python 3 should work, the program was developed and tested under Python 3.6.8. Beyond the default libraries included in Python, the following are required depending on the data product:
* [trk234](https://github.jpl.nasa.gov/rssg/trk234)
* [rdef_0222sci](https://github.jpl.nasa.gov/rssg/rdef_0222sci)

## Installation

This is a Python library package with scripts and configuration files.

The library  can be installed by cloning the repository to your local machine and running:

```
pip install \path\to\pds4
```

Note the installation path. Add files from the `scripts/` directory to your execution path, and if using the `bin/` execution scripts, update the paths in the scripts appropriately.

Copy the label templates and configuration from the `xml/` directory to a location of your choosing.

### Configuration

For users with complicated Python environments or wish to simplify the installation, several `bash` scripts are provided in the `bin/` directory. In each of the files, edit the statement to point to the correct directory the library is installed:

```
# update pythonpath for the correct libraries
export PYTHONPATH=$PYTHONPATH:/home/source/pds4
```

Also update the location of the scripts:
```
# add the path of the script install directory
SCRIPTDIR=/home/source/pds4/scripts
```

Optionally, for TRK-2-34 data files, set an environment variable to point to the label templates for TRK-2-34. If you do not do this, you will need to provide the location of the label templates each time as an option in the program. For example, inside your `.bashrc` profile:

```
RS_TRK234_DEFAULT_CONFIG=/home/apps/Linux-x86_64/share/PDS/PDS4/format_files/TNF/config/
```

## Usage

### Architecture

Each script takes a data file and an XML label template file. The XML template file contains everything already needed - the scripts will not add new metadata. The script will read the data file to get appropriate information to fill the label, and then write a label. Optionally, the script will rename the file according to a user specified naming convention with common attributes as variables (e.g. start time).

Scripts are in the `scripts/` directory. Each script uses a common `XML_Template` class and utilities from the `pds4/` library. Additional libraries are required for each data type and specified above in the Requirements section.

Sample templates are provided in the `xml/` folder along with configuration files for the DSN TRK-2-34 data type.

### Label a TRK-2-34 Data File

The script to label a DSN TRK-2-34 Tracking and Navigation Data File (sometimes referred to as *TNF* files) is called `pds4.trk234.py`. This script **requires** the [trk234](https://github.jpl.nasa.gov/rssg/trk234) library installed on the `PATH` or `PYTHONPATH` and the scripts in the `trk234/bin/` directory on the `PATH`.` This software will *reformat* the raw data file such that each data type is in ascending order for labeling by calling the `trk234_regroup` program from the `trk234` package.

Usage: `pds4.trk234.py [-h] -t TEMPLATE [-c CONFIG] [-r RENAME] [-o] [-q] Input`

Basic Example: *label a TRK-2-34 data file using a template*
```
pds4.trk234.py -t /home/apps/Linux-x86_64/share/PDS/PDS4/format_files/TNF/Template_TRK2-34_Juno.xml GRV_JUGR_2023250_0445X14MC001V01.TNF
```

Complicated Example: *label a TRK-2-34 data file using a template, and also provide the config directory and rename the file at the same time*
```
pds4.trk234.py -t /home/apps/Linux-x86_64/share/PDS/PDS4/format_files/TNF/Template_TRK2-34_Juno.xml -c /home/apps/Linux-x86_64/share/PDS/PDS4/format_files/TNF/config/ 232511615SC61DSS35_noHdr.234 -r 'jnogrv_{start_year}{start_doy}_{start_time}_{uplink_band}{ul_dss_id}{dnlink_band}{dl_dss_id}_{count_time}_v01.dat'
```

If you did not set the `RS_TRK234_DEFAULT_CONFIG` environment variable, *you must also provide the `-c` option*

### Label a TRK-2-23 Ancillary File

No additional libraries are required for the TRK-2-23 Media Calibration Interface files. These are sometimes referred to as Control Statement Processor (CSP) files, becuase the content of the data is written as pseudo-code in the CSP language, read by the JPL Orbit Determination Program (ODP) and the MONTE software. 

To label a TRK-2-23 file, simply call the program and give a template file:

Usage: `pds4.csp.py [-h] -t TEMPLATE [-r RENAME] Input`

Example: *label a TRK-2-23 CSP file, and rename it*
```
pds4.csp.py -r nsyt_maro_{start_year}_{start_doy}_{end_year}_{end_doy}_tro.csp -t /home/apps/Linux-x86_64/share/PDS/PDS4/format_files/TRO/Template_TRO_Final_InSight.xml tro.csp
```

### Label a 0222_Science Data File

***This script is in development and is not fully vetted. Currently only validated for 1 kHz / 16-bit recordings.***

The script to label a 0222_Science Open Loop Data File (sometimes referred to as OLR data, in the distant pass this data is analogous to RSR or ODR data), requires the use of the [rdef_0222sci](https://github.jpl.nasa.gov/rssg/rdef_0222sci) library on the `PATH` or `PYTHONPATH`. It is simple:

Usage: `pds4.olr.py [-h] [-r RENAME] -t TEMPLATE Input`

Example: *label a 0222_Science file, and rename it*
```
pds4.olr -t /home/apps/Linux-x86_64/share/PDS/PDS4/format_files/OLR/Template_OLR_1kHz_16bit_Clipper_Draft.xml -r RSS999XXX{start_year}{start_doy}T{start_time}_{ul_band}{ul_dss_id}{dl_band}{dl_dss_id}{bw}KNJPL_OLR010.DAT polr1_ec_rs_atlo_rs_b.23_242_223228
```


## Disclaimer Statement
Copyright (c) 2023, California Institute of Technology ("Caltech").
U.S. Government sponsorship acknowledged. Any commercial use must be 
negotiated with the Office of Technology Transfer at the California 
Institute of Technology.

This software may be subject to U.S. export control laws. By accepting this 
software, the user agrees to comply with all applicable U.S. export laws 
and regulations. User has the responsibility to obtain export licenses, or 
other export authority as may be required before exporting such information 
to foreign countries or providing access to foreign persons.

All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright notice,
  this list of conditions and the following disclaimer.
* Redistributions must reproduce the above copyright notice, this list of
  conditions and the following disclaimer in the documentation and/or other
  materials provided with the distribution.
* Neither the name of Caltech nor its operating division, the Jet Propulsion
  Laboratory, nor the names of its contributors may be used to endorse or
  promote products derived from this software without specific prior written
  permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
POSSIBILITY OF SUCH DAMAGE.

[^1]: https://pds-geosciences.wustl.edu/radiosciencedocs/urn-nasa-pds-radiosci_documentation/dsn_trk-2-34/
[^2]: https://pds-geosciences.wustl.edu/radiosciencedocs/urn-nasa-pds-radiosci_documentation/dsn_trk-2-23/
[^3]: https://pds-geosciences.wustl.edu/radiosciencedocs/urn-nasa-pds-radiosci_documentation/dsn_0222-science/
