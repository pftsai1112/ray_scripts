""" Add Plan Goals from Protocol

    This script is for physicians to approve their contour set for planning and to
    generate a Treatment Planning Order (TPO) for import into ARIA. As part of TPO
    creation, this script will also add clinical goals and initialize the treatment
    plan(s).

    Finally, dose is computed and then exported after each beamset is created. The DICOM
    export path is set in the configuration settings below. The option to only create
    beams is available by un-checking the "calculate" and "export" runtime options from
    the configuration dialog box.

    This program is free software: you can redistribute it and/or modify it under the
    terms of the GNU General Public License as published by the Free Software Foundation,
    either version 3 of the License, or (at your option) any later version.

    This program is distributed in the hope that it will be useful, but WITHOUT ANY
    WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
    PARTICULAR PURPOSE. See the GNU General Public License for more details.

    You should have received a copy of the GNU General Public License along with this
    program. If not, see <http://www.gnu.org/licenses/>.
    """

__author__ = 'Mark Geurts'
__contact__ = 'mark.w.geurts@gmail.com'
__version__ = '1.0.0'
__license__ = 'GPLv3'
__help__ = 'https://github.com/wrssc/ray_scripts/wiki/Create-TPO'
__copyright__ = 'Copyright (C) 2018, University of Wisconsin Board of Regents'

# Import packages
import sys
import os
import connect
import UserInterface
import logging
import time
import WriteTpo
import Goals

# Define the protocol XML directory
protocol_folder = r'../protocols'

# Define the priority at or below which goals are not displayed
priority = 4


def main():
    # Get current patient, case, and exam
    try:
        patient = connect.get_current('Patient')
        case = connect.get_current('Case')
        exam = connect.get_current('Examination')
        patient.Save()

    except Exception:
        UserInterface.WarningBox('This script requires a patient to be loaded')
        sys.exit('This script requires a patient to be loaded')

    # Start timer
    tic = time.time()

    # Start script status
    status = UserInterface.ScriptStatus(steps=['Enter plan information for TPO',
                                               'Clean up structure list',
                                               'Approve structures',
                                               'Initialize plan and beamsets',
                                               'Set clinical goals',
                                               'Add planning goals',
                                               'Generate TPO'],
                                        docstring=__doc__,
                                        help=__help__)

    # Display input dialog box for TPO
    status.next_step(text='In order to approve the plan and create a TPO, please fill out the displayed form ' +
                          'with information about the plan. Once completed, click Continue.')

    tpo = UserInterface.TpoDialog(patient=patient, title='TPO Dialog', match=0.6, rx=3, priority=priority)
    tpo.load_protocols(os.path.join(os.path.dirname(__file__), protocol_folder))
    response = tpo.show(case=case, exam=exam)


if __name__ == 'main':
    main()