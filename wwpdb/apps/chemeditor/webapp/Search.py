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
__author__    = "Zukang Feng"
__email__     = "zfeng@rcsb.rutgers.edu"
__license__   = "Creative Commons Attribution 3.0 Unported"
__version__   = "V0.07"

import os, sys, string, traceback

from wwpdb.utils.config.ConfigInfo                  import ConfigInfo
from wwpdb.apps.chemeditor.webapp.CVSCommit       import CVSBase
from wwpdb.io.file.mmCIFUtil                   import mmCIFUtil

#

class Search(object):
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
        self.__idMap = {}
        self.__idList = []

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
            self.__lfh.write("+Search.__getSession() - creating/joining session %s\n" % self.__sessionId)
            self.__lfh.write("+Search.__getSession() - session path %s\n" % self.__sessionPath)            

    def GetResult(self):
        self.__getInputCifData()
        self.__updateCif()
        self.__search()
        return self.__returnData()

    def __getInputCifData(self):
        cif = self.__reqObj.getValue('cif')
        filePath = os.path.join(self.__sessionPath,'in.cif')
        f = file(filePath, 'w')
        f.write(cif + '\n')
        f.close()

    def __updateCif(self):
        filePath = os.path.join(self.__sessionPath, 'in.cif')
        if not os.access(filePath, os.R_OK):
            return
        #
        script = os.path.join(self.__sessionPath, 'update-comp.csh')
        f = file(script, 'w')
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
        f.write('    mv -f out.cif in.cif\n')
        f.write('endif\n')
        f.write('#\n')
        f.close()
        cmd = 'cd ' + self.__sessionPath + '; chmod 755 update-comp.csh; ./update-comp.csh >& comp_log'
        os.system(cmd)

    def __search(self):
        filePath = os.path.join(self.__sessionPath, 'in.cif')
        if not os.access(filePath, os.R_OK):
            return
        #
        exact_flag = self.__reqObj.getValue('exact')
        if exact_flag == 'yes':
            self.__runSearchScript('prefilter|strict|skip-h|exact')
        else:
            self.__runSearchScript('prefilter|relaxedstereo|skip-h|exact')
            self.__runSearchScript('prefilter|relaxed|skip-h|allowextra')
            self.__runSearchScript('prefilter|relaxed|skip-h|close')

    def __runSearchScript(self, option):
        script = os.path.join(self.__sessionPath, 'search.csh')
        f = file(script, 'w')
        f.write('#!/bin/tcsh -f\n')
        f.write('#\n')
        f.write('setenv CC_TOOLS ' + self.__cI.get('SITE_CC_APPS_PATH') + '/bin\n')
        f.write('setenv CC_DICT  ' + self.__cI.get('SITE_CC_DICT_PATH') + '\n')
        f.write('#\n')
        f.write("${CC_TOOLS}/matchComp -i in.cif -lib ${CC_DICT}/Components-all-v3.sdb " + \
                "-index ${CC_DICT}/Components-all-v3-r4.idx -type structure -op '" + \
                option + "' -o search_result >& _search_log\n")
        f.write('#\n')
        f.close()
        cmd = 'cd ' + self.__sessionPath + '; chmod 755 search.csh; ./search.csh >& search_log'
        os.system(cmd)
        #
        self.__parseSearchResult()

    def __parseSearchResult(self):
        filePath = os.path.join(self.__sessionPath, 'search_result')
        if not os.access(filePath, os.R_OK):
            return
        #
        f = file(filePath, 'r')
        data = f.read()
        f.close()
        #
        llist = data.split('\n')
        for line in llist[1:]:
            if not line:
                continue
            #
            list = line.split('\t')
            if len(list) != 8:
                continue
            #
            if self.__idMap.has_key(list[4]):
                continue
            #
            diff = int(list[7]) - int(list[3])
            if diff > 3:
                continue
            #
            if not self.__isValidId(list[4]):
                continue
            #
            self.__idMap[list[4]] = 'yes'
            self.__idList.append(list[4])
        #

    def __isValidId(self, id):
        self.__reqObj.setValue("sessionid", self.__sessionId)
        cvsUtil = CVSBase(reqObj=self.__reqObj, verbose=self.__verbose, log=self.__lfh)
        filePath = cvsUtil.getSandBoxFilePath(id) 
        if not os.access(filePath, os.F_OK):
            return False
        #
        cifObj = mmCIFUtil(filePath=filePath)
        status = cifObj.GetSingleValue('chem_comp', 'pdbx_release_status').upper()
        if status == 'OBS':
            return False
        #
        return True

    def __returnData(self):
        data = ''
        if self.__idList:
            if len(self.__idList) > 15:
                data = '\n'.join(self.__idList[0:15])
            else:
                data = '\n'.join(self.__idList)
        return data
