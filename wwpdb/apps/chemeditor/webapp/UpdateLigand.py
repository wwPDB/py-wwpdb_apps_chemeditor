##
# File:  UpdateLigand.py
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

import os
import sys

#from mmcif.api.PdbxContainers     import *
from mmcif.io.PdbxReader         import PdbxReader
from mmcif.io.PdbxWriter         import PdbxWriter
from wwpdb.utils.config.ConfigInfo    import ConfigInfo
from wwpdb.apps.chemeditor.webapp.CVSCommit       import CVSBase
from wwpdb.io.file.mmCIFUtil                   import mmCIFUtil

class UpdateLigand(object):
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
        self.__pdbId = str(self.__reqObj.getValue('pdbid')).upper()
        self.__annotator = str(self.__reqObj.getValue('annotator'))
        self.__processing_site = str(self.__reqObj.getValue('processingsite'))
        if not self.__processing_site or self.__processing_site == 'null':
            self.__processing_site = 'RCSB'
        #
        self.__instanceid = str(self.__reqObj.getValue('instanceid'))
        self.__cclinkFile = ''
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
            self.__lfh.write("+UpdateLigand.__getSession() - creating/joining session %s\n" % self.__sessionId)
            self.__lfh.write("+UpdateLigand.__getSession() - session path %s\n" % self.__sessionPath)            

    def GetResult(self):
        self.__getInputCifData()
        self.__getCCLinkFile()
        self.__updateCif()
        self.__updateDefaultValue()
        return self.__returnData()

    def __getInputCifData(self):
        cif = self.__reqObj.getValue('cif')
        filePath = os.path.join(self.__sessionPath,'in.cif')
        f = open(filePath, 'w')
        f.write(cif + '\n')
        f.close()

    def __getCCLinkFile(self):
        topPath = str(self.__reqObj.getValue('TopSessionPath'))
        p_sessionId = str(self.__reqObj.getValue('parent_sessionid'))
        identifier = str(self.__reqObj.getValue('identifier'))
        if (not topPath) or (not p_sessionId) or (not identifier):
            return
        #
        list = []
        list.append(identifier)
        list.append(identifier.upper())
        list.append(identifier.lower())
        for id in list:
            filename = os.path.join(topPath, 'sessions', p_sessionId, id + '-cc-link.cif')
            if os.access(filename, os.R_OK):
                self.__cclinkFile = filename
                return
            #
        #

    def __updateCif(self):
        filePath = os.path.join(self.__sessionPath, 'in.cif')
        if not os.access(filePath, os.R_OK):
            return
        #
        script = os.path.join(self.__sessionPath, 'update-comp.csh')
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
        f.write('setenv BINPATH ' + self.__cI.get('SITE_ANNOT_TOOLS_PATH') + '/bin\n')
        f.write('#\n')
        if self.__instanceid and self.__cclinkFile:
            f.write('${BINPATH}/FindMissingCoordinate -comp in.cif -cclink ' + self.__cclinkFile + \
                    ' -instanceid ' + self.__instanceid + ' -log merge_log\n')
            f.write('#\n')
        #
        f.write("${CC_TOOLS}/annotateComp -vv -i in.cif -op " + \
                "'stereo-cactvs|aro-cactvs|descriptor-oe|descriptor-cactvs|" + \
                "descriptor-inchi|name-oe|name-acd|xyz-ideal-corina|xyz-model-h-oe|" + \
                "rename|fix' -o out.cif >& _comp_log\n")
        f.write('#\n')
        f.write('if ( -e out.cif ) then\n')
        f.write('    mv -f in.cif in.old.cif\n')
        f.write('    mv -f out.cif in.cif\n')
        f.write('endif\n')
        f.write('#\n')
        f.close()
        cmd = 'cd ' + self.__sessionPath + '; chmod 755 update-comp.csh; ./update-comp.csh >& comp_log'
        os.system(cmd)

    def __updateDefaultValue(self):
        filePath = os.path.join(self.__sessionPath, 'in.cif')
        if not os.access(filePath, os.R_OK):
            return
        #
        myDataList=[]
        ifh = open(filePath, 'r')
        pRd = PdbxReader(ifh)
        pRd.read(myDataList)
        ifh.close()
        #
        myBlock = myDataList[0]
        compCat = myBlock.getObj('chem_comp')
        compCat.setValue('NON-POLYMER', 'type', 0)
        compCat.setValue('HETAIN', 'pdbx_type', 0)
        id = compCat.getValue('id', 0)
        compCat.setValue(id, 'three_letter_code', 0)
        synonyms = self.__get_synonyms(id)
        if synonyms:
            compCat.setValue(synonyms, 'pdbx_synonyms', 0)
        #
        if self.__pdbId:
            compCat.setValue(self.__pdbId, 'pdbx_model_coordinates_db_code', 0)
        #
        site = compCat.getValue('pdbx_processing_site', 0)
        if site == '?' or site == '.' or site == 'ChemCompOB':
            compCat.setValue(self.__processing_site, 'pdbx_processing_site', 0)
        #
        auditCat = myBlock.getObj('pdbx_chem_comp_audit')
        site = auditCat.getValue('processing_site', 0)
        if site == '?' or site == '.' or site == 'ChemCompOB':
            auditCat.setValue(self.__processing_site, 'processing_site', 0)
        if self.__annotator:
            anno = auditCat.getValue('annotator', 0)
            if anno == '?' or anno == '.':
                auditCat.setValue(self.__annotator, 'annotator', 0)
        #
        ofh = open(filePath, 'w')
        pdbxW = PdbxWriter(ofh)
        pdbxW.write(myDataList)
        ofh.close()

    def __get_synonyms(self, id):
        self.__reqObj.setValue("sessionid", self.__sessionId)
        cvsUtil = CVSBase(reqObj=self.__reqObj, verbose=self.__verbose, log=self.__lfh)
        filePath = cvsUtil.getSandBoxFilePath(id)
        if os.access(filePath, os.F_OK):
            cifObj = mmCIFUtil(filePath=filePath)
            return cifObj.GetSingleValue('chem_comp', 'pdbx_synonyms')
        #
        return ''

    def __returnData(self):
        filePath = os.path.join(self.__sessionPath, 'in.cif')
        if not os.access(filePath, os.R_OK):
            return ''
        #
        f = open(filePath, 'r')
        data = f.read()
        f.close()
        return data
