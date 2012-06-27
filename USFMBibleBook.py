#!/usr/bin/python3
#
# USFMBibleBook.py
#   Last modified: 2012-06-22 by RJH (also update versionString below)
#
# Module handling the USFM markers for Bible books
#
# Copyright (C) 2010-2012 Robert Hunt
# Author: Robert Hunt <robert316@users.sourceforge.net>
# License: See gpl-3.0.txt
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
Module for defining and manipulating USFM Bible books.
"""

progName = "USFM Bible book handler"
versionString = "0.23"


import os, logging
from gettext import gettext as _

import Globals
from InternalBibleBook import InternalBibleBook


class USFMBibleBook( InternalBibleBook ):
    """
    Class to load and manipulate a single USFM file / book.
    """

    def __init__( self, logErrorsFlag ):
        """
        Create the USFM Bible book object.
        """
        InternalBibleBook.__init__( self, logErrorsFlag ) # Initialise the base class
        self.objectType = "USFM"
        self.objectNameString = "USFM Bible Book object"
    # end of __init__


    def load( self, bookReferenceCode, folder, filename, encoding='utf-8' ):
        """
        Load the USFM Bible book from a file.
        """

        def doAppendLine( marker, text ):
            """ Check for newLine markers within the line (if so, break the line)
                    and save the information in our database. """
            #originalMarker, originalText = marker, text # Only needed for the debug print line below
            if '\\' in text: # Check markers inside the lines
                markerList = self.USFMMarkers.getMarkerListFromText( text )
                ix = 0
                for insideMarker, nextSignificantChar, iMIndex in markerList: # check paragraph markers
                    if self.USFMMarkers.isNewlineMarker(insideMarker): # Need to split the line for everything else to work properly
                        if ix==0:
                            loadErrors.append( _("{} {}:{} NewLine marker '{}' shouldn't appear within line in \\{}: '{}'").format( self.bookReferenceCode, c, v, insideMarker, marker, text ) )
                            if self.logErrorsFlag: logging.error( _("NewLine marker '{}' shouldn't appear within line after {} {}:{} in \\{}: '{}'").format( insideMarker, self.bookReferenceCode, c, v, marker, text ) ) # Only log the first error in the line
                            self.addPriorityError( 96, c, v, _("NewLine marker \\{} shouldn't be inside a line").format( insideMarker ) )
                        thisText = text[ix:iMIndex].rstrip()
                        self.appendLine( marker, thisText )
                        ix = iMIndex + 1 + len(insideMarker) + len(nextSignificantChar) # Get the start of the next text -- the 1 is for the backslash
                        #print( "Did a split from {}:'{}' to {}:'{}' leaving {}:'{}'".format( originalMarker, originalText, marker, thisText, insideMarker, text[ix:] ) )
                        marker = insideMarker # setup for the next line
                if ix != 0: # We must have separated multiple lines
                    text = text[ix:] # Get the final bit of the line
            self.appendLine( marker, text ) # Call the function in the base class to save the line (or the remainder of the line if we split it above)
        # end of doAppendLine


        import SFMFile
        if Globals.verbosityLevel > 2: print( "  " + _("Loading {}...").format( filename ) )
        self.bookReferenceCode = bookReferenceCode
        self.isOneChapterBook = bookReferenceCode in self.BibleBooksCodes.getSingleChapterBooksList()
        self.sourceFolder = folder
        self.sourceFilename = filename
        self.sourceFilepath = os.path.join( folder, filename )
        originalBook = SFMFile.SFMLines()
        originalBook.read( self.sourceFilepath, encoding=encoding )

        # Do some important cleaning up before we save the data
        c = v = '0'
        lastMarker = lastText = ''
        loadErrors = []
        for marker,text in originalBook.lines: # Always process a line behind in case we have to combine lines
            #print( "After {} {}:{} \\{} '{}'".format( bookReferenceCode, c, v, marker, text ) )
            # Keep track of where we are for more helpful error messages
            if marker=='c' and text: c = text.split()[0]; v = '0'
            elif marker=='v' and text: v = text.split()[0]
            elif marker=='restore': continue # Ignore these lines completely

            if self.USFMMarkers.isNewlineMarker( marker ):
                if lastMarker: doAppendLine( lastMarker, lastText )
                lastMarker, lastText = marker, text
            elif self.USFMMarkers.isInternalMarker( marker ) \
            or marker.endswith('*') and self.USFMMarkers.isInternalMarker( marker[:-1] ): # the line begins with an internal marker -- append it to the previous line
                if text:
                    loadErrors.append( _("{} {}:{} Found '\\{}' internal marker at beginning of line with text: {}").format( self.bookReferenceCode, c, v, marker, text ) )
                    if self.logErrorsFlag: logging.warning( _("Found '\\{}' internal marker after {} {}:{} at beginning of line with text: {}").format( marker, self.bookReferenceCode, c, v, text ) )
                else: # no text
                    loadErrors.append( _("{} {}:{} Found '\\{}' internal marker at beginning of line (with no text)").format( self.bookReferenceCode, c, v, marker ) )
                    if self.logErrorsFlag: logging.warning( _("Found '\\{}' internal marker after {} {}:{} at beginning of line (with no text)").format( marker, self.bookReferenceCode, c, v ) )
                self.addPriorityError( 97, c, v, _("Found \\{} internal marker on new line in file").format( marker ) )
                if not lastText.endswith(' ') and marker!='f': lastText += ' ' # Not always good to add a space, but it's their fault! Don't do it for footnotes, though.
                lastText +=  '\\' + marker + ' ' + text
                if Globals.verbosityLevel > 3: print( "{} {} {} Appended {}:'{}' to get combined line {}:'{}'".format( self.bookReferenceCode, c, v, marker, text, lastMarker, lastText ) )
            else: # the line begins with an unknown marker
                if text:
                    loadErrors.append( _("{} {}:{} Found '\\{}' unknown marker at beginning of line with text: {}").format( self.bookReferenceCode, c, v, marker, text ) )
                    if self.logErrorsFlag: logging.error( _("Found '\\{}' unknown marker after {} {}:{} at beginning of line with text: {}").format( marker, self.bookReferenceCode, c, v, text ) )
                else: # no text
                    loadErrors.append( _("{} {}:{} Found '\\{}' unknown marker at beginning of line (with no text").format( self.bookReferenceCode, c, v, marker ) )
                    if self.logErrorsFlag: logging.error( _("Found '\\{}' unknown marker after {} {}:{} at beginning of line (with no text)").format( marker, self.bookReferenceCode, c, v ) )
                self.addPriorityError( 100, c, v, _("Found \\{} unknown marker on new line in file").format( marker ) )
                for tryMarker in sorted( self.USFMMarkers.getNewlineMarkersList(), key=len, reverse=True ): # Try to do something intelligent here -- it might be just a missing space
                    if marker.startswith( tryMarker ): # Let's try changing it
                        if lastMarker: doAppendLine( lastMarker, lastText )
                        lastMarker, lastText = tryMarker, marker[len(tryMarker):] + ' ' + text
                        loadErrors.append( _("{} {}:{} Changed '\\{}' unknown marker to '{}' at beginning of line: {}").format( self.bookReferenceCode, c, v, marker, tryMarker, text ) )
                        if self.logErrorsFlag: logging.warning( _("Changed '\\{}' unknown marker to '{}' after {} {}:{} at beginning of line: {}").format( marker, tryMarker, self.bookReferenceCode, c, v, text ) )
                        break
                # Otherwise, don't bother processing this line -- it'll just cause more problems later on
        if lastMarker: doAppendLine( lastMarker, lastText ) # Process the final line

        if loadErrors: self.errorDictionary['Load Errors'] = loadErrors
    # end of load


def main():
    """
    Demonstrate reading and processing some USFM Bible databases.
    """
    import USFMFilenames

    def demoFile( folder, filename, bookReferenceCode, logErrorsFlag ):
        if Globals.verbosityLevel > 1: print( _("Loading {} from {}...").format( bookReferenceCode, filename ) )
        UBB = USFMBibleBook( logErrorsFlag )
        UBB.load( bookReferenceCode, folder, filename, encoding )
        if Globals.verbosityLevel > 1: print( "  ID is '{}'".format( UBB.getField( 'id' ) ) )
        if Globals.verbosityLevel > 1: print( "  Header is '{}'".format( UBB.getField( 'h' ) ) )
        if Globals.verbosityLevel > 1: print( "  Main titles are '{}' and '{}'".format( UBB.getField( 'mt1' ), UBB.getField( 'mt2' ) ) )
        if Globals.verbosityLevel > 0: print( UBB )
        UBB.validateUSFM()
        UBBVersification = UBB.getVersification ()
        if Globals.verbosityLevel > 2: print( UBBVersification )
        UBBAddedUnits = UBB.getAddedUnits ()
        if Globals.verbosityLevel > 2: print( UBBAddedUnits )
        UBB.check()
        UBErrors = UBB.getErrors()
        if Globals.verbosityLevel > 2: print( UBErrors )
    # end of demoFile

    # Handle command line parameters
    from optparse import OptionParser
    parser = OptionParser( version="v{}".format( versionString ) )
    #parser.add_option("-e", "--export", action="store_true", dest="export", default=False, help="export the XML file to .py and .h tables suitable for directly including into other programs")
    Globals.addStandardOptionsAndProcess( parser )

    if Globals.verbosityLevel > 0: print( "{} V{}".format( progName, versionString ) )

    logErrors = True

    if 0: # Test individual files
        #name, encoding, testFolder, filename, bookReferenceCode = "WEB", "utf-8", "/mnt/Work/Bibles/English translations/WEB (World English Bible)/eng-web_usfm/", "06-JOS.usfm", "JOS" # You can put your test file here
        #name, encoding, testFolder, filename, bookReferenceCode = "WEB", "utf-8", "/mnt/Work/Bibles/English translations/WEB (World English Bible)/eng-web_usfm/", "44-SIR.usfm", "SIR" # You can put your test file here
        name, encoding, testFolder, filename, bookReferenceCode = "Matigsalug", "utf-8", "/mnt/Data/Matigsalug/Scripture/MBTV/", "MBT15EZR.SCP", "EZR" # You can put your test file here
        #name, encoding, testFolder, filename, bookReferenceCode = "Matigsalug", "utf-8", "/mnt/Data/Matigsalug/Scripture/MBTV/", "MBT67REV.SCP", "REV" # You can put your test file here
        if os.access( testFolder, os.R_OK ):
            demoFile( testFolder, filename, bookReferenceCode, logErrors )
        else: print( "Sorry, test folder '{}' doesn't exist on this computer.".format( testFolder ) )

    if 1: # Test a whole folder full of files
        #name, encoding, testFolder = "Matigsalug", "utf-8", "/mnt/Data/Matigsalug/Scripture/MBTV/" # You can put your test folder here
        name, encoding, testFolder = "WEB", "utf-8", "/mnt/Work/Bibles/English translations/WEB (World English Bible)/eng-web_usfm/" # You can put your test folder here
        if os.access( testFolder, os.R_OK ):
            if Globals.verbosityLevel > 1: print( _("Scanning {} from {}...").format( name, testFolder ) )
            fileList = USFMFilenames.USFMFilenames( testFolder ).getConfirmedFilenames()
            for bookReferenceCode,filename in fileList:
                demoFile( testFolder, filename, bookReferenceCode, logErrors )
        else: print( "Sorry, test folder '{}' doesn't exist on this computer.".format( testFolder ) )
# end of main

if __name__ == '__main__':
    main()
## End of USFMBibleBook.py
