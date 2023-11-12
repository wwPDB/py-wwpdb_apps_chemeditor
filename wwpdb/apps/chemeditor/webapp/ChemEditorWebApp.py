##
# File:  ChemEditorWebApp.py
# Date:  25-Feb-2013
# Updates:
##
"""
Chemeditor web request and response processing modules.

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

from wwpdb.utils.config.ConfigInfo import ConfigInfo
from wwpdb.utils.config.ConfigInfoApp import ConfigInfoAppCc
from wwpdb.utils.session.WebRequest import InputRequest, ResponseContent
from wwpdb.io.misc.SendEmail import SendEmail

from wwpdb.apps.chemeditor.webapp.AtomMatch import AtomMatch
# from wwpdb.apps.chemeditor.webapp.ChemCompHash import ChemCompHash
from wwpdb.apps.chemeditor.webapp.ChemEditorBase import ChemEditorBase
from wwpdb.apps.chemeditor.webapp.CVSCommit import CVSCommit
from wwpdb.apps.chemeditor.webapp.Enumeration import Enumeration
from wwpdb.apps.chemeditor.webapp.Get2D import Get2D
from wwpdb.apps.chemeditor.webapp.GetLigand import GetLigand
from wwpdb.apps.chemeditor.webapp.SaveLigand import SaveLigand
from wwpdb.apps.chemeditor.webapp.Search import Search
from wwpdb.apps.chemeditor.webapp.UpdateLigand import UpdateLigand
from wwpdb.apps.chemeditor.webapp.Upload import Upload
from wwpdb.apps.chemeditor.webapp.DaInternalCombineDb import DaInternalCombineDb


def threshold_crossed(pre, post, thresholdList):
    """Returns True if going from pre to post crosses a value in the thresholdList.
       pre > post
    """
    for th in thresholdList:
        if pre > th and post <= th:
            return True
    return False


class ChemEditorWebApp(object):
    """Handle request and response object processing for chemeditor web application.

    """
    def __init__(self, parameterDict=None, verbose=False, log=sys.stderr, siteId="WWPDB_DEV"):
        """
        Create an instance of `ChemEditorWebApp` to manage a chemeditor web request.

         :param `parameterDict`: dictionary storing parameter information from the web request.
             Storage model for GET and POST parameter data is a dictionary of lists.
         :param `verbose`:  boolean flag to activate verbose logging.
         :param `log`:      stream for logging.

        """
        if parameterDict is None:
            parameterDict = {}
        self.__verbose = verbose
        self.__lfh = log
        self.__debug = False
        self.__siteId = siteId
        self.__cI = ConfigInfo(self.__siteId)
        self.__topPath = self.__cI.get('SITE_WEB_APPS_TOP_PATH')
        #

        if isinstance(parameterDict, dict):
            self.__myParameterDict = parameterDict
        else:
            self.__myParameterDict = {}

        if (self.__verbose):
            self.__lfh.write("+ChemEditorWebApp.__init() - REQUEST STARTING ------------------------------------\n")
            self.__lfh.write("+ChemEditorWebApp.__init() - dumping input parameter dictionary \n")
            self.__lfh.write("%s" % (''.join(self.__dumpRequest())))

        self.__reqObj = InputRequest(self.__myParameterDict, verbose=self.__verbose, log=self.__lfh)

        self.__topSessionPath = self.__cI.get('SITE_WEB_APPS_TOP_SESSIONS_PATH')
        #
        self.__reqObj.setValue("TopSessionPath", self.__topSessionPath)
        self.__reqObj.setValue("TopPath", self.__topPath)
        self.__reqObj.setValue("WWPDB_SITE_ID", self.__siteId)
        os.environ["WWPDB_SITE_ID"] = self.__siteId
        #
        self.__reqObj.setReturnFormat(return_format="html")
        #
        if (self.__verbose):
            self.__lfh.write("-----------------------------------------------------\n")
            self.__lfh.write("+ChemEditorWebApp.__init() Leaving _init with request contents\n")
            self.__reqObj.printIt(ofh=self.__lfh)
            self.__lfh.write("---------------ChemEditorWebApp - done -------------------------------\n")
            self.__lfh.flush()

    def doOp(self):
        """ Execute request and package results in response dictionary.

        :Returns:
             A dictionary containing response data for the input request.
             Minimally, the content of this dictionary will include the
             keys: CONTENT_TYPE and REQUEST_STRING.
        """
        stw = ChemEditorWebAppWorker(reqObj=self.__reqObj, verbose=self.__verbose, log=self.__lfh)
        rC = stw.doOp()
        if (self.__debug):
            rqp = self.__reqObj.getRequestPath()
            self.__lfh.write("+ChemEditorWebApp.doOp() operation %s\n" % rqp)
            self.__lfh.write("+ChemEditorWebApp.doOp() return format %s\n" % self.__reqObj.getReturnFormat())
            if rC is not None:
                self.__lfh.write("%s" % (''.join(rC.dump())))
            else:
                self.__lfh.write("+ChemEditorWebApp.doOp() return object is empty\n")

        #
        # Package return according to the request return_format -
        #
        return rC.get()

    def __dumpRequest(self):
        """Utility method to format the contents of the internal parameter dictionary
           containing data from the input web request.

           :Returns:
               ``list`` of formatted text lines
        """
        retL = []
        retL.append("\n-----------------ChemEditorWebApp().__dumpRequest()-----------------------------\n")
        retL.append("Parameter dictionary length = %d\n" % len(self.__myParameterDict))
        for k, vL in self.__myParameterDict.items():
            retL.append("Parameter %30s :" % k)
            for v in vL:
                retL.append(" ->  %s\n" % v)
        retL.append("-------------------------------------------------------------\n")
        return retL


class ChemEditorWebAppWorker(object):
    def __init__(self, reqObj=None, verbose=False, log=sys.stderr):
        """
         Worker methods for the chemical component editor application

         Performs URL - application mapping and application launching
         for chemical component editor tool.

         All operations can be driven from this interface which can
         supplied with control information from web application request
         or from a testing application.
        """
        self.__verbose = verbose
        self.__lfh = log
        self.__reqObj = reqObj
        self.__siteId = str(self.__reqObj.getValue("WWPDB_SITE_ID"))
        self.__cIAppCc = ConfigInfoAppCc(self.__siteId, verbose=verbose, log=log)
        #
        self.__appPathD = {'/service/environment/dump': '_dumpOp',
                           '/service/chemeditor/get_2d': '_get2D',
                           '/service/chemeditor/upload': '_upLoad',
                           '/service/chemeditor/get_ligand': '_getLigand',
                           '/service/chemeditor/search': '_searchLigand',
                           '/service/chemeditor/atom_match': '_atomMatch',
                           '/service/chemeditor/echo_file': '_echoFileDownLoad',
                           '/service/chemeditor/get_new_code': '_getNewCode',
                           '/service/chemeditor/status_code': '_getStatusCode',
                           '/service/chemeditor/one_letter_code': '_getOneLetterCode',
                           '/service/chemeditor/update': '_updateLigand',
                           '/service/chemeditor/save_component': '_saveComponent',
                           '/service/chemeditor/cvs_commit': '_CVSCommit',
                           '/service/chemeditor/get_enumeration': '_getEnumeration',
                           '/service/chemeditor/get_entries_with_ligand': '_getEntriesWithLigands'
                           }

    def doOp(self):
        """Map operation to path and invoke operation.

            :Returns:

            Operation output is packaged in a ResponseContent() object.
        """
        return self.__doOpException()

    def __doOpNoException(self):  # pylint: disable=unused-private-member
        """Map operation to path and invoke operation.  No exception handling is performed.

            :Returns:

            Operation output is packaged in a ResponseContent() object.
        """
        #
        reqPath = self.__reqObj.getRequestPath()
        if reqPath not in self.__appPathD:
            # bail out if operation is unknown -
            rC = ResponseContent(reqObj=self.__reqObj, verbose=self.__verbose, log=self.__lfh)
            rC.setError(errMsg='Unknown operation')
            return rC
        else:
            mth = getattr(self, self.__appPathD[reqPath], None)
            rC = mth()
        return rC

    def __doOpException(self):
        """Map operation to path and invoke operation.  Exceptions are caught within this method.

            :Returns:

            Operation output is packaged in a ResponseContent() object.
        """
        #
        try:
            reqPath = self.__reqObj.getRequestPath()
            if reqPath not in self.__appPathD:
                # bail out if operation is unknown -
                rC = ResponseContent(reqObj=self.__reqObj, verbose=self.__verbose, log=self.__lfh)
                rC.setError(errMsg='Unknown operation')
            else:
                mth = getattr(self, self.__appPathD[reqPath], None)
                rC = mth()
            return rC
        except:  # noqa: E722 pylint: disable=bare-except
            traceback.print_exc(file=self.__lfh)
            rC = ResponseContent(reqObj=self.__reqObj, verbose=self.__verbose, log=self.__lfh)
            rC.setError(errMsg='Operation failure')
            return rC

    ################################################################################################################
    # ------------------------------------------------------------------------------------------------------------
    #      Top-level REST methods
    # ------------------------------------------------------------------------------------------------------------
    #
    def _dumpOp(self):
        rC = ResponseContent(reqObj=self.__reqObj, verbose=self.__verbose, log=self.__lfh)
        rC.setHtmlList(self.__reqObj.dump(format='html'))
        return rC

    def _get2D(self):
        """ Get 2D SDF file
        """
        if (self.__verbose):
            self.__lfh.write("+ChemEditorWebAppWorker._get2D() Starting now\n")
        #
        self.__reqObj.setReturnFormat(return_format="json")
        rC = ResponseContent(reqObj=self.__reqObj, verbose=self.__verbose, log=self.__lfh)
        #
        classObj = Get2D(reqObj=self.__reqObj, verbose=self.__verbose, log=self.__lfh)
        textcontent = classObj.GetResult()
        if not textcontent:
            rC.setError(errMsg='failed')
        else:
            rC.setText(text=textcontent)
        #
        return rC

    def _upLoad(self):
        """ Get upload file
        """
        if (self.__verbose):
            self.__lfh.write("+ChemEditorWebAppWorker._upLoad() Starting now\n")
        #
        self.__reqObj.setReturnFormat(return_format="html")
        rC = ResponseContent(reqObj=self.__reqObj, verbose=self.__verbose, log=self.__lfh)
        #
        classObj = Upload(reqObj=self.__reqObj, verbose=self.__verbose, log=self.__lfh)
        rC.setHtmlText(classObj.GetResult())
        #
        return rC

    def _getLigand(self):
        """ Get chemical component cif file from ID
        """
        if (self.__verbose):
            self.__lfh.write("+ChemEditorWebAppWorker._getLigand() Starting now\n")
        #
        self.__reqObj.setReturnFormat(return_format="json")
        rC = ResponseContent(reqObj=self.__reqObj, verbose=self.__verbose, log=self.__lfh)
        #
        classObj = GetLigand(reqObj=self.__reqObj, verbose=self.__verbose, log=self.__lfh)
        textcontent = classObj.GetCifData()
        if not textcontent:
            rC.setError(errMsg='failed')
        else:
            rC.setText(text=textcontent)
        #
        return rC

    def _searchLigand(self):
        """ Search chemical component dictionary
        """
        if (self.__verbose):
            self.__lfh.write("+ChemEditorWebAppWorker._searchLigand() Starting now\n")
        #
        self.__reqObj.setReturnFormat(return_format="json")
        rC = ResponseContent(reqObj=self.__reqObj, verbose=self.__verbose, log=self.__lfh)
        #
        classObj = Search(reqObj=self.__reqObj, verbose=self.__verbose, log=self.__lfh)
        textcontent = classObj.GetResult()
        if not textcontent:
            rC.setError(errMsg='failed')
        else:
            rC.setText(text=textcontent)
        #
        return rC

    def _atomMatch(self):
        """ Get matahed atom pair list for two chemical components
        """
        if (self.__verbose):
            self.__lfh.write("+ChemEditorWebAppWorker._atomMatch() Starting now\n")
        #
        self.__reqObj.setReturnFormat(return_format="json")
        rC = ResponseContent(reqObj=self.__reqObj, verbose=self.__verbose, log=self.__lfh)
        #
        classObj = AtomMatch(reqObj=self.__reqObj, verbose=self.__verbose, log=self.__lfh)
        textcontent = classObj.GetResult()
        if not textcontent:
            rC.setError(errMsg='failed')
        else:
            rC.setText(text=textcontent)
        #
        return rC

    def _echoFileDownLoad(self):
        """ Echo chemical component cif file downloading
        """
        if (self.__verbose):
            self.__lfh.write("+ChemEditorWebAppWorker._echoFileDownLoad() Starting now\n")
        #
        sObj = self.__reqObj.newSessionObj()
        _sessionId = sObj.getId()  # noqa: F841
        sessionPath = sObj.getPath()
        #
        data = self.__reqObj.getValue('download')
        data = data.replace('\n\r', '\n')
        data = data.replace('\r\n', '\n')
        data = data.replace('\r', '\n')
        fileId = str(self.__reqObj.getValue('downloadName'))
        filePath = os.path.join(sessionPath, fileId)
        f = open(filePath, 'w')
        f.write(data + '\n')
        f.close()
        #
        self.__reqObj.setReturnFormat(return_format="binary")
        rC = ResponseContent(reqObj=self.__reqObj, verbose=self.__verbose, log=self.__lfh)
        rC.setBinaryFile(filePath, attachmentFlag=True, serveCompressed=True)
        #
        return rC

    def _getNewCode(self):
        """ Get New Ligand ID Code
        """
        if (self.__verbose):
            self.__lfh.write("+ChemEditorWebAppWorker._getNewCode() Starting now\n")
        #
        code = self.__getNewCodeFromList()
        #
        self.__reqObj.setReturnFormat(return_format="json")
        rC = ResponseContent(reqObj=self.__reqObj, verbose=self.__verbose, log=self.__lfh)
        #
        if not code:
            rC.setError(errMsg='failed')
        else:
            rC.setText(text=code)
        #
        return rC

    def __getNewCodeFromList(self):
        """ Get unused Ligand Code from pre-defined list
        """
        cvsUtil = ChemEditorBase(reqObj=self.__reqObj, verbose=self.__verbose, log=self.__lfh)
        code = ''
        filePath = os.path.join(self.__cIAppCc.get_unused_ccd_file())
        self.__lfh.write("+ChemEditorWebAppWorker.__getNewCodeFromList filePath=%s\n" % filePath)
        f = open(filePath, 'r')
        data = f.read()
        f.close()
        #
#       cCH = ChemCompHash()
        idlist = data.split('\n')
        idx = 0
        for ccId in idlist:
            idx += 1
#           if cCH.getChemCompIdSite(ccId) != self.__cI.get('SITE_NAME').upper():
#               continue
#           #
            component = cvsUtil.getSandBoxFilePath(ccId)
            if not component:
                code = ccId
                break
            #
        #
        data = '\n'.join(idlist[idx:])
        f = open(filePath, 'w')
        f.write(data)
        f.close()

        # Notify if need be
        # Lists of thresholds to notify on
        crossList = [500, 250, 100, 50, 25, 10, 5, 4, 2, 1]

        presize = len(idlist)
        postsize = presize - idx
        notify = threshold_crossed(presize, postsize, crossList)
        if notify:
            self.__lfh.write("+ChemEditorWebAppWorker.__getNewCodeFromList threshold notification len=%s\n" % postsize)
            if self.__reqObj.getValue("debug_no_notify"):
                # Turn off notification
                self.__lfh.write("+ChemEditorWebAppWorker.__getNewCodeFromList skip threshold notification\n")
            else:
                se = SendEmail(self.__siteId, self.__verbose, self.__lfh)
                subj = "CCD count warning : ID left = %r" % postsize
                body = f"Warning - the number of CCDs left to be assigned is {postsize}\n"
                body += f"for siteId {self.__siteId}"
                status = se.send_system_error(body, subj)
                if not status:
                    self.__lfh.write("+ChemEditorWebAppWorker.__getNewCodeFromList failed to send notification\n")

        # Notification complete, return code
        return code

    def _getStatusCode(self):
        """ Check status code for existing chemical component
        """
        if (self.__verbose):
            self.__lfh.write("+ChemEditorWebAppWorker._getStatusCode() Starting now\n")
        #
        classObj = GetLigand(reqObj=self.__reqObj, verbose=self.__verbose, log=self.__lfh)
        status = classObj.GetReleaseStatus()
        #
        self.__reqObj.setReturnFormat(return_format="json")
        rC = ResponseContent(reqObj=self.__reqObj, verbose=self.__verbose, log=self.__lfh)
        #
        if not status:
            rC.setError(errMsg='failed')
        else:
            rC.setText(text=status)
        #
        return rC

    def _getOneLetterCode(self):
        """ Get one letter code for existing chemical component
        """
        if (self.__verbose):
            self.__lfh.write("+ChemEditorWebAppWorker._getOneLetterCode() Starting now\n")
        #
        classObj = GetLigand(reqObj=self.__reqObj, verbose=self.__verbose, log=self.__lfh)
        oneletter = classObj.GetOneLetterCode()
        #
        self.__reqObj.setReturnFormat(return_format="json")
        rC = ResponseContent(reqObj=self.__reqObj, verbose=self.__verbose, log=self.__lfh)
        #
        if not oneletter:
            rC.setError(errMsg='failed')
        else:
            rC.setText(text=oneletter)
        #
        return rC

    def _updateLigand(self):
        """ Run annotateComp program to update ligand features
        """
        if (self.__verbose):
            self.__lfh.write("+ChemEditorWebAppWorker._updateLigand() Starting now\n")
        #
        self.__reqObj.setReturnFormat(return_format="json")
        rC = ResponseContent(reqObj=self.__reqObj, verbose=self.__verbose, log=self.__lfh)
        #
        classObj = UpdateLigand(reqObj=self.__reqObj, verbose=self.__verbose, log=self.__lfh)
        textcontent = classObj.GetResult()
        if not textcontent:
            rC.setError(errMsg='failed')
        else:
            rC.setText(text=textcontent)
        #
        return rC

    def _saveComponent(self):
        """ Save edited component back to session/instance directory
        """
        if (self.__verbose):
            self.__lfh.write("+ChemEditorWebAppWorker._saveComponent() Starting now\n")
        #
        self.__reqObj.setReturnFormat(return_format="json")
        rC = ResponseContent(reqObj=self.__reqObj, verbose=self.__verbose, log=self.__lfh)
        #
        classObj = SaveLigand(reqObj=self.__reqObj, verbose=self.__verbose, log=self.__lfh)
        textcontent = classObj.GetResult()
        if not textcontent:
            rC.setError(errMsg='failed')
        else:
            rC.setText(text=textcontent)
        #
        return rC

    def _CVSCommit(self):
        """ CVS commit to chemical component dictionary
        """
        if (self.__verbose):
            self.__lfh.write("+ChemEditorWebAppWorker._CVSCommit() Starting now\n")
        #
        self.__reqObj.setReturnFormat(return_format="json")
        rC = ResponseContent(reqObj=self.__reqObj, verbose=self.__verbose, log=self.__lfh)
        #
        cvsObj = CVSCommit(reqObj=self.__reqObj, verbose=self.__verbose, log=self.__lfh)
        myD = cvsObj.commit()
        if myD:
            rC.addDictionaryItems(myD)
        #
        return rC

    def _getEnumeration(self):
        """ CVS commit to chemical component dictionary
        """
        if (self.__verbose):
            self.__lfh.write("+ChemEditorWebAppWorker._getEnumeration() Starting now\n")
        #
        self.__reqObj.setReturnFormat(return_format="json")
        rC = ResponseContent(reqObj=self.__reqObj, verbose=self.__verbose, log=self.__lfh)
        #
        enumObj = Enumeration(reqObj=self.__reqObj, verbose=self.__verbose, log=self.__lfh)
        myD = enumObj.get()
        if myD:
            rC.addDictionaryItems(myD)
        #
        return rC

    def _getEntriesWithLigands(self):
        """Get depositions containing the requested ligand.

        Returns:
            ResponseContent: ResponseContent instance wrapping a list
                of entries
        """
        if (self.__verbose):
            self.__lfh.write("+ChemEditorWebAppWorker._getEntriesWithLigands() Starting now\n")
        #
        self.__reqObj.setReturnFormat(return_format="json")
        rC = ResponseContent(reqObj=self.__reqObj, verbose=self.__verbose, log=self.__lfh)
        #

        try:
            combine_db = DaInternalCombineDb(siteId=self.__siteId, verbose=True, log=self.__lfh)
            entries = combine_db.getEntriesWithLigand(self.__reqObj.getValue("ccid"))
            rC.setData(entries)
        except:  # noqa: E722 pylint: disable=bare-except
            rC.setError("Could not open a connection to the database")
        #
        return rC


if __name__ == '__main__':
    sTool = ChemEditorWebApp()
    d = sTool.doOp()
    for k_, v_ in d.items():
        sys.stdout.write("Key - %s  value - %r\n" % (k_, v_))
