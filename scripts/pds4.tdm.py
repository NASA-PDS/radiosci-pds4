#!/usr/bin/python3
# Copyright (c) 2026, California Institute of Technology ("Caltech").
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
pds4.tdm
========

Create a PDS4-style XML label for a TDM file.

The TDM must contain only tracking data from DSN or similar station
and not any unusual data formats. Supported types include Doppler,
ranging, and uplink frequency.

Author: Dustin Buccino
Email: dustin.r.buccino@jpl.nasa.gov
Affiliation: Planetary Radar and Radio Science, Group 332K
             Jet Prouplsion Laboratory, California Institute of Technology
Date Created: 09-MAR-2026
Last Modified: 09-MAR-2026

Synopsis::

   pds4.tdm.py -t <XML_template> [options] <tdm_file>

Options::

Required:
   -t <XML_template>, the XML label template for the TDM file. this file
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

"""
from argparse import ArgumentParser
import os, sys
from datetime import datetime, timedelta
import shutil

sys.path.append( '/home/source/pds4' )
from pds4.template import XML_Template
import pds4.util as util


PAD_SPACING = 79
KEYWORD_SPACING = 24



HEADER = """             <Header>
                   <name>TDM Metadata Header</name>
                   <offset unit="byte">{start_byte}</offset>
                   <object_length unit="byte">{header_length}</object_length>
                   <parsing_standard_id>7-Bit ASCII Text</parsing_standard_id>
                   <description>Tracking Data Message metadata for the next DATA block</description>
             </Header>
"""

SINGLE_ITEM_TABLE = """             <Table_Character>
                   <name>TDM Tracking Records</name>
                   <offset unit="byte">{start_byte}</offset>
                   <records>{records}</records>
                   <description>Timeseries of Tracking Data Message Tracking Records for {types}</description>
                   <record_delimiter>Line-Feed</record_delimiter>
                   <Record_Character>
                       <fields>4</fields>
                       <groups>0</groups>
                       <record_length unit="byte">{record_length}</record_length>
                       <Field_Character>
                           <name>keyword</name>
                           <field_number>1</field_number>
                           <field_location unit="byte">{item1_location}</field_location>
                           <data_type>ASCII_String</data_type>
                           <field_length unit="byte">{item1_length}</field_length>
                           <description>Data type keyword describing this tracking data record</description>
                       </Field_Character>
                       <Field_Character>
                           <name>equals</name>
                           <field_number>2</field_number>
                           <field_location unit="byte">{item2_location}</field_location>
                           <data_type>ASCII_String</data_type>
                           <field_length unit="byte">{item2_length}</field_length>
                           <description>Delimiter separating the data from the keyword, an equals sign (=)</description>
                       </Field_Character>
                       <Field_Character>
                           <name>timetag</name>
                           <field_number>3</field_number>
                           <field_location unit="byte">{item3_location}</field_location>
                           <data_type>ASCII_Date_Time_DOY</data_type>
                           <field_length unit="byte">{item3_length}</field_length>
                           <description>Timetag of the tracking data record, in UTC</description>
                       </Field_Character>
                       <Field_Character>
                           <name>measurement</name>
                           <field_number>4</field_number>
                           <field_location unit="byte">{item4_location}</field_location>
                           <data_type>ASCII_Real</data_type>
                           <field_length unit="byte">{item4_length}</field_length>
                           <description>TTracking data measurement corresponding with the keyword</description>
                       </Field_Character>
                   </Record_Character>
             </Table_Character>
"""

def tdm_writemeta( Template, start_byte, end_byte ):
    print('   metadata starts %d ends %d' % (start_byte, end_byte-1) )

    content = HEADER.format(
        start_byte = start_byte-1,
        header_length = end_byte - start_byte
        )
    insert_table_to_template( Template, content )

def tdm_writedata( Template, data_structure, start_byte, end_byte ):
    n_records = len(data_structure)
    structure_types = list(set(data_structure))
    print('   %d data record types %s' % (len(structure_types), str(structure_types)) )
    print('   data record count %d' % n_records)
    print('   data record starts %d ends %d ***' % (start_byte, end_byte) )
    print('   *** ')
    types = [x[0] for x in structure_types]
    s = structure_types[0][1]

    content = SINGLE_ITEM_TABLE.format(
        start_byte = start_byte-1,
        records = n_records,
        types = ','.join(types),
        # total size, including the two spaces after = and after datetime, plus EOL, normally should equal 80
        record_length = s[0][1] + s[1][1] + s[2][1] + s[3][1] + 2 + 1,
        item1_location = s[0][0], item1_length = s[0][1],
        item2_location = s[1][0], item2_length = s[1][1],
        item3_location = s[2][0], item3_length = s[2][1],
        item4_location = s[3][0], item4_length = s[3][1],
        )
    insert_table_to_template( Template, content )

def insert_table_to_template( Template, content ):
    file_contents = ''.join(Template.data)
    file_index = file_contents.rfind('</File>')
    header_index = file_contents.rfind('</Header>')
    table_index = file_contents.rfind('</Table_Character>')
    if file_index > header_index and file_index > table_index:
        Template.insert( '</File>', content, 'last' )
    if header_index > file_index and header_index > table_index:
        Template.insert( '</Header>', content, 'last' )
    if table_index > file_index and table_index > header_index:
        Template.insert( '</Table_Character>', content, 'last' )

# Main function: call this first
def main( args ):

    for filename in args.Input:
        print(filename)

        # pad end of data with spaces

        newfilename = filename+'.padded.txt'
        print('padding lines to %d, keywords padded to %d spaces'% (PAD_SPACING, KEYWORD_SPACING) )
        newfile = open(newfilename, 'w')
        with open(filename, 'r') as f:
            for line in f:
                if '=' in line:
                    x = line.split('=')
                    line = x[0].ljust(KEYWORD_SPACING) + '=' +  x[1]
                newline = line.strip().ljust(PAD_SPACING)+'\n'
                newfile.write(newline)
        newfile.close()

        # open label template for reading/writing
        Template = XML_Template( args.Template )

        # variables to use during the loop reading the TDM file
        start_date = []
        end_date = []
        dss = []
        readmeta = False
        readdata = False

        uplinkDssId = []
        dnlinkDssId = []
        dnlinkBand = []
        uplinkBand = []
        dopCount = []
        path = None

        # Loop through each line in the TDM to read it
        with open(newfilename, 'r') as f:
            
            current_byte_position = 1 # PDS starts counting at 1
            for (line_number,line) in enumerate(f):

                current_byte_position = current_byte_position + len(line)

                # continually read these attributes. they will be used in the label metadata later
                if 'CREATION_DATE' in line:
                    creation_date = datetime.strptime( line.split('=')[-1].strip()[0:17], '%Y-%jT%H:%M:%S' )
                if 'START_TIME' in line:
                    start_date.append( datetime.strptime( line.split('=')[-1].strip()[0:17], '%Y-%jT%H:%M:%S' ) )
                if 'STOP_TIME' in line:
                    end_date.append( datetime.strptime( line.split('=')[-1].strip()[0:17], '%Y-%jT%H:%M:%S' ) )
                if 'PARTICIPANT' in line:
                    if 'DSS' in line:
                        dss.append( line.split('=')[-1].strip() )

                # determine if we are in the META or the DATA blocks
                if 'META_STOP' in line:
                    if path == '1,2,1':
                        uplinkDssId.append( p1[-2:] )
                        uplinkBand.append( xmtr_band )
                        dnlinkDssId.append( p1[-2:] )
                        dnlinkBand.append( rcvr_band )
                        dopCount.append(ctt)
                    elif path == '1,2,3':
                        uplinkDssId.append( p1[-2:] )
                        uplinkBand.append( xmtr_band )
                        dnlinkDssId.append( p3[-2:] )
                        dnlinkBand.append( rcvr_band )
                        dopCount.append(ctt)
                    elif path == '1,2':
                        if 'DSS' in p1:
                            uplinkDssId.append( p1[-2:] )
                            uplinkBand.append( xmtr_band )
                        if 'DSS' in p2:
                            dnlinkDssId.append( p2[-2:] )
                            dnlinkBand.append( rcvr_band )
                            dopCount.append(ctt)
                    elif path == None:
                        uplinkDssId.append( p1[-2:] )
                        uplinkBand.append( xmtr_band )
                    path = None

                    readmeta = False
                    endmetabyte = current_byte_position - 1
                    # write metadata
                    tdm_writemeta( Template, startmetabyte, endmetabyte )
                if 'DATA_STOP' in line:
                    readdata = False
                    enddatabyte = current_byte_position - len(line) - 1
                    # print the labeling
                    tdm_writedata( Template, datastructure, startdatabyte, enddatabyte )

                if readmeta:
                    if 'PATH' in line:
                        path = line.split('=')[-1].strip()
                    if 'PARTICIPANT_1' in line:
                        p1 = line.split('=')[-1].strip()
                    if 'PARTICIPANT_2' in line:
                        p2 = line.split('=')[-1].strip()
                    if 'PARTICIPANT_3' in line:
                        p3 = line.split('=')[-1].strip()
                    if 'TRANSMIT_BAND' in line:
                        xmtr_band = line.split('=')[-1].strip()
                    if 'RECEIVE_BAND' in line:
                        rcvr_band = line.split('=')[-1].strip()
                    if 'INTEGRATION_INTERVAL' in line:
                        ctt = float(line.split('=')[-1].strip())

                if readdata:
                    x = line.strip().split(' ')
                    x = [z for z in x if z] # remove blanks
                    lastbyte = len(line)-1
                    datatype = x[0]
                    indexes = []
                    for (number, item) in enumerate(x):
                        index = line.find(item)
                        size = len(item)
                        if number == 0:
                            size = KEYWORD_SPACING # REQUIRES PADDING!
                        if number == 1:
                            if size != 1:
                                print('Warning: invalid TDM data structure before line number %d' % line_number)
                        if number == 2:
                            nextindex = index + size + 1
                        if number == 3:
                            index = nextindex # assumption since the second should always be a fixed-width datetime
                            size = lastbyte - index
                        if len(item) != 0:
                            # PDS starts counting bytes at 1
                            indexes.append( (index + 1, size) )
                    # data structure defines the variable, start byte, and length of each entry
                    # should always be len(4)
                    if len(indexes) != 4:
                        print(line)
                        print(x)
                        print("Warning: invalid TDM data structure before line number %d" % line_number)
                    datastructure.append((datatype, tuple(indexes)))

                if 'DATA_START' in line:
                    readdata = True
                    startdatabyte = current_byte_position
                    datastructure = []
                if 'META_START' in line:
                    readmeta = True
                    startmetabyte = current_byte_position - len(line)


        # template metadata injection
        file_start_time =  min(start_date)
        print('   start_time = %s' % file_start_time.strftime('%Y-%m-%dT%H:%M:%S') )
        file_stop_time = max(end_date)
        print('   stop_time = %s' % file_stop_time.strftime('%Y-%m-%dT%H:%M:%S') )
        file_create_time = creation_date
        print('   creation_time = %s' % file_create_time.strftime('%Y-%m-%dT%H:%M:%S') )
        dsn_stations = list(set(dss))
        for stn in dsn_stations:
            util.add_dsn_station_context( Template, stn[-2:] )

        dnlinkBand = list(set(dnlinkBand))
        uplinkBand = list(set(uplinkBand))
        dnlinkDssId = list(set(dnlinkDssId))
        uplinkDssId = list(set(uplinkDssId))
        dopCount = list(set(dopCount))
        print(dnlinkBand)
        print(uplinkBand)
        print(dnlinkDssId)
        print(uplinkDssId)
        print(dopCount)

        # Rename the file
        if args.rename is not None:
            # parameters with logic
            if len(dnlinkDssId) == 0:
                dl_dss_id = 'nn'
            elif len(dnlinkDssId) == 1:
                dl_dss_id = dnlinkDssId[0]
            else:
                dl_dss_id = 'mm'

            if len(dnlinkBand) == 0:
                dl_band = 'n'
            elif len(dnlinkBand) == 1:
                dl_band = dnlinkBand[0]
            else:
                dl_band = 'm'

            if len(uplinkDssId) == 0:
                ul_dss_id = 'nn'
            elif len(uplinkDssId) == 1:
                ul_dss_id = uplinkDssId[0]
            else:
                ul_dss_id = 'mm'

            if len(uplinkBand) == 0:
                ul_band = 'n'
            elif len(uplinkBand) == 1:
                ul_band = uplinkBand[0]
            else:
                ul_band = 'm'

            if len(dopCount) == 0:
                integ = 'nnnn'
            elif len(dopCount) == 1:
                integ = '%04d' % int(dopCount[0])
            else:
                integ = 'mmmm'

            new_name = args.rename.format( start_year=file_start_time.strftime('%Y'),
                                           start_doy=file_start_time.strftime('%j'),
                                           start_time=file_start_time.strftime('%H%M'),
                                           dl_dss_id=dl_dss_id,
                                           dnlink_band=dl_band,
                                           ul_dss_id=ul_dss_id,
                                           uplink_band=ul_band,
                                           count_time = integ,
                                           version=args.Version )
        else:
            new_name = filename
        if args.uppercase:
            new_name = new_name.upper()
        shutil.move( newfilename, new_name )

        # write template
        labelname = util.label_filename( new_name )
        lid = Template.read('<logical_identifier>').rsplit(':',1)[0] + ':' + new_name.lower().split('.')[0]
        Template.replace( '<logical_identifier>', lid )
        Template.replace( '<modification_date>', datetime.now().strftime('%Y-%m-%d') )
        Template.replace( '<start_date_time>', file_start_time.strftime('%Y-%m-%dT%H:%M:%SZ') )
        Template.replace( '<stop_date_time>', file_stop_time.strftime('%Y-%m-%dT%H:%M:%SZ') )
        Template.replace( '<file_name>', new_name )
        Template.replace( '<creation_date_time>', file_create_time.strftime('%Y-%m-%dT%H:%M:%SZ') )
        Template.replace( '<md5_checksum>', util.md5hashfile(new_name) )
        Template.replace( '<file_size unit="byte">', str(os.path.getsize(new_name)) )
        Template.write( labelname ) 

# If called as a script, go to the main() function immediately.
if __name__ == "__main__":

    # Create parser
    parser = ArgumentParser()
    
    # Required arguments
    parser.add_argument('Input', type=str, nargs='+',
                        help="Input TDM file name(s)")
    parser.add_argument( '-t', '--template', dest='Template', type=str, required=True,
                        help='the XML label template' )

    # optional arguments
    parser.add_argument('-v','--version', dest='Version', metavar='x', type=int, default=1,
        help='file version number (default=1)')
    parser.add_argument( '-r', '--rename', dest='rename', type=str, default=None,
                        help='rename the input tnf_file to this naming convention      ' + \
                             'example: "MROMAGR_{start_year}_{start_doy}_V{version}.TDM ' + \
                             'List of naming options:                                  ' + \
                             ' {start_year} = starting year of the file                ' + \
                             ' {start_doy} = starting day of year of the file          ' + \
                             ' {start_time} = HHMM starting time of file (UTC)         ' + \
                             ' {dl_dss_id} = downlink DSS ID (multiple = "mm")         ' + \
                             ' {dnlink_band} = downlink band (multiple = "m")          ' + \
                             ' {ul_dss_id} = uplink DSS ID (multiple = "mm")           ' + \
                             ' {uplink_band} = uplink band (multiple = "m")            ' + \
                             ' {count_time} = 4 digit doppler count time (seconds)  ' + \
                             ' {version} = file version')
    parser.add_argument( '--upper', dest='uppercase', default=False, action='store_true',
                        help='make naming convetion uppercase' )

    # Parse the command line automatically    
    args = parser.parse_args()

    main( args )
