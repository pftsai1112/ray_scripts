""" Rename Beams In Beamset v01.00.02
    
    Written 9Jan2018 to automatically label beams in Raystation
    Determines the primary site of the Beam set by prompting the user
    The user identifies the site using the 4 letter pre-fix from the plan name
    If the user supplies more than 4 chars, the name is cropped
    The script will test the orientation of the patient and rename the beams accordingly
    If the beamset contains a couch kick the beams are named using the gXXCyy convention
    
    Versions: 
    01.00.00 Original submission
    01.00.01 PH reviewed, suggested eliminating an unused variable, changing integer
             floating point comparison, and embedding set-up beam creation as a 
             "try" to prevent a script failure if set-up beams were not selected
    01.00.02 PH Reviewed, correct FFP positioning issue.  Changed Beamset failure to 
             load to read the same as other IO-Faults

    This program is free software: you can redistribute it and/or modify it under
    the terms of the GNU General Public License as published by the Free Software
    Foundation, either version 3 of the License, or (at your option) any later version.
    
    This program is distributed in the hope that it will be useful, but WITHOUT
    ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
    FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
    
    You should have received a copy of the GNU General Public License along with
    this program. If not, see <http://www.gnu.org/licenses/>.
    """

__author__ = 'Adam Bayliss'
__contact__ = 'rabayliss@wisc.edu'
__date__ = '2018-02-18'

__version__ = '1.0.2'
__status__ = 'Development'
__deprecated__ = False
__reviewer__ = 'Patrick Hill'

__reviewed__ = '2018-02-05'
__raystation__ = '6.1.1.2'
__maintainer__ = 'Adam Bayliss'

__email__ =  'rabayliss@wisc.edu'
__license__ = 'GPLv3'
__copyright__ = 'Copyright (C) 2018, University of Wisconsin Board of Regents'

import wpf
import clr

clr.AddReference("System.Xml")

from System.Windows import Window
from System.Xml import XmlReader
from System.IO import StringReader
# Bring's in current data sets
from connect import *
from inspect import currentframe, getframeinfo



class MyWindow(Window):
    def __init__(self):
        # read in the markup of the gui
        xr = XmlReader.Create(StringReader(xaml))
        wpf.LoadComponent(self, xr)

    # this is the event handler for the Click event
    def submit_click(self, sender, e):
        self.DialogResult = True




xaml = """
<Window 
       xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation" 
       xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml" 
       Title="Site Name Specification"  Height="170.0" Width="450">
  <Grid>
     <Grid.ColumnDefinitions>
          <ColumnDefinition Width="150" />
          <ColumnDefinition Width="60" />
          <ColumnDefinition Width="30" />
        </Grid.ColumnDefinitions>
        <Grid.RowDefinitions>
          <RowDefinition Height="50" />
          <RowDefinition Height="Auto" />
        </Grid.RowDefinitions>          
        <Label VerticalAlignment="Center">Enter Site Name, .e.g. BreL:</Label>
        <TextBox Grid.Column = "1" Name="Site_Name" Margin = "0, 0, 2, 0" VerticalAlignment="Center"/>
        <Button Grid.Row = "5" Grid.ColumnSpan = "2" Content="Submit" HorizontalAlignment="Left" Margin="5,44,0,0" VerticalAlignment="Center" Width="75" Click="submit_click" />
  </Grid>
</Window> 
"""

if __name__ == "__main__":
#    frameinfo = getframeinfo(currentframe())
#    print 'frameinfo',frameinfo.filename, frameinfo.lineno
    dialog = MyWindow()
    dialog.ShowDialog()
    SiteName = dialog.Site_Name.Text[:4]

    try:
        patient = get_current('Patient')
    except:
        raise IOError('You load a patientfield')

    try:
        case = get_current('Case')
    except:
        raise IOError('You need to load a casefield')

    try:
        plan = get_current('Plan')
    except:
        raise IOError('You need to load a planfield')

    try:    
        beamset = get_current("BeamSet")
    except: 
        raise IOError("No beamset loaded")
# 
# Electrons, 3D, and VMAT Arcs are all that are supported.  Reject plans that aren't
    technique = beamset.DeliveryTechnique
    #
    # Oddly enough, Electrons are DeliveryTechnique = 'SMLC'
    if technique != 'SMLC' and technique != 'Arc' :
       raise IOError("Technique unsupported, manually name beams according to clinical convention.")   

# While loop variable definitions
    beamsinrange = True
    beam_index = 0
    patient_position = beamset.PatientPosition
#
# HFS Beam Naming
# Loop through all beams and except when there are no more (beamsinrange = False)
    if patient_position == 'HeadFirstSupine':
        while beamsinrange:
            try:
                GantryAngle = int(beamset.Beams[beam_index].GantryAngle)
                CouchAngle = int(beamset.Beams[beam_index].CouchAngle)
                GantryAngleString = str(int(GantryAngle)) 
                CouchAngleString = str(int(CouchAngle))
                # 
                # Determine if the type is an Arc or SMLC
                # Name arcs as #_Arc_<Site>_<Direction>_<Couch>
                if technique == 'Arc':
                    ArcDirection = beamset.Beams[beam_index].ArcRotationDirection
                    if ArcDirection == 'Clockwise':
                        ArcDirectionString = 'CW'
                    else:
                        ArcDirectionString = 'CC'
                    if CouchAngle == 0:
                        StandardBeamName = (str(beam_index+1) + '_Arc_' + SiteName + 
                          '_' + ArcDirectionString)
                    else:
                        StandardBeamName = (str(beam_index+1) + '_Arc_' + SiteName + 
                            '_' + ArcDirectionString + '_c' + CouchAngleString.zfill(1))
                else: 
                    if CouchAngle != 0:
                       StandardBeamName = (str(beam_index+1) + '_' + SiteName + '_g' 
                         + GantryAngleString.zfill(2)  + 'c' + CouchAngleString.zfill(2))
                    elif GantryAngle == 180:
                       StandardBeamName = str(beam_index+1) + '_' + SiteName + '_PA'
                    elif GantryAngle > 180 and GantryAngle < 270:
                       StandardBeamName = str(beam_index+1) + '_' + SiteName + '_RPO'
                    elif GantryAngle == 270:
                       StandardBeamName = str(beam_index+1) + '_' + SiteName + '_RLAT' 
                    elif GantryAngle > 270 and GantryAngle < 360:
                       StandardBeamName = str(beam_index+1) + '_' + SiteName + '_RAO' 
                    elif GantryAngle == 0:
                       StandardBeamName = str(beam_index+1) + '_' + SiteName + '_AP' 
                    elif GantryAngle > 0 and GantryAngle < 90:
                       StandardBeamName = str(beam_index+1) + '_' + SiteName + '_LAO' 
                    elif GantryAngle == 90:
                       StandardBeamName = str(beam_index+1) + '_' + SiteName + '_LLAT' 
                    elif GantryAngle > 90 and GantryAngle < 180:
                       StandardBeamName = str(beam_index+1) + '_' + SiteName + '_LPO' 
                    beamset.Beams[beam_index].Name = StandardBeamName    
                beam_index += 1
            except:
                beamsinrange = False
        await_user_input('Please go to Plan Design>Plan Setup and use Copy Setup to ensure there are 4 Setup beams')
        #
        # Set-Up Fields
        try:
            #
            # AP set-up field
            beamset.PatientSetup.SetupBeams[0].Name = "SetUp AP"
            beamset.PatientSetup.SetupBeams[0].Description = "SetUp AP"
            beamset.PatientSetup.SetupBeams[0].GantryAngle = "0.0"
            beamset.PatientSetup.SetupBeams[0].Segments[0].DoseRate = "5"

            #
            #Rt Lateral set-up field
            beamset.PatientSetup.SetupBeams[1].Name = "SetUp RtLat"
            beamset.PatientSetup.SetupBeams[1].Description = "SetUp RtLat"
            beamset.PatientSetup.SetupBeams[1].GantryAngle = "270.0"
            beamset.PatientSetup.SetupBeams[1].Segments[0].DoseRate = "5"

            #
            #Lt Lateral set-up field
            beamset.PatientSetup.SetupBeams[2].Name = "SetUp LtLat"
            beamset.PatientSetup.SetupBeams[2].Description = "SetUp LtLat"
            beamset.PatientSetup.SetupBeams[2].GantryAngle = "90.0"
            beamset.PatientSetup.SetupBeams[2].Segments[0].DoseRate = "5"
            #
            #Cone-Beam CT set-up field
            try:
                beamset.PatientSetup.SetupBeams[3].Name = "SetUp CBCT"
                beamset.PatientSetup.SetupBeams[3].Description = "SetUp CBCT"
                beamset.PatientSetup.SetupBeams[3].GantryAngle = "0.0"
                beamset.PatientSetup.SetupBeams[3].Segments[0].DoseRate = "5"
            except:
                await_user_input('Pretty Please go to Plan Design>Plan Setup and copy any Setup Beam then continue script')
                beamset.PatientSetup.SetupBeams[3].Name = "SetUp CBCT"
                beamset.PatientSetup.SetupBeams[3].Description = "SetUp CBCT"
                beamset.PatientSetup.SetupBeams[3].GantryAngle = "0.0"
                beamset.PatientSetup.SetupBeams[3].Segments[0].DoseRate = "5"
        except:
            raise IOError('Please select Create Set Up Beams in Edit Plan and Rerun script') 
        
    # Address the Head-first prone position
    # Loop through all beams and except when there are no more (beamsinrange = False)
    elif patient_position == 'HeadFirstProne':
        while beamsinrange :
            try:
                GantryAngle = int(beamset.Beams[beam_index].GantryAngle)
                CouchAngle = int(beamset.Beams[beam_index].CouchAngle)
                GantryAngleString = str(int(GantryAngle)) 
                CouchAngleString = str(int(CouchAngle))
                # 
                # Determine if the type is an Arc or SMLC
                # Name arcs as #_Arc_<Site>_<Direction>_<Couch>
                if technique == 'Arc':
                    ArcDirection = beamset.Beams[beam_index].ArcRotationDirection
                    if ArcDirection == 'Clockwise':
                        ArcDirectionString = 'CW'
                    else:
                        ArcDirectionString = 'CC'
                    if CouchAngle == 0:
                        StandardBeamName = (str(beam_index+1) + '_Arc_' + SiteName + 
                          '_' + ArcDirectionString)
                    else:
                        StandardBeamName = (str(beam_index+1) + '_Arc_' + SiteName + 
                                '_' + ArcDirectionString + '_c' + CouchAngleString.zfill(1))
                else: 
                    if CouchAngle != 0:
                       StandardBeamName = (str(beam_index+1) + '_' + SiteName + '_g' 
                         + GantryAngleString.zfill(2)  + 'c' + CouchAngleString.zfill(2))
                    elif GantryAngle == 180:
                       StandardBeamName = str(beam_index+1) + '_' + SiteName + '_AP'
                    elif GantryAngle > 180 and GantryAngle < 270:
                       StandardBeamName = str(beam_index+1) + '_' + SiteName + '_LAO'
                    elif GantryAngle == 270:
                       StandardBeamName = str(beam_index+1) + '_' + SiteName + '_LLAT' 
                    elif GantryAngle > 270 and GantryAngle < 360:
                       StandardBeamName = str(beam_index+1) + '_' + SiteName + '_LPO' 
                    elif GantryAngle == 0:
                       StandardBeamName = str(beam_index+1) + '_' + SiteName + '_PA' 
                    elif GantryAngle > 0 and GantryAngle < 90:
                       StandardBeamName = str(beam_index+1) + '_' + SiteName + '_RPO' 
                    elif GantryAngle == 90:
                       StandardBeamName = str(beam_index+1) + '_' + SiteName + '_RLAT' 
                    elif GantryAngle > 90 and GantryAngle < 180:
                       StandardBeamName = str(beam_index+1) + '_' + SiteName + '_RAO' 
                    beamset.Beams[beam_index].Name = StandardBeamName    
                beam_index += 1
            except:
                beamsinrange = False
        await_user_input('Please go to Plan Design>Plan Setup and use Copy Setup to ensure there are 4 Setup beams')
        #
        # Set-Up fields
        try:
            #
            # PA set-up field
            beamset.PatientSetup.SetupBeams[0].Name = "SetUp PA"
            beamset.PatientSetup.SetupBeams[0].Description = "SetUp PA"
            beamset.PatientSetup.SetupBeams[0].GantryAngle = "0.0"
            beamset.PatientSetup.SetupBeams[0].Segments[0].DoseRate = "5"

            #
            # Rt Lateral set-up field
            beamset.PatientSetup.SetupBeams[1].Name = "SetUp RtLat"
            beamset.PatientSetup.SetupBeams[1].Description = "SetUp RtLat"
            beamset.PatientSetup.SetupBeams[1].GantryAngle = "90.0"
            beamset.PatientSetup.SetupBeams[1].Segments[0].DoseRate = "5"

            #
            # Lt Lateral set-up field
            beamset.PatientSetup.SetupBeams[2].Name = "SetUp LtLat"
            beamset.PatientSetup.SetupBeams[2].Description = "SetUp LtLat"
            beamset.PatientSetup.SetupBeams[2].GantryAngle = "270.0"
            beamset.PatientSetup.SetupBeams[2].Segments[0].DoseRate = "5"

            #
            # Cone-Beam CT set-up field
            try:
                beamset.PatientSetup.SetupBeams[3].Name = "SetUp CBCT"
                beamset.PatientSetup.SetupBeams[3].Description = "SetUp CBCT"
                beamset.PatientSetup.SetupBeams[3].GantryAngle = "0.0"
                beamset.PatientSetup.SetupBeams[3].Segments[0].DoseRate = "5"
            except:
                await_user_input('Pretty Please go to Plan Design>Plan Setup and copy any Setup Beam then continue script')
                beamset.PatientSetup.SetupBeams[3].Name = "SetUp CBCT"
                beamset.PatientSetup.SetupBeams[3].Description = "SetUp CBCT"
                beamset.PatientSetup.SetupBeams[3].GantryAngle = "0.0"
                beamset.PatientSetup.SetupBeams[3].Segments[0].DoseRate = "5"
        except:
           raise IOError('Please select Create Set Up Beams in Edit Plan and Rerun script') 
    # Address the Feet-first supine position
    # Loop through all beams and except when there are no more (beamsinrange = False)
    elif patient_position == 'FeetFirstSupine':
        while beamsinrange :
            try:
                GantryAngle = int(beamset.Beams[beam_index].GantryAngle)
                CouchAngle = int(beamset.Beams[beam_index].CouchAngle)
                GantryAngleString = str(int(GantryAngle)) 
                CouchAngleString = str(int(CouchAngle))
            
                # 
                # Determine if the type is an Arc or SMLC
                # Name arcs as #_Arc_<Site>_<Direction>_<Couch>
                if technique == 'Arc':
                    ArcDirection = beamset.Beams[beam_index].ArcRotationDirection
                    if ArcDirection == 'Clockwise':
                        ArcDirectionString = 'CW'
                    else:
                        ArcDirectionString = 'CC'
                    if CouchAngle == 0:
                        StandardBeamName = (str(beam_index+1) + '_Arc_' + SiteName + 
                          '_' + ArcDirectionString)
                    else:
                        StandardBeamName = (str(beam_index+1) + '_Arc_' + SiteName + 
                            '_' + ArcDirectionString + '_c' + CouchAngleString.zfill(1))
                else:
                    if CouchAngle != 0:
                        StandardBeamName = (str(beam_index+1) + '_' + SiteName + '_g' 
                          + GantryAngleString.zfill(2)  + 'c' + CouchAngleString.zfill(2))
                    elif GantryAngle == 180:
                        StandardBeamName = str(beam_index+1) + '_' + SiteName + '_PA'
                    elif GantryAngle > 180 and GantryAngle < 270:
                        StandardBeamName = str(beam_index+1) + '_' + SiteName + '_LPO'
                    elif GantryAngle == 270:
                        StandardBeamName = str(beam_index+1) + '_' + SiteName + '_LLAT' 
                    elif GantryAngle > 270 and GantryAngle < 360:
                        StandardBeamName = str(beam_index+1) + '_' + SiteName + '_LAO' 
                    elif GantryAngle == 0:
                        StandardBeamName = str(beam_index+1) + '_' + SiteName + '_AP' 
                    elif GantryAngle > 0 and GantryAngle < 90:
                        StandardBeamName = str(beam_index+1) + '_' + SiteName + '_RAO' 
                    elif GantryAngle == 90:
                        StandardBeamName = str(beam_index+1) + '_' + SiteName + '_RLAT' 
                    elif GantryAngle > 90 and GantryAngle < 180:
                        StandardBeamName = str(beam_index+1) + '_' + SiteName + '_RPO' 
                    beamset.Beams[beam_index].Name = StandardBeamName    
                beam_index += 1
            except:
                beamsinrange = False
        await_user_input('Please go to Plan Design>Plan Setup and use Copy Setup to ensure there are 4 Setup beams')
        #
        # Set-Up Fields
        try:
            # AP set-up field
            beamset.PatientSetup.SetupBeams[0].Name = "SetUp AP"
            beamset.PatientSetup.SetupBeams[0].Description = "SetUp AP"
            beamset.PatientSetup.SetupBeams[0].GantryAngle = "0.0"
            beamset.PatientSetup.SetupBeams[0].Segments[0].DoseRate = "5"

          #Rt Lateral set-up field
            beamset.PatientSetup.SetupBeams[1].Name = "SetUp RtLat"
            beamset.PatientSetup.SetupBeams[1].Description = "SetUp RtLat"
            beamset.PatientSetup.SetupBeams[1].GantryAngle = "90.0"
            beamset.PatientSetup.SetupBeams[1].Segments[0].DoseRate = "5"

          #Lt Lateral set-up field
            beamset.PatientSetup.SetupBeams[2].Name = "SetUp LtLat"
            beamset.PatientSetup.SetupBeams[2].Description = "SetUp LtLat"
            beamset.PatientSetup.SetupBeams[2].GantryAngle = "270.0"
            beamset.PatientSetup.SetupBeams[2].Segments[0].DoseRate = "5"

          #
          #Cone-Beam CT set-up field
            try:
                beamset.PatientSetup.SetupBeams[3].Name = "SetUp CBCT"
                beamset.PatientSetup.SetupBeams[3].Description = "SetUp CBCT"
                beamset.PatientSetup.SetupBeams[3].GantryAngle = "0.0"
                beamset.PatientSetup.SetupBeams[3].Segments[0].DoseRate = "5"
            except:
                await_user_input('Pretty Please go to Plan Design>Plan Setup and copy any Setup Beam then continue script')
                beamset.PatientSetup.SetupBeams[3].Name = "SetUp CBCT"
                beamset.PatientSetup.SetupBeams[3].Description = "SetUp CBCT"
                beamset.PatientSetup.SetupBeams[3].GantryAngle = "0.0"
                beamset.PatientSetup.SetupBeams[3].Segments[0].DoseRate = "5"
        except:
            raise IOError('Please select Create Set Up Beams in Edit Plan and Rerun script') 

    # Address the Feet-first prone position
    # Loop through all beams and except when there are no more (beamsinrange = False)
    elif patient_position == 'FeetFirstProne':
        while beamsinrange :
            try:
                GantryAngle = int(beamset.Beams[beam_index].GantryAngle)
                CouchAngle = int(beamset.Beams[beam_index].CouchAngle)
                GantryAngleString = str(int(GantryAngle)) 
                CouchAngleString = str(int(CouchAngle))
                # 
                # Determine if the type is an Arc or SMLC
                # Name arcs as #_Arc_<Site>_<Direction>_<Couch>
                if technique == 'Arc':
                    ArcDirection = beamset.Beams[beam_index].ArcRotationDirection
                    if ArcDirection == 'Clockwise':
                        ArcDirectionString = 'CW'
                    else:
                        ArcDirectionString = 'CC'
                    if CouchAngle == 0:
                        StandardBeamName = (str(beam_index+1) + '_Arc_' + SiteName + 
                          '_' + ArcDirectionString)
                    else:
                        StandardBeamName = (str(beam_index+1) + '_Arc_' + SiteName + 
                                '_' + ArcDirectionString + '_c' + CouchAngleString.zfill(1))
                else:
                    if CouchAngle != 0:
                       StandardBeamName = (str(beam_index+1) + '_' + SiteName + '_g' 
                         + GantryAngleString.zfill(2)  + 'c' + CouchAngleString.zfill(2))
                    elif GantryAngle == 180:
                       StandardBeamName = str(beam_index+1) + '_' + SiteName + '_AP'
                    elif GantryAngle > 180 and GantryAngle < 270:
                       StandardBeamName = str(beam_index+1) + '_' + SiteName + '_RAO'
                    elif GantryAngle == 270:
                       StandardBeamName = str(beam_index+1) + '_' + SiteName + '_RLAT' 
                    elif GantryAngle > 270 and GantryAngle < 360:
                       StandardBeamName = str(beam_index+1) + '_' + SiteName + '_RPO' 
                    elif GantryAngle == 0:
                       StandardBeamName = str(beam_index+1) + '_' + SiteName + '_PA' 
                    elif GantryAngle > 0 and GantryAngle < 90:
                       StandardBeamName = str(beam_index+1) + '_' + SiteName + '_LPO' 
                    elif GantryAngle == 90:
                       StandardBeamName = str(beam_index+1) + '_' + SiteName + '_LLAT' 
                    elif GantryAngle > 90 and GantryAngle < 180:
                       StandardBeamName = str(beam_index+1) + '_' + SiteName + '_LAO' 
                    beamset.Beams[beam_index].Name = StandardBeamName    
                beam_index += 1
            except:
                beamsinrange = False
        await_user_input('Please go to Plan Design>Plan Setup and use Copy Setup to ensure there are 4 Setup beams')
        try: 
            # PA set-up field
            beamset.PatientSetup.SetupBeams[0].Name = "SetUp PA"
            beamset.PatientSetup.SetupBeams[0].Description = "SetUp PA"
            beamset.PatientSetup.SetupBeams[0].GantryAngle = "0.0"
            beamset.PatientSetup.SetupBeams[0].Segments[0].DoseRate = "5"

            #Rt Lateral set-up field
            beamset.PatientSetup.SetupBeams[1].Name = "SetUp RtLat"
            beamset.PatientSetup.SetupBeams[1].Description = "SetUp RtLat"
            beamset.PatientSetup.SetupBeams[1].GantryAngle = "270.0"
            beamset.PatientSetup.SetupBeams[1].Segments[0].DoseRate = "5"
  
            #Lt Lateral set-up field
            beamset.PatientSetup.SetupBeams[2].Name = "SetUp LtLat"
            beamset.PatientSetup.SetupBeams[2].Description = "SetUp LtLat"
            beamset.PatientSetup.SetupBeams[2].GantryAngle = "90.0"
            beamset.PatientSetup.SetupBeams[2].Segments[0].DoseRate = "5"
            #
            #Cone-Beam CT set-up field
            try:
                beamset.PatientSetup.SetupBeams[3].Name = "SetUp CBCT"
                beamset.PatientSetup.SetupBeams[3].Description = "SetUp CBCT"
                beamset.PatientSetup.SetupBeams[3].GantryAngle = "0.0"
                beamset.PatientSetup.SetupBeams[3].Segments[0].DoseRate = "5"
            except:
                await_user_input('Pretty Please go to Plan Design>Plan Setup and copy any Setup Beam then continue script')
                beamset.PatientSetup.SetupBeams[3].Name = "SetUp CBCT"
                beamset.PatientSetup.SetupBeams[3].Description = "SetUp CBCT"
                beamset.PatientSetup.SetupBeams[3].GantryAngle = "0.0"
                beamset.PatientSetup.SetupBeams[3].Segments[0].DoseRate = "5"
        except:
            raise IOError('Please select Create Set Up Beams in Edit Plan and Rerun script') 
    else:
        raise IOError("Patient Orientation Unsupported.. Manual Beam Naming Required")

