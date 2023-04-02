##
# File:  UpdateLigand.py
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

from mmcif.io.PdbxReader import PdbxReader
from mmcif.io.PdbxWriter import PdbxWriter
from wwpdb.apps.chemeditor.webapp.ChemEditorBase import ChemEditorBase
from wwpdb.io.file.mmCIFUtil import mmCIFUtil


class UpdateLigand(ChemEditorBase):
    """
    """
    def __init__(self, reqObj=None, verbose=False, log=sys.stderr):
        super(UpdateLigand, self).__init__(reqObj=reqObj, verbose=verbose, log=log)
        #
        self.__pdbId = str(self._reqObj.getValue("pdbid")).upper()
        self.__annotator = str(self._reqObj.getValue("annotator"))
        self.__processing_site = str(self._reqObj.getValue("processingsite"))
        if (not self.__processing_site) or (self.__processing_site == "null") or (self.__processing_site == "NULL"):
            self.__processing_site = self._cI.get("SITE_NAME").upper()
        #
        self.__instanceid = str(self._reqObj.getValue("instanceid"))
        self.__cclinkFile = ""

    def GetResult(self):
        self._getInputCifData(os.path.join(self._sessionPath, "in.cif"))
        self.__getCCLinkFile()
        self._updateCompCif(self._sessionPath, "in.cif")
        self.__updateDefaultValue()
        return self.__returnData()

    def __getCCLinkFile(self):
        topPath = str(self._reqObj.getValue("TopSessionPath"))
        p_sessionId = str(self._reqObj.getValue("parent_sessionid"))
        identifier = str(self._reqObj.getValue("identifier"))
        if (not topPath) or (not p_sessionId) or (not identifier):
            return
        #
        identifierList = []
        identifierList.append(identifier)
        identifierList.append(identifier.upper())
        identifierList.append(identifier.lower())
        for Id in identifierList:
            filename = os.path.join(topPath, "sessions", p_sessionId, Id + "-cc-link.cif")
            if os.access(filename, os.R_OK):
                self.__cclinkFile = filename
                break
            #
        #
        if (not self.__instanceid) or (not self.__cclinkFile):
            return
        #
        cmd = "cd " + self._sessionPath + " ; " + self._annotBashSetting() \
            + " ${BINPATH}/FindMissingCoordinate -comp in.cif -cclink " + self.__cclinkFile \
            + " -instanceid " + self.__instanceid + " -log merge_log > _merge_log 2>&1 ; "
        self._runCmd(cmd)

    def __updateDefaultValue(self):
        filePath = os.path.join(self._sessionPath, "in.cif")
        if not os.access(filePath, os.R_OK):
            return
        #
        myDataList = []
        ifh = open(filePath, "r")
        pRd = PdbxReader(ifh)
        pRd.read(myDataList)
        ifh.close()
        #
        myBlock = myDataList[0]
        compCat = myBlock.getObj("chem_comp")
        ccType = compCat.getValue("type", 0)
        if (ccType == "?") or (ccType == "."):
            compCat.setValue("NON-POLYMER", "type", 0)
        #
        pdbxType = compCat.getValue("pdbx_type", 0)
        if (pdbxType == "?") or (pdbxType == "."):
            compCat.setValue("HETAIN", "pdbx_type", 0)
        #
        ccId = compCat.getValue("id", 0)
        compCat.setValue(ccId, "three_letter_code", 0)
        synonyms = self.__get_synonyms(ccId)
        if synonyms:
            compCat.setValue(synonyms, "pdbx_synonyms", 0)
        #
        if self.__pdbId:
            pdbId = compCat.getValue("pdbx_model_coordinates_db_code", 0)
            if (pdbId == "?") or (pdbId == "."):
                compCat.setValue(self.__pdbId, "pdbx_model_coordinates_db_code", 0)
            #
        #
        if self.__processing_site:
            site = compCat.getValue("pdbx_processing_site", 0)
            if (site == "?") or (site == ".") or (site == "ChemCompOB"):
                compCat.setValue(self.__processing_site, "pdbx_processing_site", 0)
            #
            auditCat = myBlock.getObj("pdbx_chem_comp_audit")
            site = auditCat.getValue("processing_site", 0)
            if (site == "?") or (site == ".") or (site == "ChemCompOB"):
                auditCat.setValue(self.__processing_site, "processing_site", 0)
            #
        #
        if self.__annotator:
            anno = auditCat.getValue("annotator", 0)
            if (anno == "?") or (anno == "."):
                auditCat.setValue(self.__annotator, "annotator", 0)
            #
        #
        ofh = open(filePath, "w")
        pdbxW = PdbxWriter(ofh)
        pdbxW.write(myDataList)
        ofh.close()

    def __get_synonyms(self, ccId):
        filePath = self.getSandBoxFilePath(ccId)
        if (not filePath) or (not os.access(filePath, os.F_OK)):
            return ""
        #
        cifObj = mmCIFUtil(filePath=filePath)
        return cifObj.GetSingleValue("chem_comp", "pdbx_synonyms")

    def __returnData(self):
        filePath = os.path.join(self._sessionPath, "in.cif")
        if not os.access(filePath, os.R_OK):
            return ""
        #
        f = open(filePath, "r")
        data = f.read()
        f.close()
        return data
