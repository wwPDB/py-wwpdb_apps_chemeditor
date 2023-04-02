##
# File:  Enumeration.py
# Date:  29-Aug-2020
# Updates:
##
"""

This software was developed as part of the World Wide Protein Data Bank
Common Deposition and Annotation System Project

Copyright (c) 2020 wwPDB

This software is provided under a Creative Commons Attribution 3.0 Unported
License described at http://creativecommons.org/licenses/by/3.0/.

"""
__docformat__ = "restructuredtext en"
__author__ = "Zukang Feng"
__email__ = "zfeng@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.07"

import json
import os
import sys
import traceback

from wwpdb.apps.chemeditor.webapp.ChemEditorBase import ChemEditorBase


class Enumeration(ChemEditorBase):
    """  Class handle CVS commit to chemical component dictionary
    """
    def __init__(self, reqObj=None, verbose=False, log=sys.stderr):
        super(Enumeration, self).__init__(reqObj=reqObj, verbose=verbose, log=log)
        self.__cif_items = str(self._reqObj.getValue("cif_items"))

    def get(self):
        """  Get Enumeration values
        """
        __cD = {}
        if not self.__cif_items:
            __cD["errorflag"] = True
            __cD["errortext"] = "Missing cif_items values."
        else:
            myD = self.__getEnumeration()
            if not myD:
                __cD["errorflag"] = True
                __cD["errortext"] = "Get Enumeration values failed."
            else:
                __cD = myD
            #
        #
        return __cD

    def __getEnumeration(self):
        """ Run getting Enumeration program
        """
        jsonFilePath = os.path.join(self._sessionPath, "enumeration.json")
        self._removeFile(jsonFilePath)
        #
        cmd = "cd " + self._sessionPath + " ; " + self._annotBashSetting() + " ${BINPATH}/GetEnumeration_json -input " + self.__cif_items \
            + " -output enumeration.json > get_enumeration.log 2>&1 ; "
        self._runCmd(cmd)
        #
        retD = {}
        if os.access(jsonFilePath, os.R_OK):
            try:
                with open(jsonFilePath) as DATA:
                    retD = json.load(DATA)
                #
            except:  # noqa: E722 pylint: disable=bare-except
                if (self._verbose):
                    traceback.print_exc(file=self._lfh)
                #
                retD = {}
            #
        #
        return retD
