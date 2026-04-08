#!/usr/bin/python3
# Copyright (c) 2023, California Institute of Technology ("Caltech").
# U.S. Government sponsorship acknowledged. Any commercial use must be 
# negotiated with the Office of Technology Transfer at the California 
# Institute of Technology.
# 
# This software may be subject to U.S. export control laws. By accepting this 
# software, the user agrees to comply with all applicable U.S. export laws 
# and regulations. User has the responsibility to obtain export licenses, or 
# other export authority as may be required before exporting such information 
# to foreign countries or providing access to foreign persons.
#
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice,
#   this list of conditions and the following disclaimer.
# * Redistributions must reproduce the above copyright notice, this list of
#   conditions and the following disclaimer in the documentation and/or other
#   materials provided with the distribution.
# * Neither the name of Caltech nor its operating division, the Jet Propulsion
#   Laboratory, nor the names of its contributors may be used to endorse or
#   promote products derived from this software without specific prior written
#   permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
"""

util: utilities for PDS4

Author: Dustin Buccino
Email: dustin.r.buccino@jpl.nasa.gov
Affiliation: Planetary Radar and Radio Sciences, Group 332K
             Jet Propulsion Laboratory, California Institute of Technology
Date Created: 03-MAR-2015
Last Modified: 14-SEP-2023

"""

import os
from hashlib import md5
import shutil

# ---------------------------------------------------------------------------
def label_filename( filename ):
   """ generate a label filename based on the TNF file name """
   return os.path.split( os.path.abspath(filename) )[0] + \
          os.sep + \
          os.path.basename( filename ).split('.')[0] + '.xml'

# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
def md5hashfile(filename, blocksize=65536):
   """ return the md5 hash of a file """
   
   # open file and start hasher
   file = open(filename, 'rb')
   hasher = md5()

   # block-by-block create the hash
   buf = file.read(blocksize)
   while len(buf) > 0:
      hasher.update(buf)
      buf = file.read(blocksize)

   # close file and return
   file.close()
   return hasher.hexdigest()

# ---------------------------------------------------------------------------

def NLtoCRLF(filename,copyfile=False):
   """ convert a text file from new-line (unix) to carrage-return line-feed (windows) """

   # copy file first if we need to
   if copyfile:
      shutil.move( filename, filename + '.originalNL' )

   # load file
   with open(filename, 'r') as f:
      data = f.read()

   # replace
   data2 = data.replace('\n','\r\n')

   # write file
   with open(filename, 'w') as f:
      f.write(data2) 

# ---------------------------------------------------------------------------
DSN_CONTEXT = """                   <Observing_System_Component>
                         <name>DSS-{stn} {size}-m Radio Telescope</name>
                         <type>Telescope</type>
                         <Internal_Reference>
                               <lid_reference>urn:nasa:pds:context:telescope:{complex}.dss{stn}_{size}m</lid_reference>
                               <reference_type>is_telescope</reference_type>
                         </Internal_Reference>
                   </Observing_System_Component>
"""
def add_dsn_station_context( Template, station_id ):

    if station_id in [14, 63, 43]:
        size = 70
    else:
        size = 34
    firstdigit = int(str(station_id)[0])
    if firstdigit == 1 or firstdigit == 2:
        cplx = 'goldstone'
    elif firstdigit == 3 or firstdigit == 4:
        cplx = 'canberra'
    elif firstdigit == 5 or firstdigit == 6:
        cplx = 'madrid'
    else:
        print('Unknown complex for station ID %d, manually modify the label' % station_id)
        cplx = 'UNKNOWN'

    Template.insert('</Observing_System_Component>', DSN_CONTEXT.format(stn=station_id, size=size, complex=cplx), 'last')
