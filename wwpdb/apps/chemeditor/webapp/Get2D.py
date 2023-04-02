##
# File:  Get2D.py
# Date:  25-Feb-2013
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

from wwpdb.utils.config.ConfigInfoApp import ConfigInfoAppCommon


class Get2D(object):
    """
    """
    def __init__(self, reqObj=None, verbose=False, log=sys.stderr):
        self.__verbose = verbose
        self.__lfh = log
        self.__reqObj = reqObj
        self.__sObj = None
        self.__sessionId = None
        self.__sessionPath = None
        # self.__rltvSessionPath = None
        self.__siteId = str(self.__reqObj.getValue('WWPDB_SITE_ID'))
        self.__cICommon = ConfigInfoAppCommon(self.__siteId)
        #
        self.__getSession()
        #

    def __getSession(self):
        """ Join existing session or create new session as required.
        """
        #
        self.__sObj = self.__reqObj.newSessionObj()
        self.__sessionId = self.__sObj.getId()
        self.__sessionPath = self.__sObj.getPath()
        # self.__rltvSessionPath = self.__sObj.getRelativePath()
        if (self.__verbose):
            self.__lfh.write("------------------------------------------------------\n")
            self.__lfh.write("+Get2D.__getSession() - creating/joining session %s\n" % self.__sessionId)
            self.__lfh.write("+Get2D.__getSession() - session path %s\n" % self.__sessionPath)

    def GetResult(self):
        self.__getInputSdfData()
        self.__getCACTVSScript()
        self.__runCACTVSScript()
        return self.__returnSdfData()

    def __getInputSdfData(self):
        sdf = self.__reqObj.getValue('sdf')
        filePath = os.path.join(self.__sessionPath, 'in.sdf')
        f = open(filePath, 'w')
        f.write(sdf + '\n')
        f.close()

    def __getCACTVSScript(self):
        hflag = str(self.__reqObj.getValue('hflag'))
        filePath = os.path.join(self.__sessionPath, 'script')
        f = open(filePath, 'w')
        f.write('set ehandle [molfile read in.sdf]\n')
        if hflag == 'yes':
            f.write('ens hadd $ehandle\n')
        f.write('ens need $ehandle E_NATOMS recalc\n')
        f.write('ens lock $ehandle E_NATOMS\n')
        f.write('ens need $ehandle {A_SYMBOL A_FREE_ELECTRONS A_XY A_ELEMENT} nofunc\n')
        f.write('ens lock $ehandle {E_STDBLE A_ELEMENT A_NOM_CHARGE A_CIPSTEREO A_DLSTEREO B_CIPSTEREO B_CTSTEREO}\n')
        f.write('ens need $ehandle {A_LABSTEREO A_CIPSTEREO A_DLSTEREO} recalc\n')
        f.write('ens lock $ehandle {A_LABSTEREO A_CIPSTEREO A_DLSTEREO}\n')
        f.write('ens need $ehandle {B_LABSTEREO B_CIPSTEREO B_CTSTEREO} recalc\n')
        f.write('ens lock $ehandle {B_LABSTEREO B_CIPSTEREO B_CTSTEREO}\n')
        f.write('set whandle [molfile open out.sdf w format sdf valencelevel 1]\n')
        f.write('molfile write $whandle $ehandle\n')
        f.write('molfile close $whandle\n')
        f.close()

    def __runCACTVSScript(self):
        filePath = os.path.join(self.__sessionPath, 'get2d.csh')
        f = open(filePath, 'w')
        f.write('#!/bin/tcsh -f\n')
        f.write('#\n')
        f.write('setenv CACTVS_ROOT ' + self.__cICommon.get_site_cc_cactvs_dir() + '\n')
        f.write('#\n')
        f.write('cat script | ${CACTVS_ROOT}/csts -d $*\n')
        f.close()
        cmd = 'cd ' + self.__sessionPath + '; chmod 755 get2d.csh; ./get2d.csh'
        os.system(cmd)

    def __returnSdfData(self):
        data = ''
        filePath = os.path.join(self.__sessionPath, 'out.sdf')
        if os.access(filePath, os.R_OK):
            f = open(filePath, 'r')
            data = f.read()
            f.close()
        return data
