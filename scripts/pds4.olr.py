#!/usr/bin/python
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

========
pds4.olr
========

Create a PDS4-style XML label for a 0222-Science OLR file.

Author: Dustin Buccino
Email: dustin.r.buccino@jpl.nasa.gov
Affiliation: Planetary Radar and Radio Sciences, Group 332K
             Jet Propulsion Laboratory, California Institute of Technology
Date Created: 02-MAY-2022
Last Modified: 20-SEP-2023

Synopsis::
   pds4.olr.py -t <XML_template> [options] <olr_file>
   
Options::

Required:
   -t <XML_template>, the XML label template for the OLR file. this file
                      will be mission-specific
Optional:
   -r <filename>, rename the TNF file to this convention for the label
                     {start_year} = starting year of the file
                      {start_doy} = starting day of year of the file
                     {start_time} = starting time HHMM of file (UTC)
                      {dl_dss_id} = downlink DSS ID. If there are multiple, will print "MM"
                    {dnlink_band} = downlink band.
                      {ul_dss_id} = uplink DSS ID. If there are multiple, will print "MM"
                    {uplink_band} = downlink band.
                             {bw} = recording bandwith in kHz, zero-padded to 3 digits

"""

import os
from datetime import datetime
from argparse import ArgumentParser

import rdef_0222sci
import pds4.util as util
from pds4.template import XML_Template

def main(args):
    """ main program function """
    
    # Open OLR file and get the required information
    reader = rdef_0222sci.Reader( args.Input )
    info = rdef_0222sci.Info( reader )
    print( info )
    
    # Rename the file if desired
    if len(info.uplink_station_id) == 1:
        uplink = str(info.uplink_station_id[0])
    elif len(info.uplink_station_id) > 1:
        uplink = 'MM'
    else:
        uplink = 'NN'
    if args.rename is not None:
        new_filename = args.rename.format( start_year = info.start_time.strftime('%Y'),
                                           start_doy = info.start_time.strftime('%j'),
                                           start_time = info.start_time.strftime('%H%M'),
                                           dl_dss_id = info.station_id,
                                           dl_band = info.downlink_band,
                                           ul_dss_id = uplink,
                                           ul_band = info.uplink_band[0],
                                           bw = str(info.recording_bw/1000).zfill(3) )
        os.rename( args.Input, new_filename )
        args.Input = new_filename
        
    # Open template
    Template = XML_Template( args.template )
    
    # form new logical identifier
    file_base = os.path.basename( args.Input ).split('.')[0]
    lid = Template.read('<logical_identifier>').rsplit(':',1)[0] + ':' + file_base

    # Add DSN station context
    util.add_dsn_station_context( Template, info.station_id )
    
    # Fill label with information
    Template.replace( '<logical_identifier>', lid )
    Template.replace( '<modification_date>', datetime.now().strftime('%Y-%m-%d') )
    Template.replace( '<start_date_time>', info.start_time.strftime('%Y-%m-%dT%H:%M:%SZ') )
    Template.replace( '<stop_date_time>', info.end_time.strftime('%Y-%m-%dT%H:%M:%SZ') )
    Template.replace( '<file_name>', args.Input )
    Template.replace( '<local_identifier>', file_base )
    Template.replace( '<creation_date_time>', info.end_time.strftime('%Y-%m-%dT%H:%M:%SZ') )
    Template.replace( '<md5_checksum>', util.md5hashfile(args.Input) )
    Template.replace( '<file_size unit="byte">', str(os.path.getsize(args.Input)) )
    Template.replace( '<record_length unit="byte">', str(info.record_length) )
    Template.replace( '<records>', str(info.num_records), True )
    
    # Do something here about 16bit/8bit record
    if info.bits !=  16:
        raise ValueError('Cannot handle data that is not 16-bit. Update program and label template to deal with 8/4/2/1-bit data.')
    
    # Write label
    out_filename = util.label_filename( args.Input )
    Template.write( out_filename )
    
    
if __name__ == '__main__':

    # Create parser
    parser = ArgumentParser()

    # Add required arguments
    parser.add_argument('Input', type=str,
        help='Name of the input BOA file to read')
    parser.add_argument('-r','--rename', dest='rename', type=str, default=None,
        help='rename the Input file to this naming convention              ' + \
             '  {start_year} = starting year of the file                   ' + \
             '  {start_doy} = starting day of year of the file             ' + \
             '  {start_time} = starting time of file (UTC)                 ' + \
             '  {dl_dss_id} = downlink DSS ID                              ' + \
             '  {dl_band} = downlink band                              ' + \
             '  {ul_dss_id} = uplink DSS ID                                ' + \
             '  {ul_band} = downlink band                              ' + \
             '  {bw} = recording bandwith in kHz, zero-padded to 3 digits  ')
    parser.add_argument('-t','--template',dest='template', type=str, required=True,
        help='Location of the XML label template to use')

    # Parse
    args = parser.parse_args()

    # Error checking
    if not os.path.exists( args.Input ):
       parser.error( 'File %s does not exist' % args.Input )
    if not os.path.exists( args.template ):
       parser.error( 'Template file %s does not exist' % args.template )

    # Run code
    main(args)
