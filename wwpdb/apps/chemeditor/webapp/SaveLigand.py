##
# File:  SaveLigand.py
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
import shutil
import sys

from wwpdb.apps.ccmodule.io.ChemCompAssignDataStore import ChemCompAssignDataStore
from wwpdb.apps.ccmodule.reports.ChemCompAlignImageGenerator import ChemCompAlignImageGenerator
from wwpdb.apps.chemeditor.webapp.ChemEditorBase import ChemEditorBase


class SaveLigand(ChemEditorBase):
    """
    """
    def __init__(self, reqObj=None, verbose=False, log=sys.stderr):
        super(SaveLigand, self).__init__(reqObj=reqObj, verbose=verbose, log=log)
        self.__instanceId = str(self._reqObj.getValue("instanceid"))
        self.__subpath = str(self._reqObj.getValue("subpath"))
        self.__filextension = str(self._reqObj.getValue("filextension"))
        if not self.__filextension:
            self.__filextension = "cif"
        #
        self.__genimageflag = str(self._reqObj.getValue("genimageflag"))
        self.__sessionPath = self._sessionPath
        if self.__subpath:
            self.__sessionPath = os.path.join(self._sessionPath, self.__subpath)
        #

    def GetResult(self):
        instanceFilePath = os.path.join(self.__sessionPath, self.__instanceId, self.__instanceId + "." + self.__filextension)
        if not os.access(instanceFilePath, os.R_OK):
            return ""
        self._getInputCifData(os.path.join(self.__sessionPath, self.__instanceId, "in.cif"))
        self._updateCompCif(os.path.join(self.__sessionPath, self.__instanceId), "in.cif")
        #
        updatedFilePath = os.path.join(self.__sessionPath, self.__instanceId, "in.cif")
        if os.access(updatedFilePath, os.R_OK):
            try:
                os.rename(updatedFilePath, instanceFilePath)
            except:  # noqa: E722 pylint: disable=bare-except
                self._removeFile(instanceFilePath)
                os.rename(updatedFilePath, instanceFilePath)
            #
        #
        self.__updateImage(self.__instanceId)
        related_instanceids = str(self._reqObj.getValue("related_instanceids"))
        if related_instanceids:
            relatedList = related_instanceids.split(",")
            for relatedId in relatedList:
                relatedFilePath = os.path.join(self.__sessionPath, relatedId, relatedId + "." + self.__filextension)
                if not os.access(relatedFilePath, os.R_OK):
                    continue
                #
                shutil.copyfile(instanceFilePath, relatedFilePath)
                self.__updateImage(relatedId)
            #
        #
        return "successful"

    def __updateImage(self, instanceId):
        if self.__genimageflag != "yes":
            return
        #
        self._reqObj.setValue("SessionsPath", self._cICommon.get_site_web_apps_sessions_path())
        ccAssignDataStore = ChemCompAssignDataStore(self._reqObj, verbose=self._verbose, log=self._lfh)
        mtchL = ccAssignDataStore.getTopHitsList(instanceId)
        HitList = []
        for tupL in mtchL:
            HitList.append(tupL[0])
        #
        chemCompFilePathAbs = os.path.join(self.__sessionPath, instanceId, instanceId + "." + self.__filextension)
        ccaig = ChemCompAlignImageGenerator(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        ccaig.generateImages(instId=instanceId, instFile=chemCompFilePathAbs, hitList=HitList)
