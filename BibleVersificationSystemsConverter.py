#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# BibleVersificationSystemsConverter.py
#
# Module handling BibleVersificationSystem_*.xml to produce C and Python data tables
#   Last modified: 2011-12-06 (also update versionString below)
#
# Copyright (C) 2010-2011 Robert Hunt
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
Module handling BibleVersificationSystem_*.xml to produce C and Python data tables.
"""

progName = "Bible Chapter/Verse Systems handler"
versionString = "0.47"


import os, logging
from gettext import gettext as _
from collections import OrderedDict
from xml.etree.cElementTree import ElementTree

from singleton import singleton
import Globals
from BibleBooksCodes import BibleBooksCodes


@singleton # Can only ever have one instance
class BibleVersificationSystemsConverter:
    """
    A class to handle data for Bible versification systems.
    """

    def __init__( self ):
        """
        Constructor.
        """
        self.__filenameBase = "BibleVersificationSystems"

        # These fields are used for parsing the XML
        self.__treeTag = "BibleVersificationSystem"
        self.__headerTag = "header"
        self.__mainElementTag = "BibleBookVersification"

        # These fields are used for automatically checking/validating the XML
        self.__compulsoryAttributes = ()
        self.__optionalAttributes = ( "omittedVerses", "combinedVerses", "reorderedVerses", )
        self.__uniqueAttributes = self.__compulsoryAttributes + self.__optionalAttributes
        self.__compulsoryElements = ( "nameEnglish", "referenceAbbreviation", "numChapters", "numVerses", )
        self.__optionalElements = ()
        self.__uniqueElements = ( "nameEnglish", "referenceAbbreviation", ) + self.__optionalElements

        # These are fields that we will fill later
        self.__XMLSystems, self.__DataDict = {}, {}

        # Make sure we have the bible books codes data loaded and available
        self.__BibleBooksCodes = BibleBooksCodes().loadData()
    # end of __init__

    def loadSystems( self, XMLFolder=None ):
        """
        Load and pre-process the specified versification systems.
        """
        if not self.__XMLSystems: # Only ever do this once
            if XMLFolder==None: XMLFolder = os.path.join( os.path.dirname(__file__), "DataFiles", "VersificationSystems" ) # Relative to module, not cwd
            self.__XMLFolder = XMLFolder
            if Globals.verbosityLevel > 2: print( _("Loading versification systems from {}...").format( XMLFolder ) )
            filenamePrefix = "BIBLEVERSIFICATIONSYSTEM_"
            for filename in os.listdir( XMLFolder ):
                filepart, extension = os.path.splitext( filename )
                if extension.upper() == '.XML' and filepart.upper().startswith(filenamePrefix):
                    versificationSystemCode = filepart[len(filenamePrefix):]
                    if Globals.verbosityLevel > 3: print( _("Loading{} versification system from {}...").format( versificationSystemCode, filename ) )
                    self.__XMLSystems[versificationSystemCode] = {}
                    self.__XMLSystems[versificationSystemCode]["tree"] = ElementTree().parse( os.path.join( XMLFolder, filename ) )
                    assert( self.__XMLSystems[versificationSystemCode]["tree"] ) # Fail here if we didn't load anything at all

                    # Check and remove the header element
                    if self.__XMLSystems[versificationSystemCode]["tree"].tag  == self.__treeTag:
                        header = self.__XMLSystems[versificationSystemCode]["tree"][0]
                        if header.tag == self.__headerTag:
                            self.__XMLSystems[versificationSystemCode]["header"] = header
                            self.__XMLSystems[versificationSystemCode]["tree"].remove( header )
                            if len(header)>1:
                                logging.info( _("Unexpected elements in header") )
                            elif len(header)==0:
                                logging.info( _("Missing work element in header") )
                            else:
                                work = header[0]
                                if work.tag == "work":
                                    self.__XMLSystems[versificationSystemCode]["version"] = work.find("version").text
                                    self.__XMLSystems[versificationSystemCode]["date"] = work.find("date").text
                                    self.__XMLSystems[versificationSystemCode]["title"] = work.find("title").text
                                else:
                                    logging.warning( _("Missing work element in header") )
                        else:
                            logging.warning( _("Missing header element (looking for '{}' tag)").format( headerTag ) )
                    else:
                        logging.error( _("Expected to load '{}' but got '{}'").format( self.__treeTag, self.__XMLSystems[versificationSystemCode]["tree"].tag ) )
                    bookCount = 0 # There must be an easier way to do this
                    for subelement in self.__XMLSystems[versificationSystemCode]["tree"]:
                        bookCount += 1
                    logging.info( _("    Loaded {} books").format( bookCount ) )

                    if Globals.strictCheckingFlag:
                        self._validateSystem( self.__XMLSystems[versificationSystemCode]["tree"] )
        else: # The data must have been already loaded
            if XMLFolder is not None and XMLFolder!=self.__XMLFolder: logging.error( _("Bible versification systems are already loaded -- your different folder of '{}' was ignored").format( XMLFolder ) )
        return self
    # end of loadSystems

    def _validateSystem( self, versificationTree ):
        """
        """
        assert( versificationTree )

        uniqueDict = {}
        for elementName in self.__uniqueElements: uniqueDict["Element_"+elementName] = []
        for attributeName in self.__uniqueAttributes: uniqueDict["Attribute_"+attributeName] = []

        expectedID = 1
        for k,element in enumerate(versificationTree):
            if element.tag == self.__mainElementTag:
                # Check compulsory attributes on this main element
                for attributeName in self.__compulsoryAttributes:
                    attributeValue = element.get( attributeName )
                    if attributeValue is None:
                        logging.error( _("Compulsory '{}' attribute is missing from {} element in record {}").format( attributeName, element.tag, k ) )
                    if not attributeValue:
                        logging.warning( _("Compulsory '{}' attribute is blank on {} element in record {}").format( attributeName, element.tag, k ) )

                # Check optional attributes on this main element
                for attributeName in self.__optionalAttributes:
                    attributeValue = element.get( attributeName )
                    if attributeValue is not None:
                        if not attributeValue:
                            logging.warning( _("Optional '{}' attribute is blank on {} element in record {}").format( attributeName, element.tag, k ) )

                # Check for unexpected additional attributes on this main element
                for attributeName in element.keys():
                    attributeValue = element.get( attributeName )
                    if attributeName not in self.__compulsoryAttributes and attributeName not in self.__optionalAttributes:
                        logging.warning( _("Additional '{}' attribute ('{}') found on {} element in record {}").format( attributeName, attributeValue, element.tag, k ) )

                # Check the attributes that must contain unique information (in that particular field -- doesn't check across different attributes)
                for attributeName in self.__uniqueAttributes:
                    attributeValue = element.get( attributeName )
                    if attributeValue is not None:
                        if attributeValue in uniqueDict["Attribute_"+attributeName]:
                            logging.error( _("Found '{}' data repeated in '{}' field on {} element in record {}").format( attributeValue, attributeName, element.tag, k ) )
                        uniqueDict["Attribute_"+attributeName].append( attributeValue )

                # Check compulsory elements
                ID = element.find("referenceAbbreviation").text
                for elementName in self.__compulsoryElements:
                    if element.find( elementName ) is None:
                        logging.error( _("Compulsory '{}' element is missing in record with ID '{}' (record {})").format( elementName, ID, k ) )
                    if not element.find( elementName ).text:
                        logging.warning( _("Compulsory '{}' element is blank in record with ID '{}' (record {})").format( elementName, ID, k ) )

                # Check optional elements
                for elementName in self.__optionalElements:
                    if element.find( elementName ) is not None:
                        if not element.find( elementName ).text:
                            logging.warning( _("Optional '{}' element is blank in record with ID '{}' (record {})").format( elementName, ID, k ) )

                # Check for unexpected additional elements
                for subelement in element:
                    if subelement.tag not in self.__compulsoryElements and subelement.tag not in self.__optionalElements:
                        logging.warning( _("Additional '{}' element ('{}') found in record with ID '{}' (record {})").format( subelement.tag, subelement.text, ID, k ) )

                # Check the elements that must contain unique information (in that particular element -- doesn't check across different elements)
                for elementName in self.__uniqueElements:
                    if element.find( elementName ) is not None:
                        text = element.find( elementName ).text
                        if text in uniqueDict["Element_"+elementName]:
                            logging.error( _("Found '{}' data repeated in '{}' element in record with ID '{}' (record {})").format( text, elementName, ID, k ) )
                        uniqueDict["Element_"+elementName].append( text )
            else:
                logging.warning( _("Unexpected element: {} in record {}").format( element.tag, k ) )
    # end of _validateSystem

    def __str__( self ):
        """
        This method returns the string representation of a Bible versification system.
        
        @return: the name of a Bible object formatted as a string
        @rtype: string
        """
        result = "BibleVersificationSystemsConverter object"
        #if self.__title: result += ('\n' if result else '') + self.__title
        #if self.__version: result += ('\n' if result else '') + "Version:{}".format( self.__version )
        #if self.__date: result += ('\n' if result else '') + "Date:{}".format( self.__date )
        result += ('\n' if result else '') + "  Number of versification systems loaded = {}".format( len(self.__XMLSystems) )
        if 0: # Make it verbose
            for x in self.__XMLSystems:
                result += ('\n' if result else '') + " {}".format( x )
                title = self.__XMLSystems[x]["title"]
                if title: result += ('\n' if result else '') + "   {}".format( title )
                version = self.__XMLSystems[x]["version"]
                if version: result += ('\n    ' if result else '    ') + _("Version: {}").format( version )
                date = self.__XMLSystems[x]["date"]
                if date: result += ('\n    ' if result else '    ') + _("Last updated: {}").format( date )
                result += ('\n' if result else '') + "    Number of books = {}".format( len(self.__XMLSystems[x]["tree"]) )
                totalChapters, totalVerses, totalOmittedVerses, numCombinedVersesInstances, numRecorderedVersesInstances = 0, 0, 0, 0, 0
                for bookElement in self.__XMLSystems[x]["tree"]:
                    totalChapters += int( bookElement.find("numChapters").text )
                    for chapterElement in bookElement.findall("numVerses"):
                        totalVerses += int( chapterElement.text )
                        omittedVerses = chapterElement.get( "omittedVerses" )
                        if omittedVerses is not None: totalOmittedVerses += len(omittedVerses.split(','))
                        combinedVerses = chapterElement.get( "combinedVerses" )
                        if combinedVerses is not None: numCombinedVersesInstances += 1
                        reorderedVerses = chapterElement.get( "reorderedVerses" )
                        if reorderedVerses is not None: numRecorderedVersesInstances += 1
                if totalChapters: result += ('\n' if result else '') + "      Total chapters = {}".format( totalChapters )
                if totalVerses: result += ('\n' if result else '') + "      Total verses = {}".format( totalVerses )
                if totalOmittedVerses: result += ('\n' if result else '') + "      Total omitted verses = {}".format( totalOmittedVerses )
                if numCombinedVersesInstances: result += ('\n' if result else '') + "      Number of combined verses instances = {}".format( numCombinedVersesInstances )
                if numRecorderedVersesInstances: result += ('\n' if result else '') + "      Number of reordered verses instances = {}".format( numRecorderedVersesInstances )
        return result
    # end of __str__

    def __len__( self ):
        """ Returns the number of systems loaded. """
        return len( self.__XMLSystems )
    # end of __len__

    def importDataToPython( self ):
        """
        Loads (and pivots) the data (not including the header) into suitable Python containers to use in a Python program.
        """
        assert( self.__XMLSystems )
        if self.__DataDict: # We've already done an import/restructuring -- no need to repeat it
            return self.__DataDict

        # We'll create a number of dictionaries
        self.__DataDict = {}
        for versificationSystemCode in self.__XMLSystems.keys():
            #print( versificationSystemCode )
            # Make the data dictionary for this versification system
            chapterDataDict, omittedVersesDict, combinedVersesDict, reorderedVersesDict = OrderedDict(), OrderedDict(), {}, {}
            for bookElement in self.__XMLSystems[versificationSystemCode]["tree"]:
                BBB = bookElement.find("referenceAbbreviation").text
                #print( BBB )
                if not self.__BibleBooksCodes.isValidReferenceAbbreviation( BBB ):
                    logging.error( _("Unrecognized '{}' book abbreviation in '{}' versification system").format( BBB, versificationSystemCode ) )
                numChapters = bookElement.find("numChapters").text # This is a string

                # Check the chapter data against the expected chapters in the BibleBooksCodes data
                if numChapters not in self.__BibleBooksCodes.getExpectedChaptersList(BBB):
                    logging.info( _("Expected number of chapters for {} is {} but we got '{}' for {}").format(BBB, self.__BibleBooksCodes.getExpectedChaptersList(BBB), numChapters, versificationSystemCode ) )

                chapterData, omittedVersesData, combinedVersesData, reorderedVersesData = OrderedDict(), [], [], []
                chapterData['numChapters'] = numChapters
                for chapterElement in bookElement.findall("numVerses"):
                    chapter = chapterElement.get("chapter")
                    numVerses = chapterElement.text
                    assert( chapter not in chapterData )
                    chapterData[chapter] = numVerses
                    omittedVerses = chapterElement.get( "omittedVerses" )
                    if omittedVerses is not None:
                        bits = omittedVerses.split(',')
                        for bit in bits:
                            omittedVersesData.append( (chapter, bit,) )
                    combinedVerses = chapterElement.get( "combinedVerses" )
                    if combinedVerses is not None:
                        combinedVersesData.append( (chapter, combinedVerses,) )
                    reorderedVerses = chapterElement.get( "reorderedVerses" )
                    if reorderedVerses is not None:
                        reorderedVersesData.append( (chapter, reorderedVerses,) )
                # Save it by book reference abbreviation
                #assert( BBB not in bookData )
                #bookData[BBB] = (chapterData, omittedVersesData,)
                if BBB in chapterDataDict:
                    logging.error( _("Duplicate {} in {}").format( BBB, versificationSystemCode ) )
                chapterDataDict[BBB] = chapterData
                if BBB in omittedVersesDict:
                    logging.error( _("Duplicate omitted verse data for {} in {}").format( BBB, versificationSystemCode ) )
                if omittedVersesData: omittedVersesDict[BBB] = omittedVersesData
                if combinedVersesData: combinedVersesDict[BBB] = combinedVersesData
                if reorderedVersesData: reorderedVersesDict[BBB] = reorderedVersesData

            if Globals.strictCheckingFlag: # check for duplicates
                for checkSystemCode in self.__DataDict:
                    checkChapterDataDict, checkOmittedVersesDict, checkCombinedVersesDict, checkReorderedVersesDict = self.__DataDict[checkSystemCode]['CV'], self.__DataDict[checkSystemCode]['omitted'], self.__DataDict[checkSystemCode]['combined'], self.__DataDict[checkSystemCode]['reordered']
                    if checkChapterDataDict==chapterDataDict:
                        if checkOmittedVersesDict==omittedVersesDict:
                            logging.error( _("{} and {} versification systems are exactly identical").format( versificationSystemCode, checkSystemCode ) )
                        else: # only the omitted verse lists differ
                            logging.warning( _("{} and {} versification systems are mostly identical (omitted verse lists differ)").format( versificationSystemCode, checkSystemCode ) )
                    else: # check if one is the subset of the other
                        BBBcombinedSet = set( checkChapterDataDict.keys() ) or set( chapterDataDict.keys() )
                        different, numCommon = False, 0
                        for BBB in BBBcombinedSet:
                            if BBB in checkChapterDataDict and BBB in chapterDataDict: # This book is in both
                                numCommon += 1
                                if checkChapterDataDict[BBB] != chapterDataDict[BBB]: different = True
                        if not different:
                            different2, numCommon2 = False, 0
                            for BBB in BBBcombinedSet:
                                if BBB in checkOmittedVersesDict and BBB in omittedVersesDict: # This book is in both
                                    numCommon2 += 1
                                    if checkOmittedVersesDict[BBB] != omittedVersesDict[BBB]: different2 = True
                            if not different2:
                                logging.warning( _("The {} common books in {} ({}) and {} ({}) versification systems are exactly identical").format( numCommon, versificationSystemCode, len(chapterDataDict), checkSystemCode, len(checkChapterDataDict) ) )
                            else: # only the omitted verse lists differ
                                logging.warning( _("The {} common books in {} ({}) and {} ({}) versification systems are mostly identical (omitted verse lists differ)").format( numCommon, versificationSystemCode, len(chapterDataDict), checkSystemCode, len(checkChapterDataDict) ) )


            # Now put it into my dictionaries for easy access
            self.__DataDict[versificationSystemCode] = {'CV':chapterDataDict, 'omitted':omittedVersesDict, 'combined':combinedVersesDict, 'reordered':reorderedVersesDict }
        return self.__DataDict
    # end of importDataToPython

    def pickle( self, filepath=None ):
        """
        Writes the information tables to a .pickle file that can be easily loaded into a Python3 program.
        """
        import pickle

        assert( self.__XMLSystems )
        self.importDataToPython()
        assert( self.__DataDict )

        if not filepath:
            folder = os.path.join( self.__XMLFolder, "../", "DerivedFiles/" )
            if not os.path.exists( folder ): os.mkdir( folder )
            filepath = os.path.join( folder, self.__filenameBase + "_Tables.pickle" )
        if Globals.verbosityLevel > 1: print( _("Exporting to {}...").format( filepath ) )
        with open( filepath, 'wb' ) as pickleFile:
            pickle.dump( self.__DataDict, pickleFile )
    # end of pickle

    def exportDataToPython( self, filepath=None ):
        """
        Writes the information tables to a .py file that can be cut and pasted into a Python program.
        """
        def exportPythonDict( theFile, theDict, systemName, keyComment, fieldsComment ):
            """Exports theDict to theFile."""
            theFile.write( '  "{}": {{\n    # Key is{}\n    # Fields are:{}\n'.format( systemName, keyComment, fieldsComment ) )
            for dictKey in theDict.keys():
                theFile.write( '   {}:{},\n'.format( repr(dictKey), theDict[dictKey] ) )
            theFile.write( "  }}, # end of{} ({} entries)\n\n".format( systemName, len(theDict) ) )
        # end of exportPythonDict

        from datetime import datetime

        assert( self.__XMLSystems )
        self.importDataToPython()
        assert( self.__DataDict )

        if not filepath: filepath = os.path.join( self.__XMLFolder, "../", "DerivedFiles", self.__filenameBase + "_Tables.py" )
        if Globals.verbosityLevel > 1: print( _("Exporting to {}...").format( filepath ) )
        versificationSystemDict = self.importDataToPython()
        # Split into two dictionaries
        with open( filepath, 'wt' ) as myFile:
            myFile.write( "#{}\n#\n".format( filepath ) )
            myFile.write( "# This UTF-8 file was automatically generated by BibleVersificationSystems.py V{} on {}\n#\n".format( versionString, datetime.now() ) )
            #if self.__title: myFile.write( "#{}\n".format( self.__title ) )
            #if self.__version: myFile.write( "#  Version:{}\n".format( self.__version ) )
            #if self.__date: myFile.write( "#  Date:{}\n#\n".format( self.__date ) )
            myFile.write( "#  {}{} loaded from the original XML files.\n#\n\n".format( len(self.__XMLSystems), self.__treeTag ) )
            myFile.write( "from collections import OrderedDict\n\n" )
            myFile.write( "chapterVerseDict = {\n  # Key is versificationSystemName\n  # Fields are versificationSystem\n" )
            for systemName in versificationSystemDict:
                exportPythonDict( myFile, versificationSystemDict[systemName]['CV'], systemName, "BBB referenceAbbreviation", "tuples containing (\"numChapters\", numChapters) then (chapterNumber, numVerses)" )
            myFile.write( "}} # end of chapterVerseDict ({} systems)\n\n".format( len(versificationSystemDict) ) )
            myFile.write( "omittedVersesDict = {{\n  # Key is versificationSystemName\n  # Fields are omittedVersesSystem\n" )
            for systemName in versificationSystemDict:
                exportPythonDict( myFile, versificationSystemDict[systemName]['omitted'], systemName, "BBB referenceAbbreviation", "tuples containing (chapterNumber, omittedVerseNumber)" )
            myFile.write( "}} # end of omittedVersesDict ({} systems)\n\n".format( len(versificationSystemDict) ) )
            myFile.write( "combinedVersesDict = {{\n  # Key is versificationSystemName\n  # Fields are combinedVersesSystem\n" )
            for systemName in versificationSystemDict:
                exportPythonDict( myFile, versificationSystemDict[systemName]['combined'], systemName, "BBB referenceAbbreviation", "tuples containing (chapterNumber, omittedVerseNumber)" )
            myFile.write( "}} # end of combinedVersesDict ({} systems)\n\n".format( len(versificationSystemDict) ) )
            myFile.write( "reorderedVersesDict = {{\n  # Key is versificationSystemName\n  # Fields are reorderedVersesSystem\n" )
            for systemName in versificationSystemDict:
                exportPythonDict( myFile, versificationSystemDict[systemName]['reordered'], systemName, "BBB referenceAbbreviation", "tuples containing (chapterNumber, omittedVerseNumber)" )
            myFile.write( "}} # end of reorderedVersesDict ({} systems)\n\n".format( len(versificationSystemDict) ) )
    # end of exportDataToPython

    def exportDataToJSON( self, filepath=None ):
        """
        Writes the information tables to a .json file that can be easily loaded into a Java program.

        See http://en.wikipedia.org/wiki/JSON.
        """
        from datetime import datetime
        import json

        assert( self.__XMLSystems )
        self.importDataToPython()
        assert( self.__DataDict )

        if not filepath: filepath = os.path.join( self.__XMLFolder, "../", "DerivedFiles", self.__filenameBase + "_Tables.json" )
        if Globals.verbosityLevel > 1: print( _("Exporting to {}...").format( filepath ) )
        with open( filepath, 'wt' ) as myFile:
            #myFile.write( "#{}\n#\n".format( filepath ) ) # Not sure yet if these comment fields are allowed in JSON
            #myFile.write( "# This UTF-8 file was automatically generated by BibleVersificationSystems.py V{} on {}\n#\n".format( versionString, datetime.now() ) )
            #if self.__titleString: myFile.write( "#{} data\n".format( self.__titleString ) )
            #if self.__versionString: myFile.write( "#  Version:{}\n".format( self.__versionString ) )
            #if self.__dateString: myFile.write( "#  Date:{}\n#\n".format( self.__dateString ) )
            #myFile.write( "#  {}{} loaded from the original XML file.\n#\n\n".format( len(self.__XMLtree), self.__treeTag ) )
            json.dump( self.__DataDict, myFile, indent=2 )
            #myFile.write( "\n\n# end of{}".format( os.path.basename(filepath) ) )
    # end of exportDataToJSON

    def exportDataToC( self, filepath=None ):
        """
        Writes the information tables to a .h file that can be included in c and c++ programs.
        """
        def writeStructure( hFile, structName, structure ):
            """ Writes a typedef to the .h file. """
            hFile.write( "typedef struct{}EntryStruct {\n".format( structName ) )
            for declaration in structure.split(';'):
                adjDeclaration = declaration.strip()
                if adjDeclaration: hFile.write( "   {};\n".format( adjDeclaration ) )
            hFile.write( "}{}Entry;\n\n".format( structName ) )
        # end of writeStructure

        def exportPythonDict( cFile, theDict, dictName, structName, sortedBy, structure ):
            """ Exports theDict to the .h and .c files. """
            def convertEntry( entry ):
                """ Convert special characters in an entry... """
                result = ""
                if isinstance( entry, int ): result += str(entry)
                elif isinstance( entry, str): result += '"' + str(entry).replace('"','\\"') + '"'
                else:
                    for field in entry:
                        if result: result += ", " # Separate the fields
                        if field is None: result += '""'
                        elif isinstance( field, str): result += '"' + str(field).replace('"','\\"') + '"'
                        elif isinstance( field, int): result += str(field)
                        elif isinstance( field, tuple):
                            tupleResult = ""
                            for value in field:
                                if tupleResult: tupleResult += "," # Separate the fields (without a space)
                                tupleResult += convertEntry( value ) # recursive call
                            result += "{{} }".format( tupleResult )
                        else: logging.error( _("Cannot convert unknown field type '{}' in entry '{}'").format( field, entry ) )
                return result
            # end of convertEntry

            #for dictKey in theDict.keys(): # Have to iterate this :(
            #    fieldsCount = len( theDict[dictKey] ) + 1 # Add one since we include the key in the count
            #    break # We only check the first (random) entry we get
            fieldsCount = 2

            cFile.write( "const static{}\n{}[{}] = {\n  // Fields ({}) are{}\n  // Sorted by{}\n".format( structName, dictName, len(theDict), fieldsCount, structure, sortedBy ) )
            for dictKey in sorted(theDict.keys()):
                if isinstance( dictKey, str ):
                    cFile.write( "  {\"{}\",{}},\n".format( dictKey, convertEntry(theDict[dictKey]) ) )
                elif isinstance( dictKey, int ):
                    cFile.write( "  {{},{}},\n".format( dictKey, convertEntry(theDict[dictKey]) ) )
                else:
                    logging.error( _("Can't handle this type of data yet: {}").format( dictKey ) )
            cFile.write( "}; //{} ({} entries)\n\n".format( dictName, len(theDict) ) )
        # end of exportPythonDict

        def XXXexportPythonDict( theFile, theDict, dictName, structName, fieldsComment ):
            """Exports theDict to theFile."""
            def convertEntry( entry ):
                """Convert special characters in an entry..."""
                result = ""
                for field in entry if isinstance( entry, list) else entry.items():
                    #print( field )
                    if result: result += ", " # Separate the fields
                    if field is None: result += '""'
                    elif isinstance( field, str): result += '"' + str(field).replace('"','\\"') + '"'
                    elif isinstance( field, int): result += str(field)
                    elif isinstance( field, tuple):
                        tupleResult = ""
                        for tupleField in field:
                            #print( field, tupleField )
                            if tupleResult: tupleResult += "," # Separate the fields (without a space)
                            if tupleField is None: tupleResult += '""'
                            elif isinstance( tupleField, str): tupleResult += '"' + str(tupleField).replace('"','\\"') + '"'
                            elif isinstance( tupleField, int): tupleResult += str(tupleField)
                            else: logging.error( _("Cannot convert unknown tuplefield type '{}' in entry '{}' for {}").format( tupleField, entry, field ) )
                        result += tupleResult
                    else: logging.error( _("Cannot convert unknown field type '{}' in entry '{}'").format( field, entry ) )
                return result

            theFile.write( "static struct{}{}[{}] = {\n  // Fields are{}\n".format( structName, dictName, len(theDict), fieldsComment ) )
            for dictKey in sorted(theDict.keys()):
                if isinstance( dictKey, str ):
                    #print( dictKey, theDict[dictKey] )
                    theFile.write( "  {\"{}\",{}},\n".format( dictKey, convertEntry(theDict[dictKey]) ) )
                elif isinstance( dictKey, int ):
                    theFile.write( "  {{},{}},\n".format( dictKey, convertEntry(theDict[dictKey]) ) )
                else:
                    logging.error( _("Can't handle this type of key data yet: {}").format( dictKey ) )
            theFile.write( "}; //{} ({} entries)\n\n".format( dictName, len(theDict) ) )
        # end of XXXexportPythonDict

        from datetime import datetime

        assert( self.__XMLSystems )
        self.importDataToPython()
        assert( self.__DataDict )

        if not filepath: filepath = os.path.join( self.__XMLFolder, "../", "DerivedFiles", self.__filenameBase + "_Tables" )
        hFilepath = filepath + '.h'
        cFilepath = filepath + '.c'
        if Globals.verbosityLevel > 1: print( _("Exporting to {}...").format( cFilepath ) ) # Don't bother telling them about the .h file
        ifdefName = self.__filenameBase.upper() + "_Tables_h"

        with open( hFilepath, 'wt' ) as myHFile, open( cFilepath, 'wt' ) as myCFile:
            myHFile.write( "//{}\n//\n".format( hFilepath ) )
            myCFile.write( "//{}\n//\n".format( cFilepath ) )
            lines = "// This UTF-8 file was automatically generated by BibleVersificationSystems.py V{} on {}\n//\n".format( versionString, datetime.now() )
            myHFile.write( lines ); myCFile.write( lines )
            myCFile.write( "//  {}{} loaded from the original XML file.\n//\n\n".format( len(self.__XMLSystems), self.__treeTag ) )
            myHFile.write( "\n#ifndef{}\n#define{}\n\n".format( ifdefName, ifdefName ) )
            myCFile.write( '#include "{}"\n\n'.format( os.path.basename(hFilepath) ) )

            # This needs to be thought out better :(
            # Need to put all CV data for all books into an array
            #  and then have another level that points into it
            #    BBB, numChapters, startIndex
            raise Exception( "Sorry, this c export isn't working yet :(" )

            CHAR = "const unsigned char"
            BYTE = "const int"
            N1 = "CVCount"
            N2 = "CVCounts"
            N3 = "CVOmitted"
            N4 = "CVOmits"
            S1 = "{}* chapterNumberString;{}* numVersesString;".format(CHAR,CHAR)
            S2 = "{} referenceAbbreviation[3+1];{}Entry numVersesString[];".format(CHAR,N1)
            S3 = "{}* chapterNumberString;{}* verseNumberString;".format(CHAR,CHAR)
            S4 = "{} referenceAbbreviation[3+1];{}Entry numVersesString[];".format(CHAR,N3)
            writeStructure( myHFile, N1, S1 )
            writeStructure( myHFile, N2, S2 )
            writeStructure( myHFile, N3, S4 )
            writeStructure( myHFile, N4, S4 )
            writeStructure( myHFile, "table", "{}* systemName;{}Entry* systemCVCounts;{}Entry* systemOmittedVerses;".format(CHAR,N2,N4) ) # I'm not sure if I need one or two asterisks on those last two
                                                                                                        # They're supposed to be pointers to an array of structures
            myHFile.write( "#endif //{}\n\n".format( ifdefName ) )
            myHFile.write( "// end of{}".format( os.path.basename(hFilepath) ) )

            #myHFile.write( "static struct {struct char*, void*, void*} versificationSystemNames[{}] = {\n  // Fields are systemName, systemVersification, systemOmittedVerses\n".format( len(versificationSystemDict) ) )

            for systemName,systemInfo in self.__DataDict.items(): # Now write out the actual data into the .c file
                myCFile.write( "\n//{}\n".format( systemName ) )
                exportPythonDict( myCFile, systemInfo[0], systemName+"CVDict", N1+"Entry", "referenceAbbreviation", S1 )
                exportPythonDict( myCFile, systemInfo[1], systemName+"OmittedVersesDict", N2+"Entry", "indexNumber", S2 )

                break # Just do one for now
#            for systemName in self.__DataDict: # Now write out the actual data into the .c file
#                print( systemName )
#                myCFile.write( '  { "{}",{}_versificationSystem,{}_omittedVerses },\n'.format( systemName, systemName, systemName ) )
#            myCFile.write( "}; // versificationSystemNames ({} entries)\n\n".format( len(self.__DataDict) ) )
#            for systemName in self.__DataDict:
#                print( systemName )
#                myCFile.write( "#\n#{}\n".format( systemName ) )
#                exportPythonDict( myCFile, self.__DataDict[systemName][0], systemName+"_versificationSystem", "{struct char* stuff[]}", "tables containing referenceAbbreviation, (\"numChapters\", numChapters) then pairs of chapterNumber,numVerses" )
#                exportPythonDict( myCFile, self.__DataDict[systemName][1], systemName+"_omittedVerses", "{struct char* stuff[]}", "tables containing referenceAbbreviation then pairs of chapterNumber,omittedVerseNumber" )
#                exportPythonDict( myCFile, self.__DataDict[systemName][1], "omittedVersesDict", "{struct char* stuff[]}", "tables containing referenceAbbreviation then pairs of chapterNumber,omittedVerseNumber" )

            # Write out the final table of pointers to the above information
            myCFile.write( "\n// Pointers to above data\nconst static tableEntry bookOrderSystemTable[{}] = {\n".format( len(self.__DataDict) ) )
            for systemName in self.__DataDict: # Now write out the actual pointer data into the .c file
                myCFile.write( '  { "{}",{},{} },\n'.format( systemName, systemName+"CVDict", systemName+"OmittedVersesDict" ) )
            myCFile.write( "}; //{} entries\n\n".format( len(self.__DataDict) ) )
            myCFile.write( "// end of{}".format( os.path.basename(cFilepath) ) )
    # end of exportDataToC

    def obsoleteCheckVersificationSystem( self, thisSystemName, versificationSchemeToCheck, omittedVersesToCheck=None ):
        """
        Check the given versification scheme against all the loaded systems.
        Create a new versification file if it doesn't match any.
        """
        assert( self.__DataDict )
        assert( versificationSchemeToCheck )
        if omittedVersesToCheck is None: omittedVersesToCheck = {}

        matchedVersificationSystemCodes = []
        systemMatchCount, systemMismatchCount, allErrors, errorSummary = 0, 0, '', ''
        for versificationSystemCode in self.__DataDict: # Step through the various reference schemes
            #print( system )
            bookMismatchCount, chapterMismatchCount, verseMismatchCount, omittedVerseMismatchCount, theseErrors = 0, 0, 0, 0, ''
            CVData, OVData, CombVData, ReordVData = self.__DataDict[versificationSystemCode]

            # Check verses per chapter
            for BBB in versificationSchemeToCheck.keys():
                #print( BBB )
                if BBB in CVData:
                    for chapterToCheck,numVersesToCheck in versificationSchemeToCheck[BBB]:
                        if not isinstance(chapterToCheck,str): raise Exception( "Chapter programming error" )
                        if not isinstance(numVersesToCheck,str): raise Exception( "Verse programming error" )
                        if chapterToCheck in CVData[BBB]: # That chapter number is in our scheme
                            if CVData[BBB][chapterToCheck] != numVersesToCheck:
                                theseErrors += ("\n" if theseErrors else "") + "    " + _("Doesn't match '{}' system at {} {} verse {}").format( versificationSystemCode, BBB, chapterToCheck, numVersesToCheck )
                                if bookMismatchCount==0 and chapterMismatchCount==0 and verseMismatchCount==0: rememberedBBB, rememberedChapter, rememberedVerses1, rememberedVerses2 = BBB, chapterToCheck, CVData[BBB][chapterToCheck], numVersesToCheck
                                verseMismatchCount += 1
                        else: # Our scheme doesn't have that chapter number
                            theseErrors += ("\n" if theseErrors else "") + "    " + _("Doesn't match '{}' system at {} chapter {} ({} verses)").format( versificationSystemCode, BBB, chapterToCheck, numVersesToCheck )
                            chapterMismatchCount += 1
                else:
                    theseErrors += ("\n" if theseErrors else "") + "    " + _("Can't find {} bookcode in {}").format( BBB, versificationSystemCode )
                    bookMismatchCount += 1

            # Check omitted verses
            for BBB in omittedVersesToCheck.keys():
                if BBB in OVData:
                    if OVData[BBB] == omittedVersesToCheck[BBB]: continue # Perfect match for this book
                    for cv in omittedVersesToCheck[BBB]:
                        if cv not in OVData[BBB]:
                            theseErrors += ("\n" if theseErrors else "") + "   " + _("{}:{} not omitted in {} reference versification for {}").format( cv[0], cv[1], versificationSystemCode, BBB )
                            omittedVerseMismatchCount += 1
                    for cv in OVData[BBB]:
                        if cv not in omittedVersesToCheck[BBB]:
                            theseErrors += ("\n" if theseErrors else "") + "   " + _("{}:{} is omitted in {} reference versification for {}").format( cv[0], cv[1], versificationSystemCode, BBB )
                            omittedVerseMismatchCount += 1
                else: # We don't match
                    theseErrors += ("\n" if theseErrors else "") + "    " + _("No omitted verses for {} in {}").format( BBB, versificationSystemCode )
                    omittedVerseMismatchCount += len( omittedVersesToCheck[BBB] )

            if bookMismatchCount or chapterMismatchCount or verseMismatchCount or omittedVerseMismatchCount:
                if omittedVersesToCheck:
                    thisError = "    " + _("Doesn't match '{}' system ({} book mismatches, {} chapter mismatches, {} verse mismatches, {} omitted-verse mismatches)").format( versificationSystemCode, bookMismatchCount, chapterMismatchCount, verseMismatchCount,omittedVerseMismatchCount )
                else:
                    thisError = "    " + _("Doesn't match '{}' system ({} book mismatches, {} chapter mismatches, {} verse mismatches)").format( versificationSystemCode, bookMismatchCount, chapterMismatchCount, verseMismatchCount )
                    if bookMismatchCount==0 and chapterMismatchCount==0 and verseMismatchCount==1: thisError += "\n      " + _("{} {} chapter {} had {} verses not {}").format(thisSystemName, rememberedBBB, rememberedChapter, rememberedVerses2, rememberedVerses1)
                theseErrors += ("\n" if theseErrors else "") + thisError
                errorSummary += ("\n" if errorSummary else "") + thisError
                systemMismatchCount += 1
            else:
                #print( "  Matches '{}' system".format( versificationSystemCode ) )
                systemMatchCount += 1
                matchedVersificationSystemCodes.append( versificationSystemCode )
            if Globals.commandLineOptions.debug and chapterMismatchCount==0 and 0<verseMismatchCount<8 and omittedVerseMismatchCount<10: print( theseErrors )
            allErrors += ("\n" if allErrors else "") + theseErrors

        if systemMatchCount:
            if systemMatchCount == 1: # What we hope for
                print( "  " + _("Matched {} versification (with these {} books)").format( matchedVersificationSystemCodes[0], len(versificationSchemeToCheck) ) )
                if Globals.commandLineOptions.debug: print( errorSummary )
            else:
                print( "  " + _("Matched {} versification system(s): {} (with these {} books)").format( systemMatchCount, matchedVersificationSystemCodes, len(versificationSchemeToCheck) ) )
                if Globals.commandLineOptions.debug: print( errorSummary )
        else:
            print( "  " + _("Mismatched {} versification systems (with these {} books)").format( systemMismatchCount, len(versificationSchemeToCheck) ) )
            if Globals.commandLineOptions.debug: print( allErrors )
            else: print( errorSummary)

        if Globals.commandLineOptions.export and not systemMatchCount: # Write a new file
            outputFilepath = os.path.join( os.path.dirname(__file__), "DataFiles/", "ScrapedFiles/", "BibleVersificationSystem_"+thisSystemName + ".xml" )
            if Globals.verbosityLevel > 1: print( _("Writing {} books to {}...").format( len(versificationSchemeToCheck), outputFilepath ) )
            if omittedVersesToCheck:
                totalOmittedVerses = 0
                for BBB in omittedVersesToCheck.keys():
                    totalOmittedVerses += len( omittedVersesToCheck[BBB] )
                if Globals.verbosityLevel > 2: print( "  " + _("Have {} omitted verses for {} books").format( totalOmittedVerses, len(omittedVersesToCheck) ) )
            with open( outputFilepath, 'wt' ) as myFile:
                for BBB in versificationSchemeToCheck:
                    myFile.write( "  <BibleBookVersification>\n" )
                    myFile.write( "    <nameEnglish>{}</nameEnglish>\n".format( self.__BibleBooksCodesDict[BBB][9] ) ) # the book name from the BibleBooksCodes.xml file
                    myFile.write( "    <referenceAbbreviation>{}</referenceAbbreviation>\n".format( BBB ) )
                    myFile.write( "    <numChapters>{}</numChapters>\n".format( len(versificationSchemeToCheck[BBB]) ) )
                    for c,numV in versificationSchemeToCheck[BBB]:
                        omittedVerseString = ''
                        if BBB in omittedVersesToCheck:
                            for oc,ov in omittedVersesToCheck[BBB]:
                                if oc == c: # It's this chapter
                                    omittedVerseString += (',' if omittedVerseString else '') + str(ov)
                        if omittedVerseString:
                            if Globals.verbosityLevel > 3 or Globals.commandLineOptions.debug: print( '   ', BBB, c+':'+omittedVerseString )
                            myFile.write( '    <numVerses chapter="{}" omittedVerses="{}">{}</numVerses>\n'.format( c, omittedVerseString, numV ) )
                        else:
                            myFile.write( '    <numVerses chapter="{}">{}</numVerses>\n'.format( c, numV ) )
                    myFile.write( "  </BibleBookVersification>\n" )
                myFile.write( "\n</BibleVersificationSystem>" )
    # end of obsoleteCheckVersificationSystem
# end of BibleVersificationSystemsConverter class


def main():
    """
    Main program to handle command line parameters and then run what they want.
    """
    # Handle command line parameters
    from optparse import OptionParser
    parser = OptionParser( version="v{}".format( versionString ) )
    parser.add_option("-e", "--export", action="store_true", dest="export", default=False, help="export the XML files to .py and .h tables suitable for directly including into other programs")
    Globals.addStandardOptionsAndProcess( parser )

    if Globals.verbosityLevel > 1: print( "{} V{}".format( progName, versionString ) )

    bvsc = BibleVersificationSystemsConverter().loadSystems() # Load the XML
    if Globals.commandLineOptions.export:
        bvsc.pickle() # Produce the .pickle file
        bvsc.exportDataToPython() # Produce the .py tables
        bvsc.exportDataToJSON() # Produce a json output file
        bvsc.exportDataToC() # Produce the .h and .c tables

    else: # Must be demo mode
        print( bvsc ) # Just print a summary
# end of main

if __name__ == '__main__':
    main()
# end of BibleVersificationSystemsConverter.py