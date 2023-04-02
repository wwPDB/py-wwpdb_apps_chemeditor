##
# File:  Search.py
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

import os
import sys
from operator import itemgetter

from wwpdb.apps.chemeditor.webapp.ChemEditorBase import ChemEditorBase
from wwpdb.io.file.mmCIFUtil import mmCIFUtil


class Search(ChemEditorBase):
    """
    """
    def __init__(self, reqObj=None, verbose=False, log=sys.stderr):
        super(Search, self).__init__(reqObj=reqObj, verbose=verbose, log=log)
        #
        self.__standardComponents = ("ALA", "ARG", "ASN", "ASP", "CYS", "GLU", "GLN", "GLY", "HIS", "ILE", "LEU", "LYS", "MET", "PHE",
                                     "PRO", "SER", "THR", "TRP", "TYR", "VAL", "A", "C", "G", "T", "U", "DA", "DC", "DG", "DT", "DU")
        #
        self.__idMap = {}
        self.__idList = []

    def GetResult(self):
        self._getInputCifData(os.path.join(self._sessionPath, "in.cif"))
        self._updateCompCif(self._sessionPath, "in.cif")
        self.__search()
        return self.__returnData()

    def __search(self):
        filePath = os.path.join(self._sessionPath, "in.cif")
        if not os.access(filePath, os.R_OK):
            return
        #
        exact_flag = self._reqObj.getValue("exact")
        if exact_flag == "yes":
            self.__runSearchScript("'prefilter|strict|skip-h|exact'")
        else:
            self.__runSearchScript("'prefilter|relaxedstereo|skip-h|exact'")
            self.__runSearchScript("'prefilter|relaxed|skip-h|allowextra'")
            self.__runSearchScript("'prefilter|relaxed|skip-h|close'")
        #

    def __runSearchScript(self, option):
        self._runMatchComp(self._sessionPath, "in.cif", "search_result", option)
        self.__parseSearchResult()

    def __parseSearchResult(self):
        filePath = os.path.join(self._sessionPath, "search_result")
        if not os.access(filePath, os.R_OK):
            return
        #
        f = open(filePath, "r")
        data = f.read()
        f.close()
        #
        llist = data.split("\n")
        for line in llist[1:]:
            if not line:
                continue
            #
            vlist = line.split("\t")
            if len(vlist) != 8:
                continue
            #
            if vlist[4] in self.__idMap:
                continue
            #
            diff = int(vlist[7]) - int(vlist[3])
            if diff > 3:
                continue
            #
            if not self.__isValidId(vlist[4]):
                continue
            #
            self.__idMap[vlist[4]] = "yes"
            standard = 1
            if vlist[4] in self.__standardComponents:
                standard = 0
            #
            self.__idList.append((vlist[4], diff, standard))
        #

    def __isValidId(self, ccId):
        filePath = self.getSandBoxFilePath(ccId)
        if (not filePath) or (not os.access(filePath, os.F_OK)):
            return False
        #
        cifObj = mmCIFUtil(filePath=filePath)
        status = cifObj.GetSingleValue("chem_comp", "pdbx_release_status").upper()
        if status == "OBS":
            return False
        #
        return True

    def __returnData(self):
        data = ""
        if self.__idList:
            if len(self.__idList) > 1:
                self.__idList.sort(key=itemgetter(1, 2))
            #
            number = len(self.__idList)
            if number > 15:
                number = 15
            #
            for i in range(0, number):
                if data:
                    data += "\n"
                #
                data += self.__idList[i][0]
            #
        #
        return data
