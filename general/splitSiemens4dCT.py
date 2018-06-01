""" Split Siemens 4D CT
    
    Divide the Siemens 4D into up to 13 phases
    
    Scope: Specific directories required.  Testing compatibility with dicom library

    Example Usage:

    This program is free software: you can redistribute it and/or modify it under
    the terms of the GNU General Public License as published by the Free Software
    Foundation, either version 3 of the License, or (at your option) any later
    version.
    
    This program is distributed in the hope that it will be useful, but WITHOUT
    ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
    FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
    
    You should have received a copy of the GNU General Public License along with
    this program. If not, see <http://www.gnu.org/licenses/>.
    """

__author__ = 'Adam Bayliss'
__contact__ = 'rabayliss@wisc.edu'
__date__ = '2018-Apr-06'
__version__ = '1.0.0'
__status__ = 'Development'
__deprecated__ = False
__reviewer__ = 'Someone else'
__reviewed__ = 'YYYY-MM-DD'
__raystation__ = '7.0.0'
__maintainer__ = 'One maintainer'
__email__ =  'rabayliss@wisc.edu'
__license__ = 'GPLv3'
__copyright__ = 'Copyright (C) 2018, University of Wisconsin Board of Regents'
__credits__ = ['']


from connect import *
import tempfile
import zipfile
import sys
import clr
import os
import random
mydir = tempfile.mkdtemp()
sys.path.append(mydir)
#this location must be edited if used in other versions of RayStation
#zipfile.ZipFile(r'\\mvs-rayssql01\DicomImageStorage\Python 4D Package\pydicom.egg').extractall(mydir)
import pydicom
clr.AddReference("PresentationFramework")
from System.Windows import *

#gui folder selection
def get_folder():
    clr.AddReference("System.Windows.Forms")
    from System import Windows
    folderDialog = Windows.Forms.FolderBrowserDialog()
    folderDialog.rootfolder = "\\mvs-rayssql01\DicomImageStorage"
    folderDialog.ShowNewFolderButton = True
    folderDialog.SelectedPath = ""
    folderDialog.Description = "Please select a folder for Siemens 4DCT DICOM import"
    if (folderDialog.ShowDialog() == Windows.Forms.DialogResult.OK):
        return folderDialog.SelectedPath
    else:
        sys.exit()

#this is a check to see if the is a period in the number
def isInt(x):
    try:
        #no period returns true
        if int(x)/float(x) == 1:
            return True
        else:
            #(1) period returns false
            return False
    except:
        #more than (1) period throughs and exception and returns false
        return False

def unmerge_4dct():
    #create the containers to keep track of the phases
    #this script should be valid for up to 13 phases, most vendors suggest 10 or less
    one = []
    two = []
    three = []
    four = []
    five = []
    six = []
    seven = []
    eight = []
    nine = []
    ten = []
    eleven =[]
    twelve = []
    thirteen = []
    #initiate counters to keep track of progress
    i = 1
    j = 1
    k = 1
    #create an arbitrary length of digits to change in the Series UID, the Series UID
    #must be the same for all the slices in a series and must be unique from any other series
    chlen = 6
    #initialize the variable that will contain the random numbers that will replace the last set
    #of number in the SeriesUID
    siuidrand = 0

    #recursively walk the path supplied by the user
    for root, subFolders, files in os.walk(path):
        #initialize the variable to compare for the progression through the files
        lof = len(files)

        #loop through every file, we will use logic to separate the NON DICOM files
        while lof > i:
            #k is used as a sanity check.  If the program gets caught in an endless loop k will break that loop
            k += 1
            #the loop is allowed to iterate 3 times the number of files found.  The typical value of k for a successful
            #import is less than 5, so this should be plenty of cushion.
            if k > len(files) * 3:
                print "An error occured, the conversion was not successful.  Please verify the CT Data."
                exit(0)

            #iterate over each file
            for file in files:

                #if the file is not a DICOM file this will through an exception, will will catch the exception and then continue the script
                try:
                    #open the file
                    dicom_file = root + "\\" + file
                    df = dicom.read_file(dicom_file)
                    #unless something goes wrong we will save the file after modification
                    save = 1
                    #check if the file is a CT slice
                    if df.Modality == 'CT':
                        #check if the slice is the next in the series
                        if int(df.InstanceNumber) == i:
                            #get the Series UID for the slice
                            siuid = df.SeriesInstanceUID
                            #get the last few digits (default is 6) of the Series UID
                            siuidchk = siuid[-chlen:]

                            #check to see if there are any periods in the last few digits of the Series UID, typically there should not be
                            if not isInt(siuidchk):
                                toolong = True
                                #while a period is found we will truncate the length by shortening the variable chlen
                                #it is possible that if there is a period in the second to last number xxxx.x the import will not be
                                #available for (1) phase due to duplicate Series UID if a planning CT is also imported.
                                while toolong:
                                    chlen -= 1
                                    siuidchk = siuid[-chlen:]
                                    #once no periods are found exit the loop
                                    if isInt(siuidchk):
                                        toolong = False

                            #do not change the replacement characters unless there is a required change in the length of the replacement variable
                            #this needs to stay the same for the entire phase, the length should not change ever because the Series UID should be
                            #the same for every slice prior to running this script, but this is added for unforseen changes in the future
                            if not len(str(siuidrand)) == chlen:
                                siuidrand = random.randint(10**(chlen-1),10**(chlen))

                            #make the change to the Series UID to make it unique from the original scan
                            siuid = siuid[:-chlen] + str(siuidrand)

                            #increment the check for correct slice
                            i+=1

                            #check to see if the second to last number is a 1, if it is then we will adjust to
                            #make sure we do not have duplicate Series UIDs if the number of phases exceed 10
                            checkfor1 = siuid[-2:-1]

                            #this will add the slice location to the phase bins, if the location already exists
                            #then it means that we have already completed that phase
                            #for the appropriate phase we will change the the Series UIDs to match, the Series number to match
                            #and the instance number to match the slice number for that series
                            if df.SliceLocation not in one:
                                one.append(df.SliceLocation)
                                df.SeriesNumber = 1
                                df.InstanceNumber = j
                                siuid = siuid[:-1]
                                siuid = siuid + '1'
                                j+=1

                            #after the first phase is complete we will reset the instance number to 1 only
                            #if it is the first slice of the new phase
                            elif df.SliceLocation not in two:
                                if not two:
                                    j = 1
                                two.append(df.SliceLocation)
                                df.SeriesNumber = 2
                                df.InstanceNumber = j
                                siuid = siuid[:-1]
                                siuid = siuid + '2'
                                j+=1
                            elif df.SliceLocation not in three:
                                if not three:
                                    j = 1
                                three.append(df.SliceLocation)
                                df.SeriesNumber = 3
                                df.InstanceNumber = j
                                siuid = siuid[:-1]
                                siuid = siuid + '3'
                                j+=1
                            elif df.SliceLocation not in four:
                                if not four:
                                    j = 1
                                four.append(df.SliceLocation)
                                df.SeriesNumber = 4
                                df.InstanceNumber = j
                                siuid = siuid[:-1]
                                siuid = siuid + '4'
                                j+=1
                            elif df.SliceLocation not in five:
                                if not five:
                                    j = 1
                                five.append(df.SliceLocation)
                                df.SeriesNumber = 5
                                df.InstanceNumber = j
                                siuid = siuid[:-1]
                                siuid = siuid + '5'
                                j+=1
                            elif df.SliceLocation not in six:
                                if not six:
                                    j = 1
                                six.append(df.SliceLocation)
                                df.SeriesNumber = 6
                                df.InstanceNumber = j
                                siuid = siuid[:-1]
                                siuid = siuid + '6'
                                j+=1
                            elif df.SliceLocation not in seven:
                                if not seven:
                                    j = 1
                                seven.append(df.SliceLocation)
                                df.SeriesNumber = 7
                                df.InstanceNumber = j
                                siuid = siuid[:-1]
                                siuid = siuid + '7'
                                j+=1
                            elif df.SliceLocation not in eight:
                                if not eight:
                                    j = 1
                                eight.append(df.SliceLocation)
                                df.SeriesNumber = 8
                                df.InstanceNumber = j
                                siuid = siuid[:-1]
                                siuid = siuid + '8'
                                j+=1
                            elif df.SliceLocation not in nine:
                                if not nine:
                                    j = 1
                                nine.append(df.SliceLocation)
                                df.SeriesNumber = 9
                                df.InstanceNumber = j
                                siuid = siuid[:-1]
                                siuid = siuid + '9'
                                j+=1
                            elif df.SliceLocation not in ten:
                                if not ten:
                                    j = 1
                                ten.append(df.SliceLocation)
                                df.SeriesNumber = 10
                                df.InstanceNumber = j
                                siuid = siuid[:-2]
                                siuid = siuid + ('20' if checkfor1 == 1 else '10')
                                j+=1
                            elif df.SliceLocation not in eleven:
                                if not eleven:
                                    j = 1
                                eleven.append(df.SliceLocation)
                                df.SeriesNumber = 11
                                df.InstanceNumber = j
                                siuid = siuid[:-2]
                                siuid = siuid + ('21' if checkfor1 == 1 else '11')
                                j+=1
                            elif df.SliceLocation not in twelve:
                                if not twelve:
                                    j = 1
                                twelve.append(df.SliceLocation)
                                df.SeriesNumber = 12
                                df.InstanceNumber = j
                                siuid = siuid[:-2]
                                siuid = siuid + ('22' if checkfor1 == 1 else '12')
                                j+=1
                            elif df.SliceLocation not in thirteen:
                                if not thirteen:
                                    j = 1
                                thirteen.append(df.SliceLocation)
                                df.SeriesNumber = 13
                                df.InstanceNumber = j
                                siuid = siuid[:-2]
                                siuid = siuid + ('23' if checkfor1 == 1 else '13')
                                j+=1
                        #if this was not the CT slice that we were expecting we will skip the rest and not save the file
                        else:
                            save = 0
                            pass
                    #if this is not a CT slice we will skip the rest and not save the file
                    #we will also remove the file from the file count
                    else:
                        save = 0
                        lof -=1
                        pass

                    #if save is still equal to 1 then all is good and we can update the Series UID and save the file
                    if save == 1:
                        df.SeriesInstanceUID = siuid
                        df.save_as(dicom_file)
                        #reset the replacement variable length to 6 incase it is the last slice of a series.
                        chlen = 6
                #if this was not a DICOM file we will remove it from the file count
                except:
                    lof-=1
                    pass


#import into a new patient
def import_new():

    # Get handle to patient db
    db = get_current("PatientDB")

    # Query patients from path
    pis = db.QueryPatientsFromPath(Path = path, Filter = filter)

    patients = ['{0} (ID {1}) \n'.format(pi['EncodedName'], pi['Id']) for pi in pis]

    if len(pis) > 1:
         MessageBox.Show("More than (1) patient found in the selected directory.  Please only select the directory for the patient you want, and or move the dicom into it's own directory")
         sys.exit()
    result = MessageBox.Show("\n".join(["The following patient will be DICOM imported into the database. The patient is:", "\n"] + patients) + "\n" +"\n" + "Do you want to continue?",
                    "DICOM import",
                    MessageBoxButton.YesNo,
                    MessageBoxImage.Question)

    if result == MessageBoxResult.No:
      sys.exit()

    #separate the phases
    unmerge_4dct()


    # Import patients
    for pi in pis:
      try:
        patient = get_current('Patient')
        patient.Save()
      except:
        print 'Initial save operation not needed...'
      try:
        db.ImportPatientFromPath(Path = path, Patient = pi, SeriesFilter = {}, ImportFilters = []) # {'Modality': '^CT$'})
      except Exception:
        print 'Failed to DICOM import patient (Id = {0}, Name = {1})'.format(pi['Id'], pi['EncodedName'])

#import into the current patient
def import_current():

    db = get_current("PatientDB")

    # Get handle to patient db
    patient = get_current("Patient")

    # Query CTs from path
    ct_query = db.QuerySeriesFromPath(Path=path,Filter={'PatientID':'^'+patient.PatientID+'$','Modality':'^CT$'})

    if ct_query.Count > 0:
        #separate the phases
        unmerge_4dct()
        #requery to include all the series that we create (each phase)
        ct_query = db.QuerySeriesFromPath(Path=path,Filter={'PatientID':'^'+patient.PatientID+'$','Modality':'^CT$'})
        #get the current list of Series UIDs already imported for the patient
        imported_uids = [e.Series[0].ImportedDicomUID for e in patient.Examinations]

        for ct in ct_query:
            #check each series (phase) to verify that the Series UID is not a duplicate then import the CT
            if not ct['SeriesUID'] in imported_uids:
                number = ct['SeriesNumber']
                warnings = patient.ImportDicomDataFromPath(Path=path,SeriesFilter={'SeriesNumber':number},ImportFilters=[])
                print warnings



#get the location of the DICOM files.
path = get_folder()

# Define filter
filter = {}

#ask the user if this will be imported into the current patient
result = MessageBox.Show("Will the CT be imported as a new patient?\n",
                "Current or New Patient",
                MessageBoxButton.YesNo,
                MessageBoxImage.Question)

#A patient must be saved before you can import DICOM
try:
    patient = get_current('Patient')
    patient.Save()
except:
    print 'Initial save operation not needed...'

#check if the users answer
if result == MessageBoxResult.Yes:
    #import to new patient
    import_new()
else:
    #import to current patient
    import_current()








