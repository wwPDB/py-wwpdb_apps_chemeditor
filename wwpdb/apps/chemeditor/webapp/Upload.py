##
# File:  Upload.py
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
import traceback
import ntpath


class Upload(object):
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
        self.__fileName = None
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
            self.__lfh.write("+Upload.__getSession() - creating/joining session %s\n" % self.__sessionId)
            self.__lfh.write("+Upload.__getSession() - session path %s\n" % self.__sessionPath)

    def GetResult(self):
        self.__uploadFile()
        return self.__returnData()

    def __uploadFile(self):
        if (self.__verbose):
            self.__lfh.write("+Upload.__uploadFile() - file upload starting\n")
        #
        # Copy upload file to session directory -
        #
        try:
            fs = self.__reqObj.getRawValue('data')
            fNameInput = str(fs.filename).lower()
            #
            # Need to deal with some platform issues -
            #
            if (fNameInput.find('\\') != -1) :
                # likely windows path -
                self.__fileName = ntpath.basename(fNameInput)
            else:
                self.__fileName = os.path.basename(fNameInput)
            #
            if (self.__verbose):
                self.__lfh.write("+Upload.__uploadFile() - upload file %s\n" % fs.filename)
                self.__lfh.write("+Upload.__uploadFile() - base file   %s\n" % self.__fileName)
            #
            # Store upload file in session directory -
            #
            fPathAbs = os.path.join(self.__sessionPath, self.__fileName)
            ofh = open(fPathAbs, 'wb')
            ofh.write(fs.file.read())
            ofh.close()
        except:  # noqa: E722 pylint: disable=bare-except
            if (self.__verbose):
                self.__lfh.write("+Upload.__uploadFile() File upload processing failed for %s\n" % str(fs.filename))
                traceback.print_exc(file=self.__lfh)
        #

    def __returnData(self):
        data = ''
        if not self.__fileName:
            return data
        #
        filePath = os.path.join(self.__sessionPath, self.__fileName)
        if os.access(filePath, os.R_OK):
            f = open(filePath, 'r')
            data = f.read()
            f.close()
        return data
