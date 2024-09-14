##
# File:  AtomMatch.py
# Date:  27-Feb-2013
# Updates:
##
"""

This software was developed as part of the World Wide Protein Data Bank
Common Deposition and Annotation System Project

Copyright (c) 2012 wwPDB

This software is provided under a Creative Commons Attribution 3.0 Unported
License described at http://creativecommons.org/licenses/by/3.0/.

"""
__docformat__ = "restructuredtext en"
__author__ = "Zukang Feng"
__email__ = "zfeng@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.07"

import os
import sys

from wwpdb.apps.chemeditor.webapp.ChemEditorBase import ChemEditorBase


class AtomMatch(ChemEditorBase):
    """ """

    def __init__(self, reqObj=None, verbose=False, log=sys.stderr):
        super(AtomMatch, self).__init__(reqObj=reqObj, verbose=verbose, log=log)
        #
        self.__inputFilePath = os.path.join(self._sessionPath, "in.cif")
        self.__matchResultPath = os.path.join(self._sessionPath, "match_result")

    def GetResult(self):
        self._getInputCifData(self.__inputFilePath)
        self.__runAtomMatchScript()
        return self.__returnData()

    def __runAtomMatchScript(self):
        if not os.access(self.__inputFilePath, os.R_OK):
            return
        #
        ccFilePath = self._getCcFilePathWithWebRequstId()
        if not ccFilePath:
            return
        #
        reverse_flag = self._reqObj.getValue("reverse")
        self._removeFile(self.__matchResultPath)
        #
        cmd = "cd " + self._sessionPath + " ; " + self._annotBashSetting()
        if reverse_flag == "yes":
            cmd += " ${BINPATH}/GetAtomMatch -first in.cif -second " + ccFilePath
        else:
            cmd += " ${BINPATH}/GetAtomMatch -first " + ccFilePath + " -second in.cif"
        #
        cmd += " -output match_result -log logfile > _match_log 2>&1 ; "
        self._runCmd(cmd)

    def __returnData(self):
        if not os.access(self.__matchResultPath, os.R_OK):
            return ""
        #
        f = open(self.__matchResultPath, "r")
        data = f.read()
        f.close()
        #
        return data
