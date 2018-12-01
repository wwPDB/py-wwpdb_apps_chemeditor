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
__author__    = "Zukang Feng"
__email__     = "zfeng@rcsb.rutgers.edu"
__license__   = "Creative Commons Attribution 3.0 Unported"
__version__   = "V0.07"

import os, sys, string, traceback

from wwpdb.utils.config.ConfigInfo  import ConfigInfo
from wwpdb.apps.chemeditor.webapp.CVSCommit  import CVSBase

#

class AtomMatch(object):
    """ 
    """
    def __init__(self, reqObj=None, verbose=False, log=sys.stderr):
        self.__verbose=verbose
        self.__lfh=log
        self.__reqObj=reqObj
        self.__sObj=None
        self.__sessionId=None
        self.__sessionPath=None
        self.__rltvSessionPath=None
        self.__siteId  = str(self.__reqObj.getValue('WWPDB_SITE_ID'))
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
        self.__rltvSessionPath=self.__sObj.getRelativePath()
        if (self.__verbose):
            self.__lfh.write("------------------------------------------------------\n")                    
            self.__lfh.write("+AtomMatch.__getSession() - creating/joining session %s\n" % self.__sessionId)
            self.__lfh.write("+AtomMatch.__getSession() - session path %s\n" % self.__sessionPath)            

    def GetResult(self):
        self.__getInputCifData()
        self.__runAtomMatchScript()
        return self.__returnData()

    def __getInputCifData(self):
        cif = self.__reqObj.getValue('cif')
        filePath = os.path.join(self.__sessionPath,'in.cif')
        f = file(filePath, 'w')
        f.write(cif + '\n')
        f.close()

    def __runAtomMatchScript(self):
        filePath = os.path.join(self.__sessionPath, 'in.cif')
        if not os.access(filePath, os.R_OK):
            return
        #
        reverse_flag = self.__reqObj.getValue('reverse')
        id =  str(self.__reqObj.getValue('id'))
        if not id:
            return
        #
        self.__reqObj.setValue("sessionid", self.__sessionId)
        cvsUtil = CVSBase(reqObj=self.__reqObj, verbose=self.__verbose, log=self.__lfh)
        filePath = cvsUtil.getSandBoxFilePath(id)
        if not os.access(filePath, os.F_OK):
            return
        #
        script = os.path.join(self.__sessionPath, 'match.csh')
        f = file(script, 'w')
        f.write('#!/bin/tcsh -f\n')
        f.write('#\n')
        f.write('setenv RCSBROOT   ' + self.__cI.get('SITE_ANNOT_TOOLS_PATH') + '\n')
        f.write('setenv BINPATH ${RCSBROOT}/bin\n')
        f.write('#\n')
        if reverse_flag == 'yes':
            f.write('${BINPATH}/GetAtomMatch -first in.cif -second ' + filePath)
        else:
            f.write('${BINPATH}/GetAtomMatch -first ' + filePath + ' -second in.cif')
        f.write(' -output match_result -log logfile >& _match_log\n')
        f.write('#\n')
        f.close()
        cmd = 'cd ' + self.__sessionPath + '; chmod 755 match.csh; ./match.csh >& match_log'
        os.system(cmd)
        #

    def __returnData(self):
        filePath = os.path.join(self.__sessionPath, 'match_result')
        if not os.access(filePath, os.R_OK):
            return ''
        #
        f = file(filePath, 'r')
        data = f.read()
        f.close()
        #
        return data
