#!/usr/bin/env python3
#
# USFM2USX.minimal.py
#
# Command-line app to export a USX (XML) Bible.
#
# Copyright (C) 2019-2020 Robert Hunt
# Author: Robert Hunt <Freely.Given.org+BOS@gmail.com>
# License: See gpl-3.0.txt
#
"""
A short command-line app as part of BOS (Bible Organisational System) demos.
This app inputs any known type of Bible file(s) from disk
    and then exports a USX version in the (default) OutputFiles folder
        (inside the BibleOrgSys folder in your home folder).

Of course, you must already have Python3 installed on your system.
    (Probably installed by default on most modern Linux systems.)

Note that this app can be run from your BOS folder,
    e.g., using the command:
        Apps/USFM2USX.minimal.py path/to/BibleFileOrFolder

You can discover the available command line parameters with
        Apps/USFM2USX.minimal.py --help

This app also demonstrates how little code is required to use the BOS
    to load a Bible (in any of a large range of formats — see UnknownBible.py)
    and then to export it in your desired format (see options in BibleWriter.py).
"""
from BibleOrgSys import BibleOrgSysGlobals
from BibleOrgSys.BibleOrgSysGlobals import vPrint
from BibleOrgSys.UnknownBible import UnknownBible


PROGRAM_NAME = "USFM to USX (minimal)"
PROGRAM_VERSION = '0.05'


# Configure basic Bible Organisational System (BOS) set-up
parser = BibleOrgSysGlobals.setup( PROGRAM_NAME, PROGRAM_VERSION )
parser.add_argument( "inputBibleFileOrFolder", help="path/to/BibleFileOrFolder" )
BibleOrgSysGlobals.addStandardOptionsAndProcess( parser )

# Do the actual Bible load and export work that we want
unknownBible = UnknownBible( BibleOrgSysGlobals.commandLineArguments.inputBibleFileOrFolder )
loadedBible = unknownBible.search( autoLoadAlways=True, autoLoadBooks=True ) # Load all the books if we find any
if not isinstance( loadedBible, str ): # i.e., not an error message
    loadedBible.toUSX2XML() # Export as USX files (USFM inside XML)
    print( f"\nOutput should be in {BibleOrgSysGlobals.DEFAULT_WRITEABLE_OUTPUT_FOLDERPATH.joinpath( 'BOS_USX2_Export/' )}/ folder." )

# Do the BOS close-down stuff
BibleOrgSysGlobals.closedown( PROGRAM_NAME, PROGRAM_VERSION )
