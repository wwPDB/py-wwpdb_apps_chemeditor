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
__author__    = "Zukang Feng"
__email__     = "zfeng@rcsb.rutgers.edu"
__license__   = "Creative Commons Attribution 3.0 Unported"
__version__   = "V0.07"

import os, sys, string, traceback

from wwpdb.utils.config.ConfigInfo  import ConfigInfo
from wwpdb.apps.chemeditor.webapp.CVSCommit  import CVSBase

#

class GetLigand(object):
    """ 
    """
    def __init__(self, reqObj=None, verbose=False, log=sys.stderr):
        self.__verbose=verbose
        self.__lfh=log
        self.__reqObj=reqObj
        self.__siteId  = str(self.__reqObj.getValue('WWPDB_SITE_ID'))
        self.__cI=ConfigInfo(self.__siteId)
        #

    def GetResult(self):
        if (self.__verbose):
            self.__lfh.write("+GetLigand.GetResult() - starting\n")
        #
        id =  str(self.__reqObj.getValue('id'))
        if not id:
            return ''
        #
        cvsUtil = CVSBase(reqObj=self.__reqObj, verbose=self.__verbose, log=self.__lfh)
        filePath = cvsUtil.getSandBoxFilePath(id)
        if not os.access(filePath, os.F_OK):
            if (self.__verbose):
                self.__lfh.write("+GetLigand.GetResult() - Not found %s\n" % filePath)
            return ''
        #
        if (self.__verbose):
            self.__lfh.write("+GetLigand.GetResult() - found %s\n" % filePath)
        f = file(filePath, 'r')
        data = f.read()
        f.close()
        #if (self.__verbose):
        #    self.__lfh.write("+GetLigand.GetResult() - data %s\n" % data)
        return data
