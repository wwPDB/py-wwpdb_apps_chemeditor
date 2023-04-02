##
# File:  GetLigand.py
# Date:  26-Feb-2013
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

import sys

from wwpdb.apps.chemeditor.webapp.ChemEditorBase import ChemEditorBase
from wwpdb.io.file.mmCIFUtil import mmCIFUtil


class GetLigand(ChemEditorBase):
    """
    """
    def __init__(self, reqObj=None, verbose=False, log=sys.stderr):
        super(GetLigand, self).__init__(reqObj=reqObj, verbose=verbose, log=log)
        #
        self.__ccFilePath = self._getCcFilePathWithWebRequstId()
        self.__cifObj = None

    def GetCifData(self):
        """
        """
        if not self.__ccFilePath:
            return ""
        #
        ifh = open(self.__ccFilePath, "r")
        data = ifh.read()
        ifh.close()
        return data

    def GetReleaseStatus(self):
        """
        """
        self.__getCifObj()
        if not self.__cifObj:
            return ""
        #
        return self.__cifObj.GetSingleValue("chem_comp", "pdbx_release_status")

    def GetOneLetterCode(self):
        """
        """
        self.__getCifObj()
        if not self.__cifObj:
            return ""
        #
        return self.__cifObj.GetSingleValue("chem_comp", "one_letter_code")

    def __getCifObj(self):
        """
        """
        if self.__cifObj:
            return
        #
        if not self.__ccFilePath:
            return
        #
        self.__cifObj = mmCIFUtil(filePath=self.__ccFilePath)
