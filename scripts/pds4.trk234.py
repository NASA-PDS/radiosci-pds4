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

===========
pds4.trk234
===========

Create a PDS4-style XML label for a TRK 2-34 file.

This program is rather complicated and requires a
template XML file of the label and a configuration
directory where the bits and bytes of the TRK 2-34
file are stored.

Author: Dustin Buccino
Email: dustin.r.buccino@jpl.nasa.gov
Affiliation: Planetary Radar and Radio Science, Group 332K
             Jet Prouplsion Laboratory, California Institute of Technology
Date Created: 19-AUG-2014
Last Modified: 14-SEP-2023

Synopsis::

   pds4.trk234.py -c <config_dir> -t <XML_template> [options] <tnf_file>

Options::

Required:
   -c <config_dir>, the configuration directory where the SFDU data type
                    XML files are stored
   -t <XML_template>, the XML label template for the TRK 2-34 file. this file
                      will be mission-specific

Optional:
   -r <filename>, rename the TNF file to this convention for the label
                     {start_year} = starting year of the file
                      {start_doy} = starting day of year of the file
                     {start_time} = starting time of file (UTC)
                     {count_time} = doppler count time, in seconds.
                      {dl_dss_id} = downlink DSS ID. If there are multiple, will print "MM"
                    {dnlink_band} = downlink band. If there are multiple, will print "M"
                      {ul_dss_id} = uplink DSS ID. If there are multiple, will print "MM"
                    {uplink_band} = uplink band. If there are multiple, will print "M"
                  for example, "dawnvegr_{start_year}_{start_doy}.tnf"
   -v, validate the output file using the PDS4 validate software
   -o, keep original TNF file (do not sort the file by SFDU type - NOT RECOMMENDED)
   -q, quick version. okay for very large (>1GB), predictable (single-spacecraft) TNF files
   --upper, make the naming convention uppercase

"""

# Required imports
import os
import sys
from argparse import ArgumentParser
from datetime import datetime
import trk234
import pds4.util as util
from pds4.template import XML_Template

# Define the default configuraiton directory
DEFAULT_CONFIG_DIR = os.getenv('RS_TRK234_DEFAULT_CONFIG')

class Label:
   """
   The basic class that will generate a label for a given TNF file
   """

   def __init__(self, tnf_file, label_template, config_directory, quick=False):
      """ Class constructor """

      # Save the TNF file name and configuration directory
      self.filename = tnf_file
      self.config_dir = config_directory

      # Load the template
      self.Template = XML_Template( label_template )

      # Load the TNF file and parse the SFDUs (exept tracking chdo to save speed)
      self.tnf = trk234.Reader( tnf_file )
      if quick:
         self.trk234_info = trk234.Info( self.tnf, True )
         print( "Using `quick` option! Some checks are NOT done and assumptions ARE made. Manually check the label." )
      else:
         self.tnf.decode( trk_chdo=False, progress=True )
         self.trk234_info = trk234.Info( self.tnf )

         # Validate the TNF type 16 and 17. They must contain only ***ONE*** observation or else
         # we cannot label them! Very important!
         for s in self.tnf.sfdu_list:
            if s.pri_chdo.format_code == 16:
               if s.label.sfdu_length != 200:
                  ValueError('File ' + self.filename + ' contains a DT16 with more than one observation.\n' +
                             'Expected label.sfdu_length = 200, actual label.sfdu_length = %i' % s.label.sfdu_length )
            if s.pri_chdo.format_code == 17:
               if s.label.sfdu_length != 216:
                  ValueError('File ' + self.filename + ' contains a DT17 with more than one observation.\n' +
                             'Expected label.sfdu_length = 216, actual label.sfdu_length = %i' % s.label.sfdu_length )

      # Load the configuration files
      self.tableTemplate = []
      for i in range(0,18):
         fn = os.path.abspath( config_directory ) + os.sep + 'trk_TableBinary_SFDU_%02i.xml' % i
         self.tableTemplate.append( XML_Template( fn ) )

   def __str__(self):
      """ convert this class to a string for printing """
      return str(self.Template)

   def fill(self):
      """ rewrite the template with updated information based on the TNF """

      # Replace the unique LID reference
      file_base = os.path.basename( self.filename ).split('.')[0].lower()
      lid = self.Template.read('<logical_identifier>').rsplit(':',1)[0] + ':' + file_base.lower()
      self.Template.replace( '<logical_identifier>', lid )

      # Replace the modification date
      self.Template.replace( '<modification_date>', datetime.now().strftime('%Y-%m-%d') )

      # Replace the applicable start time
      self.Template.replace( '<start_date_time>', self.trk234_info.startTime.strftime('%Y-%m-%dT%H:%M:%SZ') )

      # Replace the applicable stop time
      self.Template.replace( '<stop_date_time>', self.trk234_info.endTime.strftime('%Y-%m-%dT%H:%M:%SZ') )

      # Replace the file name
      self.Template.replace( '<file_name>', os.path.basename(self.filename) )

      # Replace the creation date
#      self.Template.replace( '<creation_date_time>', self.trk234_info.lastModified.strftime('%Y-%m-%dT%H:%M:%SZ') )
      self.Template.replace( '<creation_date_time>', self.trk234_info.endTime.strftime('%Y-%m-%dT%H:%M:%SZ') )

      # Replace the file size
      self.Template.replace( '<file_size unit="byte">', str(os.path.getsize(self.filename)) )

      # Replace the number of records - the first instance in the file
      self.Template.replace( '<records>', str(self.trk234_info.numRecords), True )

      # Replace the MD5 checksum
      self.Template.replace( '<md5_checksum>', util.md5hashfile(self.filename) )

      # Print the TRK 2-34 info to the comments
      self.Template.insert( '<comment>', str(self.trk234_info), 'first' )

      # Add DSN station context
      stations = list(set(self.trk234_info.uplinkDssId+self.trk234_info.dnlinkDssId))
      for stn in stations:
          util.add_dsn_station_context( self.Template, stn )


      # Determine the number of each SFDU, and modify the label appropriately
      # --- THIS ASSUMES YOU'VE ALREADY REGROUPED THE SFDUs ---
      byte_location = 0
      for i in self.trk234_info.dataTypes:

         # Number of SFDUs for this data type
         n_sfdus = self.trk234_info.numberDataTypes[i]

         # Read number of bits from the XML template for the data type
         n_bits = int( self.tableTemplate[i].read('<record_length unit="byte">') )

         # Replace the current byte offset in the template
         self.tableTemplate[i].replace( '<offset unit="byte">', str(byte_location) )

         # Replace number of records
         self.tableTemplate[i].replace( '<records>', str(n_sfdus), True )
#         self.tableTemplate[i].replace( '<groups>', str(n_sfdus), True )
         self.tableTemplate[i].replace( '<groups>', '0', True )

         # Update byte location
         byte_location = byte_location + n_bits * n_sfdus

         # Insert into the template
         if any('<Table_Binary>' in x for x in self.Template.data):
            self.Template.insert( '</Table_Binary>', self.tableTemplate[i].data ,'last' )
         else:
            self.Template.insert( '</File>', self.tableTemplate[i].data, 'last' )

   def write(self, out_filename):
      """ write template to file """
      self.Template.write( out_filename )

# ---------------------------------------------------------------------------

def main():
   """ Main program function. This is the first executed code,
       and contains the necessary argument parsing and dump functions """

   # Get the TNF file we're working with
   tnf_file = args.Input

   # sort the TRK 2-34 file and re-write as new filename
   if args.sort:
      # sort, rename, rename: output = sorted TNF of same name, original TNF appended with '.original'
      print( "Sorting the TRK-2-34 file by data type in ascending order..." )
      os.system( 'trk234_regroup ' + tnf_file + ' ' + tnf_file + '.sorted' )
      os.rename( tnf_file, tnf_file + '.original' )
      os.rename( tnf_file + '.sorted', tnf_file )
      

   # Initalize label creation and load the TNF file into memory
   label = Label( tnf_file, args.template, args.config, args.quick )

   # Rename the TNF file if necessary, and change the name of the TNF file in the label
   if args.rename is not None:
      tnf_new_name = args.rename.format( start_year=label.trk234_info.startTime.strftime('%Y') ,
                                         start_doy=label.trk234_info.startTime.strftime('%j'),
                                         start_time=label.trk234_info.startTime.strftime('%H%M'),
                                         count_time='mmmm' if len( label.trk234_info.dopplerCountTime ) != 1 else str(int(label.trk234_info.dopplerCountTime[0])).zfill(4),
                                         dl_dss_id='mm' if len( label.trk234_info.dnlinkDssId )!=1 else label.trk234_info.dnlinkDssId[0],
                                         dnlink_band='m' if len( label.trk234_info.dnlinkBand )!=1 else label.trk234_info.dnlinkBand[0].lower(),
                                         ul_dss_id='mm' if len( label.trk234_info.uplinkDssId )!=1 else label.trk234_info.uplinkDssId[0],
                                         uplink_band='m' if len( label.trk234_info.uplinkBand )!=1 else label.trk234_info.uplinkBand[0].lower() )
      if args.uppercase:
         tnf_new_name = tnf_new_name.upper()
      os.rename( tnf_file, tnf_new_name )
      tnf_file = tnf_new_name
      label.filename = tnf_new_name

   # Fill the label with information
   label.fill()

   # Write label
   label_file = util.label_filename( tnf_file )
   label.write( label_file )

# If called as a script, go to the main() function immediately
if __name__ == "__main__":

   # Setup the parser
   parser = ArgumentParser( prog='pds4.trk234',
                            description='Label a DSN TRK-2-34 file with a PDS4 XML label' )

   # Add arguments
   parser.add_argument( 'Input', type=str,
                        help='the name of the TRK-2-34 file to label' )
   parser.add_argument( '-t', '--template', dest='template', type=str, required=True,
                        help='the XML label template' )

   parser.add_argument( '-c', '--config-dir', dest='config', type=str,
                        help='the configuration directory for this program. the default is ' + \
                            DEFAULT_CONFIG_DIR )
   parser.add_argument( '-r', '--rename', dest='rename', type=str, default=None,
                        help='rename the input tnf_file to this naming convention   ' + \
                             'example: "MROMAGR_{start_year}_{start_doy}_V1.TNF     ' + \
                             'List of naming options:                               ' + \
                             ' {start_year} = starting year of the file             ' + \
                             ' {start_doy} = starting day of year of the file       ' + \
                             ' {start_time} = starting time of file (UTC)           ' + \
                             ' {count_time} = 4 digit doppler count time (seconds)  ' + \
                             ' {dl_dss_id} = downlink DSS ID (multiple = "mm")      ' + \
                             ' {dnlink_band} = downlink band (multiple = "m")       ' + \
                             ' {ul_dss_id} = uplink DSS ID (multiple = "mm")        ' + \
                             ' {uplink_band} = uplink band (multiple = "m")         ' )
   parser.add_argument( '-o', '--original', dest='sort', default=True, action='store_false',
                        help='do not resort the TNF file (not recommended)' )
   parser.add_argument( '-q', '--quick', dest='quick', default=False, action='store_true',
                        help='quick version, makes some assumptions. okay for very large, predictable files')
   parser.add_argument( '--upper', dest='uppercase', default=False, action='store_true',
                        help='make naming convetion uppercase' )

   # Parse the command line automatically
   args = parser.parse_args()

   # Error checking - does the file exist
   if not os.path.exists( args.Input ):
      parser.error( 'File %s does not exist' % args.Input )
   if not os.path.exists( args.template ):
      parser.error( 'Template file %s does not exist' % args.template )

   if not args.config:
      print( "Using default configuration directory: %s" % DEFAULT_CONFIG_DIR )
      args.config = DEFAULT_CONFIG_DIR

   main()
