##
# File:  ChemEditorBase.py
# Date:  11-Jul-2019
# Updates:
##
"""

This software was developed as part of the World Wide Protein Data Bank
Common Deposition and Annotation System Project

Copyright (c) 2013 wwPDB

This software is provided under a Creative Commons Attribution 3.0 Unported
License described at http://creativecommons.org/licenses/by/3.0/.

"""
__docformat__ = "restructuredtext en"
__author__    = "Zukang Feng"
__email__     = "zfeng@rcsb.rutgers.edu"
__license__   = "Creative Commons Attribution 3.0 Unported"
__version__   = "V0.07"

import os,sys,traceback

from wwpdb.io.cvs.CvsAdmin import CvsSandBoxAdmin
from wwpdb.utils.config.ConfigInfo import ConfigInfo


class ChemEditorBase(object):
    """  Class handle various system and C++ applications setting. 
    """
    def __init__(self, reqObj = None, verbose = False, log = sys.stderr):
        self._verbose = verbose
        self._lfh = log
        self._reqObj = reqObj
        self._sObj = None
        self._sessionId = None
        self._sessionPath = None
        self._rltvSessionPath = None
        self.__siteId = str(self._reqObj.getValue("WWPDB_SITE_ID"))
        self._cI = ConfigInfo(self.__siteId)
        self.__sbTopPath = self._cI.get("SITE_REFDATA_TOP_CVS_SB_PATH")     # "/wwpdb_da/da_top/reference/components"
        self._ccProjectName = self._cI.get("SITE_REFDATA_PROJ_NAME_CC")    # "ligand-dict-v3"
        self._ccPath = os.path.join(self.__sbTopPath, self._ccProjectName)
        #
        self.__getSession()
        #
        self._cvsAdmin = self.__setupCvs()

    def getSandBoxFilePath(self, ccId):
        """ Return full sandbox chemical component file path 
        """
        filePath = os.path.join(self._ccPath, ccId[0], ccId, ccId + ".cif")
        self._lfh.write("enter ChemEditorBase.getSandBoxFilePath for ccId=%s filePath=%s\n" % (ccId, filePath))
        if os.access(filePath, os.F_OK):
            return filePath
        #
        self._lfh.write("ChemEditorBase.getSandBoxFilePath running checkOut\n")
        self._cvsAdmin.checkOut(os.path.join(self._ccProjectName, ccId[0], ccId))
        #self._cvsAdmin.cleanup()
        #
        if os.access(filePath, os.F_OK):
            return filePath
        #
        return ""

    def _getCcFilePathWithWebRequstId(self):
        """
        """
        ccId =  str(self._reqObj.getValue("id"))
        if not ccId:
            return ""
        #
        return self.getSandBoxFilePath(ccId)

    def _annotBashSetting(self):
        """
        """
        setting = " RCSBROOT=" + self._cI.get("SITE_ANNOT_TOOLS_PATH") + "; export RCSBROOT; " \
                + " COMP_PATH=" + self._cI.get("SITE_CC_CVS_PATH") + "; export COMP_PATH; " \
                + " BINPATH=${RCSBROOT}/bin; export BINPATH; "
        return setting;

    def _ccToolsBashSetting(self):
        """
        """
        setting = " CC_TOOLS=" + os.path.join(self._cI.get("SITE_CC_APPS_PATH"), "bin") + "; export CC_TOOLS; " \
                + " OE_DIR=" + self._cI.get("SITE_CC_OE_DIR") + "; export OE_DIR; " \
                + " OE_LICENSE=" + self._cI.get("SITE_CC_OE_LICENSE") + "; export OE_LICENSE; " \
                + " ACD_DIR=" + self._cI.get("SITE_CC_ACD_DIR") + "; export ACD_DIR; " \
                + " CACTVS_DIR=" + self._cI.get("SITE_CC_CACTVS_DIR") + "; export CACTVS_DIR; " \
                + " CORINA_DIR=" + os.path.join(self._cI.get("SITE_CC_CORINA_DIR"), "bin")  + "; export CORINA_DIR; " \
                + " BABEL_DIR="  + self._cI.get("SITE_CC_BABEL_DIR") + "; export BABEL_DIR; " \
                + " BABEL_DATADIR=" + self._cI.get("SITE_CC_BABEL_DATADIR") + "; export BABEL_DATADIR; " \
                + " INCHI_DIR=" + self._cI.get("SITE_CC_INCHI_DIR") + "; export INCHI_DIR; " \
                + " LD_LIBRARY_PATH=" + self._cI.get("SITE_CC_BABEL_LIB") + ":" + os.path.join(self._cI.get("SITE_LOCAL_APPS_PATH"), "lib") + ":" \
                + self._cI.get("SITE_CC_ACD_DIR") + "; export LD_LIBRARY_PATH; "
        return setting

    def _mmcifDictBashSetting(self):
        """
        """
        dictInfo = self._cI.get("SITE_PDBX_DICTIONARY_NAME_DICT")
        setting = " PDBX_DICT_PATH=" + self._cI.get("SITE_PDBX_DICT_PATH") + "; export PDBX_DICT_PATH; " \
                + " DICT_NAME=" + dictInfo["ARCHIVE_NEXT"] + "; DICT_NAME; " \
                + " DICT_CIF_FILE=${PDBX_DICT_PATH}/${DICT_NAME}.dic; export DICT_CIF_FILE; " \
                + " DICT_SDB_FILE=${PDBX_DICT_PATH}/${DICT_NAME}.sdb; export DICT_SDB_FILE; " \
                + " DICT_ODB_FILE=${PDBX_DICT_PATH}/${DICT_NAME}.odb; export DICT_ODB_FILE; "
        return setting

    def _ccDictBashSetting(self):
        """
        """
        setting = " CC_DICT=" + self._cI.get("SITE_CC_DICT_PATH") + "; export CC_DICT; " \
                + " CC_IDX_FILE=${CC_DICT}/Components-all-v3-r4.idx; export CC_IDX_FILE; " \
                + " CC_SDB_FILE=${CC_DICT}/Components-all-v3.sdb; export CC_SDB_FILE; "
        return setting

    def _runCmd(self, cmd):
        """
        """
        self._lfh.write("running cmd=%s\n" % cmd)
        os.system(cmd)

    def _removeFile(self, filePath):
        """
        """
        if os.access(filePath, os.R_OK):
            os.remove(filePath)
        #

    def _updateCompCif(self, workingPath, inFile):
        """
        """
        inputFilePath = os.path.join(workingPath, inFile)
        if not os.access(inputFilePath, os.R_OK):
            return
        #
        outputFilePath = os.path.join(workingPath, "out.cif")
        self._removeFile(outputFilePath)
        #
        self._runCmd(self.__getAnnotateCompCmd(workingPath, inFile, "out.cif"))
        #
        if os.access(outputFilePath, os.R_OK):
            try:
                os.rename(outputFilePath, inputFilePath)
            except:
                self._removeFile(inputFilePath)
                os.rename(outputFilePath, inputFilePath)
            #
        #

    def _runMatchComp(self, workingPath, inFile, outFile, option):
        """
        """
        inputFilePath = os.path.join(workingPath, inFile)
        if not os.access(inputFilePath, os.R_OK):
            return
        #
        outputFilePath = os.path.join(workingPath, outFile)
        self._removeFile(outputFilePath)
        #
        cmd = "cd " + workingPath + " ; " + self._ccToolsBashSetting() + self._ccDictBashSetting() \
            + " ${CC_TOOLS}/matchComp -i " + inFile + " -lib ${CC_SDB_FILE} -index ${CC_IDX_FILE} -type structure -o " \
            + outFile + " -op " + option + " > _matchComp_log 2>&1 ; "
        #
        self._runCmd(cmd)

    def _getInputCifData(self, filePath):
        """
        """
        cifData = self._reqObj.getValue("cif")
        ofh = open(filePath, "w")
        ofh.write(cifData + "\n")
        ofh.close()

    def __getSession(self):
        """ Join existing session or create new session as required.
        """
        #
        self._sObj = self._reqObj.newSessionObj()
        self._sessionId = self._sObj.getId()
        self._sessionPath = self._sObj.getPath()
        self._rltvSessionPath = self._sObj.getRelativePath()
        if (self._verbose):
            self._lfh.write("------------------------------------------------------\n")                    
            self._lfh.write("+ChemEditorBase.__getSession() - creating/joining session %s\n" % self._sessionId)
            self._lfh.write("+ChemEditorBase.__getSession() - session path %s\n" % self._sessionPath)
        #

    def __setupCvs(self):
        """ Assign site specific chemical reference data CVS repository details
        """
        cvsRepositoryHost = self._cI.get("SITE_REFDATA_CVS_HOST")
        cvsRepositoryPath = self._cI.get("SITE_REFDATA_CVS_PATH")
        cvs = CvsSandBoxAdmin(tmpPath = self._sessionPath, verbose = self._verbose, log = self._lfh)
        cvs.setRepositoryPath(host=cvsRepositoryHost, path=cvsRepositoryPath)
        cvs.setAuthInfo(user="liganon3", password="lig1234")
        cvs.setSandBoxTopPath(self.__sbTopPath)
        return cvs

    def __getAnnotateCompCmd(self, workingPath, inFile, outFile):
        """
        """
        cmd = "cd " + workingPath + " ; " + self._ccToolsBashSetting() + " ${CC_TOOLS}/annotateComp -vv -i " + inFile \
            + " -op 'stereo-cactvs|aro-cactvs|descriptor-oe|descriptor-cactvs|descriptor-inchi|name-oe|name-acd|xyz-ideal-corina|xyz-model-h-oe|rename|fix' " \
            + " -o " + outFile + " > _comp_log 2>&1 ; "
        return cmd
