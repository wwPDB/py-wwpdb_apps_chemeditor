##
# File:  CVSCommit.py
# Date:  05-Nov-2013
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

import os, shutil, string, sys, traceback

from mmcif.api.PdbxContainers                  import *
from mmcif.api.DataCategory                    import DataCategory
from mmcif.io.PdbxReader                       import PdbxReader
from mmcif.io.PdbxWriter                       import PdbxWriter
from wwpdb.utils.config.ConfigInfo             import ConfigInfo
from wwpdb.io.file.mmCIFUtil                   import mmCIFUtil
from wwpdb.io.cvs.CvsAdmin                     import CvsSandBoxAdmin

class CVSBase(object):
    """  Class handle CVS commit to chemical component dictionary
    """
    def __init__(self, reqObj = None, verbose = False, log = sys.stderr):
        self._verbose = verbose
        self._lfh = log
        self._reqObj = reqObj
        self._sObj = None
        self._sessionId = None
        self._sessionPath = None
        self._rltvSessionPath = None
        self.__siteId = str(self._reqObj.getValue('WWPDB_SITE_ID'))
        self._cI = ConfigInfo(self.__siteId)
        self.__sbTopPath = self._cI.get('SITE_REFDATA_TOP_CVS_SB_PATH')
        self.__ccProjectName = self._cI.get('SITE_REFDATA_PROJ_NAME_CC')
        self._ccPath = os.path.join(self.__sbTopPath, self.__ccProjectName)
        #
        self.__getSession()
        #
        self._cvsAdmin = self.__setupCvs()

    def getSandBoxFilePath(self, ccId):
        """ Return full sandbox chemical component file path 
        """
        filePath = os.path.join(self._ccPath, ccId[0], ccId, ccId + '.cif')
        self._lfh.write('enter getSandBoxFilePath for ccId=%s filePath=%s\n' % (ccId, filePath))
        if os.access(filePath, os.F_OK):
            return filePath
        #
        self._lfh.write('getSandBoxFilePath running checkOut\n')
        self._cvsAdmin.checkOut(os.path.join(self.__ccProjectName, ccId[0], ccId))
        #self._cvsAdmin.cleanup()
        #
        return filePath

    def cvsCommit(self, ccId, sourceFilePath):
        """ Run CVS commit
        """
        if (not sourceFilePath) or (not os.access(sourceFilePath, os.R_OK)):
            return 'CVS commit failed - Cannot update nonexistent file'
        #
        targetFile = self.getSandBoxFilePath(ccId)
        textList = []
        try:
            if os.access(targetFile, os.F_OK):
                self._cvsAdmin.checkOut(os.path.join(self.__ccProjectName, ccId[0], ccId, ccId + '.cif'))
                shutil.copy2(sourceFilePath, targetFile)
            else:
                dstPath = os.path.join(self._ccPath, ccId[0], ccId)
                if (not os.access(dstPath, os.F_OK)):
                    os.makedirs(dstPath)
                    ok, text = self._cvsAdmin.add(self.__ccProjectName, os.path.join(ccId[0], ccId))
                    if (not ok) and text:
                        textList.append(text)
                    #
                #
                shutil.copy2(sourceFilePath, targetFile)
                ok, text = self._cvsAdmin.add(self.__ccProjectName, os.path.join(ccId[0], ccId, ccId + '.cif'))
                if (not ok) and text:
                    textList.append(text)
                #
            #
            ok, text = self._cvsAdmin.commit(self.__ccProjectName, os.path.join(ccId[0], ccId, ccId + '.cif'))
            if (not ok) and text:
                textList.append(text)
            #
        except:
            textList.append('CVS commit failed - CVS update exception')
            traceback.print_exc(file=self.__lfh)
        #
        self._cvsAdmin.cleanup()
        #
        if not os.access(targetFile, os.R_OK):
            textList.append('CVS commit ' + ccId + ' failed')
        #
        if textList:
            return '\n'.join(textList)
        #
        return ''

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
            self._lfh.write("+CVSBase.__getSession() - creating/joining session %s\n" % self._sessionId)
            self._lfh.write("+CVSBase.__getSession() - session path %s\n" % self._sessionPath)
        #

    def __setupCvs(self):
        """ Assign site specific chemical reference data CVS repository details
        """
        cvsRepositoryHost = self._cI.get('SITE_REFDATA_CVS_HOST')
        cvsRepositoryPath = self._cI.get('SITE_REFDATA_CVS_PATH')
        cvs = CvsSandBoxAdmin(tmpPath = self._sessionPath, verbose = self._verbose, log = self._lfh)
        cvs.setRepositoryPath(host=cvsRepositoryHost, path=cvsRepositoryPath)
        cvs.setAuthInfo(user='liganon3', password='lig1234')
        cvs.setSandBoxTopPath(self.__sbTopPath)
        return cvs

class CVSCommit(CVSBase):
    """  Class handle CVS commit to chemical component dictionary
    """
    def __init__(self, reqObj = None, verbose = False, log = sys.stderr):
        super(CVSCommit, self).__init__(reqObj = reqObj, verbose = verbose, log = log)
        self.__templatePath = os.path.join(self._cI.get('SITE_WEB_APPS_TOP_PATH'), 'htdocs', 'chemeditor')
        self.__cif = None
        self.__id = None
        self.__flag = None
        self.__sourceFile = None
        self.__getData()

    def commit(self):
        """  Do CVS commit
        """
        message1 = self.__checkIDExisted()
        message2 = ''
        message3 = ''
        message4 = ''
        message5 = ''
        message6 = ''
        message7 = ''
        #
        if not message1:
            if self.__flag:
                message6 = self.__commitCVS()
            else:
                message2 = self.__saveData()
                if not message2:
                    message3 = self.__checkSynTaxError()
                    if not message3:
                        message4 = self.__checkComp()
                        message5 = self.__checkDuplicate()
                        if not message4 and not message5:
                            message6 = self.__commitCVS()
                        #
                    #
                if message4 or message5:
                    message7 = self.__writeError2(message4, message5)
                #
            #
        #
        __cD={}
        if message1 or message2 or message6:
            __cD['errorflag']=True
            if message1:
                __cD['errortext']=message1
            elif message2:
                __cD['errortext']=message2
            else:
                __cD['errortext']=message6
        elif message3:
            __cD['errorflag1']=True
            __cD['errortext1']=os.path.join(self._rltvSessionPath, 'error1.html')
        elif message7:
            __cD['errorflag2']=True
            __cD['errortext2']=os.path.join(self._rltvSessionPath, 'error2.html')
        else:
            __cD['errorflag']=False
        return __cD

    def __getData(self):
        """ Get input data
        """
        self.__id = str(self._reqObj.getValue('id'))
        self.__cif = self._reqObj.getValue('cif')
        self.__flag = self._reqObj.getValue('force')
        #
        if not self.__id:
            return
        #
        self.getSandBoxFilePath(self.__id)
        self.__sourceFile = os.path.join(self._sessionPath, self.__id + '.cif')
        self.__targetPath = os.path.join(self._ccPath, self.__id[0], self.__id)

    def __checkIDExisted(self):
        """ Check if Ligand ID exists 
        """
        if not self.__targetPath:
            return 'CVS commit failed'
        return ''

    def __saveData(self):
        """ Save chemical component cif file
        """
        if self.__flag:
            return ''
        #
        if (not self.__sourceFile) or (not self.__cif):
            return 'CVS commit failed'
        #
        f = file(self.__sourceFile, 'w')
        f.write(self.__cif + '\n')
        f.close()
        if not os.access(self.__sourceFile, os.R_OK):
            return 'CVS commit failed'
        return ''

    def __checkSynTaxError(self):
        """ Run syntax checking
        """
        script = os.path.join(self._sessionPath, 'precheckComp.csh')
        f = file(script, 'w')
        f.write('#!/bin/tcsh -f\n')
        f.write('setenv RCSBROOT   ' + self._cI.get('SITE_ANNOT_TOOLS_PATH') + '\n')
        f.write('setenv BINPATH ${RCSBROOT}/bin\n')
        f.write('#\n')
        f.write('${BINPATH}/precheckComp -i ' + self.__id + '.cif -id ' + self.__id + ' -o precheckComp.log\n')
        f.write('#\n')
        f.close()
        cmd = 'cd ' + self._sessionPath + '; chmod 755 precheckComp.csh; ./precheckComp.csh'
        os.system(cmd)
        #
        message = ''
        filePath = os.path.join(self._sessionPath, 'precheckComp.log')
        if os.access(filePath, os.R_OK):
            f = file(filePath, 'r')
            data = f.read()
            f.close()
            if data:
                message = 'yes'
                filePath = os.path.join(self._sessionPath, 'error1.html')
                f = file(filePath, 'w')
                f.write('<html>\n')
                f.write('<body>\n')
                f.write('<br><br>\n')
                f.write('<center><h4>Diagnostic Error Report</h4></center>\n')
                f.write('<pre>\n')
                f.write(data + '\n')
                f.write('</pre>\n')
                f.write('</body>\n')
                f.write('</html>\n')
                f.close()
            #
        #
        return message

    def __checkComp(self):
        """ Run dictionary checking
        """
        script = os.path.join(self._sessionPath, 'checkComp.csh')
        f = file(script, 'w')
        f.write('#!/bin/tcsh -f\n')
        f.write('#\n')
        f.write('setenv CC_TOOLS   ' + self._cI.get('SITE_CC_APPS_PATH') + '/bin\n')
        f.write('setenv OE_DIR     ' + self._cI.get('SITE_CC_OE_DIR') + '\n')
        f.write('setenv OE_LICENSE ' + self._cI.get('SITE_CC_OE_LICENSE') + '\n')
        f.write('setenv ACD_DIR    ' + self._cI.get('SITE_CC_ACD_DIR') + '\n')
        f.write('setenv CACTVS_DIR ' + self._cI.get('SITE_CC_CACTVS_DIR') + '\n')
        f.write('setenv CORINA_DIR ' + self._cI.get('SITE_CC_CORINA_DIR') + '/bin\n')
        f.write('setenv INCHI_DIR  ' + self._cI.get('SITE_CC_INCHI_DIR') + '\n')
        f.write('setenv LD_LIBRARY_PATH ' + self._cI.get('SITE_CC_BABEL_LIB') + ':' + \
                os.path.join(self._cI.get('SITE_LOCAL_APPS_PATH'), 'lib') + ':' + \
                self._cI.get('SITE_CC_ACD_DIR') + '\n')
        f.write('setenv PDBX_DICT_PATH ' + self._cI.get('SITE_PDBX_DICT_PATH') + '\n')
        f.write('setenv DICT_NAME ' + self._cI.get('SITE_PDBX_V4_DICT_NAME') + '.sdb\n')
        f.write('#\n')
        f.write('${CC_TOOLS}/checkComp -v -i ' + self.__id + '.cif -op checkhtml -dictsdb ' + \
                '${PDBX_DICT_PATH}/${DICT_NAME} -version 4 -report ' + self.__id + '.report >& _log\n')
        f.write('#\n')
        f.close()
        cmd = 'cd ' + self._sessionPath + '; chmod 755 checkComp.csh; ./checkComp.csh'
        os.system(cmd)
        #
        message = ''
        filePath = os.path.join(self._sessionPath, self.__id + '.report')
        if os.access(filePath, os.R_OK):
            f = file(filePath, 'r')
            data = f.read()
            f.close()
            if data:
                if data.find('No errors found in') >= 0:
                    pass
                else:
                    start = data.find('<pre>')
                    end = data.find('</pre>')
                    if start >= 0 and end > start + 5:
                        message = data[start+5:end]
                    start = data.find('+++[')
                    end = data.find(']+++')
                    if start >= 0 and end > start + 5:
                        message = data[start+5:end]
                    #
                #
            #
        #
        return message

    def __checkDuplicate(self):
        """ Run duplicate checking
        """
        script = os.path.join(self._sessionPath, 'matchComp.csh')
        f = file(script, 'w')
        f.write('#!/bin/tcsh -f\n')
        f.write('#\n')
        f.write('setenv CC_TOOLS ' + self._cI.get('SITE_CC_APPS_PATH') + '/bin\n')
        f.write('setenv CC_DICT  ' + self._cI.get('SITE_CC_DICT_PATH') + '\n')
        f.write('#\n')
        f.write('set idxfile = "${CC_DICT}/Components-all-v3-r4.idx"\n')
        f.write('set sdbfile = "${CC_DICT}/Components-all-v3.sdb"\n')
        f.write('#\n')
        f.write('${CC_TOOLS}/matchComp -i ' + self.__id + '.cif -lib ${sdbfile} ' + \
                '-index ${idxfile} -type structure -o ' + self.__id + '.match' + \
                " -op 'prefilter|strict|exact' \n")
        f.write('#\n')
        f.close()
        cmd = 'cd ' + self._sessionPath + '; chmod 755 matchComp.csh; ./matchComp.csh'
        os.system(cmd)
        #
        message = ''
        filePath = os.path.join(self._sessionPath, self.__id + '.match')
        if os.access(filePath, os.R_OK):
            f = file(filePath, 'r')
            data = f.read()
            f.close()
            if data:
                lines = data.split('\n')
                matched_ids = []
                if len(lines) > 1:
                    for line in lines[1:]:
                        records = line.split('\t')
                        if (len(records) > 4):
                            matched_ids.append(records[4])
                        #
                    #
                #
                if matched_ids:
                    message = 'WARNING - ' + self.__id + ' matches ' + ','.join(matched_ids)
                #
            #
        #
        return message

    def __writeError2(self, error1, error2):
        """ Write error message html page
        """
        errorlist = []
        if error1:
            lines = error1.split('\n')
            for line in lines:
                s = line.strip()
                if not s:
                    continue
                errorlist.append(s)
            #
        #
        if error2:
            errorlist.append(error2)
        #
        if not errorlist:
            return ''
        #
        error_msg = ''
        for error in errorlist:
             error_msg += '<li>' + error + '</li>\n'
        #
        myD = {}
        myD['id'] = self.__id
        myD['sessionid'] = self._sessionId
        myD['error'] = error_msg
        #
        filePath = os.path.join(self._sessionPath, 'error2.html')
        f = file(filePath, 'w')
        f.write(self.__processTemplate('cvs_commit_tmplt.html', myD) + '\n')
        f.close()
        return 'yes'

    def __commitCVS(self):
        """ Run CVS check-in
        """
        if not os.access(self.__sourceFile, os.R_OK):
            return 'CVS commit failed'
        #
        targetFile = os.path.join(self.__targetPath, self.__id + '.cif')
        if os.access(self.__targetPath, os.F_OK):
            if not os.access(targetFile, os.R_OK):
                return self.__targetPath + ' exists. But ' + targetFile + ' does not exist. CVS commit failed.'
            #
            self.__updateExistingValues(targetFile)
        #
        return self.cvsCommit(self.__id, self.__sourceFile)

    def __updateExistingValues(self, existingFile):
        """
        """
        cifObj = mmCIFUtil(filePath=existingFile)
        #
        myDataList=[]
        ifh = open(self.__sourceFile, 'r')
        pRd = PdbxReader(ifh)
        pRd.read(myDataList)
        ifh.close()
        #
        myBlock = myDataList[0]
        compCat = myBlock.getObj('chem_comp')
        for item in ( 'pdbx_initial_date', 'pdbx_release_status', 'pdbx_replaced_by', 'pdbx_replaces' ):
            val = cifObj.GetSingleValue('chem_comp', item)
            if val:
                compCat.setValue(val, item, 0)
            #
        #
        existing_audits = cifObj.GetValue('pdbx_chem_comp_audit')
        if existing_audits:
            items = [ 'comp_id', 'action_type', 'date', 'processing_site', 'annotator', 'details' ]
            auditCat = myBlock.getObj('pdbx_chem_comp_audit')
            newAuditCat = DataCategory('pdbx_chem_comp_audit')
            for item in items:
                newAuditCat.appendAttribute(item)
            #
            row = 0
            for dir in existing_audits:
                for item in items:
                    if dir.has_key(item):
                        newAuditCat.setValue(dir[item], item, row)
                    #
                #
                row += 1
            #
            for item in items:
                try:
                    val = auditCat.getValue(item, 0)
                    if val and val != '?' and val != '.':
                        newAuditCat.setValue(val, item, row)
                    #
                except:
                    pass
                #
            #
            myBlock.replace(newAuditCat)
        #
        ofh = open(self.__sourceFile, 'w')
        pdbxW = PdbxWriter(ofh)
        pdbxW.write(myDataList)
        ofh.close()

    def __processTemplate(self,fn,parameterDict={}):
        """ Read the input HTML template data file and perform the key/value substitutions in the
            input parameter dictionary.
            
            :Params:
                ``parameterDict``: dictionary where
                key = name of subsitution placeholder in the template and
                value = data to be used to substitute information for the placeholder
                
            :Returns:
                string representing entirety of content with subsitution placeholders now replaced with data
        """
        fPath=os.path.join(self.__templatePath, fn)
        ifh=open(fPath,'r')
        sIn=ifh.read()
        ifh.close()
        return (  sIn % parameterDict )

if __name__ == '__main__':
    from wwpdb.utils.session.WebRequest                  import InputRequest
    siteId = 'WWPDB_DEPLOY_TEST_RU'
    os.environ["WWPDB_SITE_ID"] = siteId
    myReqObj = InputRequest({}, verbose = True, log = sys.stderr)
    myReqObj.setValue("WWPDB_SITE_ID",  siteId)
    myReqObj.setValue("SITE_REFDATA_CVS_USER", "liganon3")
    myReqObj.setValue("SITE_REFDATA_CVS_PASSWORD", "lig1234")
    testUtil = CVSBase(reqObj=myReqObj, verbose = True, log = sys.stderr)
    rtn_text = testUtil.cvsCommit('SO4', '/net/users/zfeng/SO4.cif')
    print('rtn_text=' + rtn_text)
    rtn_text = testUtil.cvsCommit('ZAG', '/net/users/zfeng/ZAG.cif')
    print ('rtn_text=' + rtn_text)

