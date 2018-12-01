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
__author__    = "Zukang Feng"
__email__     = "zfeng@rcsb.rutgers.edu"
__license__   = "Creative Commons Attribution 3.0 Unported"
__version__   = "V0.07"

import os, shutil, sys

from wwpdb.utils.config.ConfigInfo                           import ConfigInfo
from wwpdb.apps.ccmodule.io.ChemCompAssignDataStore          import ChemCompAssignDataStore
from wwpdb.apps.ccmodule.reports.ChemCompAlignImageGenerator import ChemCompAlignImageGenerator

class SaveLigand(object):
    """ 
    """
    def __init__(self, reqObj=None, verbose=False, log=sys.stderr):
        self.__verbose=verbose
        self.__lfh=log
        self.__reqObj=reqObj
        self.__sObj=None
        self.__sessionId=None
        self.__sessionPath=None
        self.__instanceId=str(self.__reqObj.getValue("instanceid"))
        self.__subpath=str(self.__reqObj.getValue("subpath"))
        self.__filextension=str(self.__reqObj.getValue("filextension"))
        if not self.__filextension:
            self.__filextension='cif'
        #
        self.__genimageflag=str(self.__reqObj.getValue("genimageflag"))
        self.__siteId=str(self.__reqObj.getValue('WWPDB_SITE_ID'))
        self.__cI=ConfigInfo(self.__siteId)
        #
        self.__getSession()
        #

    def __getSession(self):
        """ Join existing session or create new session as required.
        """
        #
        self.__sObj=self.__reqObj.newSessionObj()
        self.__sessionId=self.__sObj.getId()
        self.__sessionPath=self.__sObj.getPath()
        if self.__subpath:
            self.__sessionPath=os.path.join(self.__sObj.getPath(),self.__subpath)
        #
        if (self.__verbose):
            self.__lfh.write("------------------------------------------------------\n")                    
            self.__lfh.write("+SaveLigand.__getSession() - creating/joining session %s\n" % self.__sessionId)
            self.__lfh.write("+SaveLigand.__getSession() - session path %s\n" % self.__sessionPath)            

    def GetResult(self):
        filePath = os.path.join(self.__sessionPath, self.__instanceId, self.__instanceId + '.' + self.__filextension)
        if not os.access(filePath, os.R_OK):
            return ''
        self.__getInputCifData()
        self.__updateCif()
        self.__updateImage(self.__instanceId)
        related_instanceids = str(self.__reqObj.getValue("related_instanceids"))
        if related_instanceids:
            relatedList = related_instanceids.split(",")
            for relatedId in relatedList:
                relatedFilePath = os.path.join(self.__sessionPath, relatedId, relatedId + '.' + self.__filextension)
                if not os.access(relatedFilePath, os.R_OK):
                    continue
                #
                shutil.copyfile(filePath, relatedFilePath)
                self.__updateImage(relatedId)
            #
        #
        return 'successful'

    def __getInputCifData(self):
        cif = self.__reqObj.getValue('cif')
        filePath = os.path.join(self.__sessionPath, self.__instanceId, 'in.cif')
        f = open(filePath, 'w')
        f.write(cif + '\n')
        f.close()

    def __updateCif(self):
        filePath = os.path.join(self.__sessionPath, self.__instanceId, 'in.cif')
        if not os.access(filePath, os.R_OK):
            return
        #
        script = os.path.join(self.__sessionPath, self.__instanceId, 'update-comp.csh')
        f = open(script, 'w')
        f.write('#!/bin/tcsh -f\n')
        f.write('#\n')
        f.write('setenv CC_TOOLS   ' + self.__cI.get('SITE_CC_APPS_PATH') + '/bin\n')
        f.write('setenv OE_DIR     ' + self.__cI.get('SITE_CC_OE_DIR') + '\n')
        f.write('setenv OE_LICENSE ' + self.__cI.get('SITE_CC_OE_LICENSE') + '\n')
        f.write('setenv ACD_DIR    ' + self.__cI.get('SITE_CC_ACD_DIR') + '\n')
        f.write('setenv CACTVS_DIR ' + self.__cI.get('SITE_CC_CACTVS_DIR') + '\n')
        f.write('setenv CORINA_DIR ' + self.__cI.get('SITE_CC_CORINA_DIR') + '/bin\n')
        f.write('setenv BABEL_DIR '  + self.__cI.get('SITE_CC_BABEL_DIR') + '\n')
        f.write('setenv BABEL_DATADIR ' + self.__cI.get('SITE_CC_BABEL_DATADIR') + '\n')
        f.write('setenv INCHI_DIR  ' + self.__cI.get('SITE_CC_INCHI_DIR') + '\n')
        f.write('setenv LD_LIBRARY_PATH ' + self.__cI.get('SITE_CC_BABEL_LIB') + ':' + \
                os.path.join(self.__cI.get('SITE_LOCAL_APPS_PATH'), 'lib') + ':' + \
                self.__cI.get('SITE_CC_ACD_DIR') + '\n')
        f.write('#\n')
        f.write("${CC_TOOLS}/annotateComp -vv -i in.cif -op " + \
                "'stereo-cactvs|aro-cactvs|descriptor-oe|descriptor-cactvs|" + \
                "descriptor-inchi|name-oe|name-acd|xyz-ideal-corina|xyz-model-h-oe|" + \
                "rename|fix' -o out.cif >& _comp_log\n")
        f.write('#\n')
        f.write('if ( -e out.cif ) then\n')
        f.write('    mv -f out.cif ' + self.__instanceId + '.' + self.__filextension + '\n')
        f.write('else\n')
        f.write('    mv -f in.cif ' + self.__instanceId + '.' + self.__filextension + '\n')
        f.write('endif\n')
        f.write('#\n')
        f.close()
        cmd = 'cd ' + os.path.join(self.__sessionPath, self.__instanceId)  + '; chmod 755 update-comp.csh; ./update-comp.csh >& comp_log'
        os.system(cmd)

    def __updateImage(self, instanceId):
        if self.__genimageflag != 'yes':
            return
        #
        self.__reqObj.setValue("SessionsPath", self.__cI.get('SITE_WEB_APPS_SESSIONS_PATH'))
        ccAssignDataStore = ChemCompAssignDataStore(self.__reqObj, verbose=self.__verbose, log=self.__lfh)
        mtchL = ccAssignDataStore.getTopHitsList(instanceId)
        HitList = []
        for tupL in mtchL:
            HitList.append(tupL[0])
        #
        chemCompFilePathAbs = os.path.join(self.__sessionPath, instanceId, instanceId + '.' + self.__filextension)
        ccaig = ChemCompAlignImageGenerator(reqObj=self.__reqObj, verbose=self.__verbose, log=self.__lfh)
        ccaig.generateImages(instId=instanceId, instFile=chemCompFilePathAbs, hitList=HitList)
