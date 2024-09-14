##
# File:  CVSCommit.py
# Date:  05-Nov-2013
# Updates:
# 06-Sep-2024  zf replace ${CC_TOOLS}/checkComp with RcsbDpUtility's "annot-check-ccd-definition" operator
#                 added "begin_comment" & "end_comment" variables to control the "Continue commit to CVS" button
#
##
"""

This software was developed as part of the World Wide Protein Data Bank
Common Deposition and Annotation System Project

Copyright (c) 2013 wwPDB

This software is provided under a Creative Commons Attribution 3.0 Unported
License described at http://creativecommons.org/licenses/by/3.0/.

"""
__docformat__ = "restructuredtext en"
__author__ = "Zukang Feng"
__email__ = "zfeng@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.07"

import os
import shutil
import sys
import traceback
from datetime import datetime

from mmcif.api.DataCategory import DataCategory
from mmcif.io.PdbxReader import PdbxReader
from mmcif.io.PdbxWriter import PdbxWriter
from wwpdb.apps.chemeditor.webapp.ChemEditorBase import ChemEditorBase
from wwpdb.io.file.mmCIFUtil import mmCIFUtil
from wwpdb.utils.dp.RcsbDpUtility import RcsbDpUtility


class CVSCommit(ChemEditorBase):
    """  Class handle CVS commit to chemical component dictionary
    """
    def __init__(self, reqObj=None, verbose=False, log=sys.stderr):
        super(CVSCommit, self).__init__(reqObj=reqObj, verbose=verbose, log=log)
        self.__siteId = str(self._reqObj.getValue("WWPDB_SITE_ID"))
        self.__templatePath = os.path.join(self._cI.get("SITE_WEB_APPS_TOP_PATH"), "htdocs", "chemeditor")
        self.__cif = None
        self.__id = None
        self.__flag = None
        self.__sourceFile = None
        self.__reservedIdList = ["DRG", "INH", "LIG", "01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12", "13", "14", "15",
                                 "16", "17", "18", "19", "20", "21", "22", "23", "24", "25", "26", "27", "28", "29", "30", "31", "32", "33", "34", "35",
                                 "36", "37", "38", "39", "40", "41", "42", "43", "44", "45", "46", "47", "48", "49", "50", "51", "52", "53", "54", "55",
                                 "56", "57", "58", "59", "60", "61", "62", "63", "64", "65", "66", "67", "68", "69", "70", "71", "72", "73", "74", "75",
                                 "76", "77", "78", "79", "80", "81", "82", "83", "84", "85", "86", "87", "88", "89", "90", "91", "92", "93", "94", "95",
                                 "96", "97", "98", "99"]
        #
        self.__getData()

    def commit(self):
        """  Do CVS commit
        """
        message1 = self.__checkIDExisted()
        message2 = ""
        message3 = ""
        message4 = ""
        message5 = ""
        messageBackboneError = ""
        message6 = ""
        message7 = ""
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
                        # messageBackboneError = self.__checkPeptideBackboneAssigned()
                        if (
                            (not message4)
                            and (not message5)
                            and (not messageBackboneError)
                        ):
                            message6 = self.__commitCVS()
                        #
                    #
                if message4 or message5 or messageBackboneError:
                    message7 = self.__writeError2(
                        message4, message5, messageBackboneError
                    )
                #
            #
        #
        __cD = {}
        if message1 or message2 or message6:
            __cD["errorflag"] = True
            if message1:
                __cD["errortext"] = message1
            elif message2:
                __cD["errortext"] = message2
            else:
                __cD["errortext"] = message6
        elif message3:
            __cD["errorflag1"] = True
            __cD["errortext1"] = os.path.join(self._rltvSessionPath, "error1.html")
        elif message7:
            __cD["errorflag2"] = True
            __cD["errortext2"] = os.path.join(self._rltvSessionPath, "error2.html")
        else:
            __cD["errorflag"] = False
        return __cD

    def __getData(self):
        """ Get input data
        """
        self.__id = str(self._reqObj.getValue("id"))
        self.__cif = self._reqObj.getValue("cif")
        self.__flag = self._reqObj.getValue("force")
        self.__existingFlag = self._reqObj.getValue("existflag")
        #
        if not self.__id:
            return
        #
        self.getSandBoxFilePath(self.__id)
        self.__sourceFile = os.path.join(self._sessionPath, self.__id + ".cif")
        self.__targetPath = self._crpi.getFileDir(self.__id, "CC")

    def __checkIDExisted(self):
        """ Check if Ligand ID exists
        """
        if not self.__targetPath:
            return "CVS commit failed"
        #
        if self.__id.upper() in self.__reservedIdList:
            return "Ligand ID '" + self.__id + "' is a reserved ligand code."
        #
        return ""

    def __saveData(self):
        """ Save chemical component cif file
        """
        if self.__flag:
            if (not self.__sourceFile) or (not os.access(self.__sourceFile, os.R_OK)):
                return "CVS commit failed"
            #
            return ""
        #
        if (not self.__sourceFile) or (not self.__cif):
            return "CVS commit failed"
        #
        f = open(self.__sourceFile, "w")
        f.write(self.__cif + "\n")
        f.close()
        if not os.access(self.__sourceFile, os.R_OK):
            return "CVS commit failed"
        #
        return ""

    def __checkSynTaxError(self):
        """ Run syntax checking
        """
        logFilePath = os.path.join(self._sessionPath, "precheckComp.log")
        self._removeFile(logFilePath)
        #
        cmd = "cd " + self._sessionPath + " ; " + self._annotBashSetting() + " ${BINPATH}/precheckComp -i " + self.__id \
            + ".cif -id " + self.__id + " -o precheckComp.log > _precheckComp_log 2>&1 ; "
        self._runCmd(cmd)
        #
        message = ""
        if os.access(logFilePath, os.R_OK):
            f = open(logFilePath, "r")
            data = f.read()
            f.close()
            if (not data) or (not data.startswith("Syntax error:")):
                data += self.__checkParentCompId_and_updateSynonyms(not data)
            #
            if data:
                message = "yes"
                filePath = os.path.join(self._sessionPath, "error1.html")
                f = open(filePath, "w")
                f.write("<html>\n")
                f.write("<body>\n")
                f.write("<br><br>\n")
                f.write("<center><h4>Diagnostic Error Report</h4></center>\n")
                f.write("<pre>\n")
                f.write(data + "\n")
                f.write("</pre>\n")
                f.write("</body>\n")
                f.write("</html>\n")
                f.close()
            #
        #
        return message

    def __checkComp(self):
        """ Run CCD definition checking
        """
        reportFilePath = os.path.join(self._sessionPath, self.__id + ".report")
        self._removeFile(reportFilePath)
        #
        dp = RcsbDpUtility(tmpPath=self._sessionPath, siteId=self.__siteId, verbose=self._verbose, log=self._lfh)
        dp.imp(os.path.join(self._sessionPath, self.__id + ".cif"))
#
#       Allow to use system provided dataset file instead of default "annotation-pack/data/ascii/pcm_type_category_map.cif" file
#
#       dp.addInput(name="pcm_support_file", value=system provided dataset file name)
#
#       Check if CCD already existed and set "set_stripped_down_flag" flag
#
#       targetFile = os.path.join(self.__targetPath, self.__id + ".cif")
#       if os.access(targetFile, os.F_OK):
#           dp.addInput(name="set_stripped_down_flag", value="yes")
        #
        dp.addInput(name="set_ok_flag", value="yes")
        dp.op("annot-check-ccd-definition")
        dp.exp(reportFilePath)
        dp.cleanup()
        #
        message = ""
        if os.access(reportFilePath, os.R_OK):
            f = open(reportFilePath, "r")
            data = f.read()
            f.close()
            if data and (data.strip() != "Checking OK!"):
                message = data
            #
        #
        return message

    # def __checkCompOrg(self):
    #     """ Run dictionary checking
    #     """
    #     reportFilePath = os.path.join(self._sessionPath, self.__id + ".report")
    #     self._removeFile(reportFilePath)
    #     #
    #     cmd = "cd " + self._sessionPath + " ; " + self._ccToolsBashSetting() + self._mmcifDictBashSetting() \
    #         + " ${CC_TOOLS}/checkComp -v -i " + self.__id + ".cif -op checkhtml -dictsdb ${DICT_SDB_FILE} -version 3 -report " \
    #         + self.__id + ".report > _checkComp_log 2>&1 ; "
    #     self._runCmd(cmd)
    #     #
    #     message = ""
    #     if os.access(reportFilePath, os.R_OK):
    #         f = open(reportFilePath, "r")
    #         data = f.read()
    #         f.close()
    #         if data:
    #             if data.find("No errors found in") >= 0:
    #                 pass
    #             else:
    #                 start = data.find("<pre>")
    #                 end = data.find("</pre>")
    #                 if start >= 0 and end > start + 5:
    #                     message = data[start + 5:end]
    #                 start = data.find("+++[")
    #                 end = data.find("]+++")
    #                 if start >= 0 and end > start + 5:
    #                     message = data[start + 5:end]
    #                 #
    #             #
    #         #
    #     #
    #     return message

    def __checkDuplicate(self):
        """ Run duplicate checking
        """
        self._runMatchComp(self._sessionPath, self.__id + ".cif", self.__id + ".match", "'prefilter|strict|exact'")
        #
        matchFilePath = os.path.join(self._sessionPath, self.__id + ".match")
        if not os.access(matchFilePath, os.R_OK):
            return ""
        #
        ifh = open(matchFilePath, "r")
        data = ifh.read()
        ifh.close()
        #
        if not data:
            return ""
        #
        lines = data.split("\n")
        matched_ids = []
        if len(lines) > 1:
            for line in lines[1:]:
                records = line.split("\t")
                if (len(records) > 4):
                    matched_ids.append(records[4])
                #
            #
        #
        if matched_ids:
            message = "WARNING - " + self.__id + " matches " + ",".join(matched_ids)
            return message
        #
        return ""

    def __commitCVS(self):
        """ Run CVS check-in
        """
        if (not self.__sourceFile) or (not os.access(self.__sourceFile, os.R_OK)):
            return "CVS commit failed"
        #
        targetFile = os.path.join(self.__targetPath, self.__id + ".cif")
        if os.access(self.__targetPath, os.F_OK):
            if not os.access(targetFile, os.R_OK):
                return self.__targetPath + " exists. But " + targetFile + " does not exist. CVS commit failed."
            #
            self.__updateExistingValues(targetFile)
        #
        return self.__cvsCommit(self.__id, self.__sourceFile)

    def __writeError2(self, error1, error2, error3):
        """ Write error message html page
        """
        begin_comment = ""
        end_comment = ""
        errorlist = []
        if error1:
            lines = error1.split("\n")
            for line in lines:
                s = line.strip()
                if not s:
                    continue
                #
                if s.startswith("ERROR"):
                    begin_comment = "<!-- "
                    end_comment = " -->"
                #
                errorlist.append(s)
            #
        #
        if error2:
            errorlist.append(error2)
        #
        if error3:
            errorlist.append(error3)
        #
        if not errorlist:
            return ""
        #
        error_msg = ""
        for error in errorlist:
            error_msg += "<li>" + error + "</li>\n"
        #
        myD = {}
        myD["id"] = self.__id
        myD["sessionid"] = self._sessionId
        myD["existflag"] = self.__existingFlag
        myD["error"] = error_msg
        for item in ("newcodeflag", "instanceid", "parent_sessionid", "filesource", "identifier"):
            myD[item] = self._reqObj.getValue(item)
        #
        myD["begin_comment"] = begin_comment
        myD["end_comment"] = end_comment
        #
        filePath = os.path.join(self._sessionPath, "error2.html")
        f = open(filePath, "w")
        f.write(self.__processTemplate("cvs_commit_tmplt.html", myD) + "\n")
        f.close()
        return "yes"

    def __checkParentCompId_and_updateSynonyms(self, noErrorFlag):
        """
        """
        cifObj = mmCIFUtil(filePath=self.__sourceFile)
        #
        synonyms = ""
        synonymList = cifObj.GetValue("pdbx_chem_comp_synonyms")
        if synonymList:
            uniqueList = []
            for dic in synonymList:
                if ("name" not in dic) or (not dic["name"]) or (dic["name"] in uniqueList):
                    continue
                #
                uniqueList.append(dic["name"])
                if synonyms:
                    synonyms += "; "
                #
                synonyms += dic["name"]
            #
        #
        errorMessage = ""
        parent_comp_ids = cifObj.GetSingleValue("chem_comp", "mon_nstd_parent_comp_id")
        if parent_comp_ids:
            comp_ids = parent_comp_ids.replace("\n\r", " ").replace("\n", " ").replace("\r", " ").replace(";", " ").replace(",", " ")
            for comp_id in comp_ids.split(" "):
                if not comp_id:
                    continue
                #
                targetFile = self._crpi.getFilePath(comp_id, "CC")
                if (not targetFile) or (not os.access(targetFile, os.F_OK)):
                    errorMessage = "Incorrect parent compId: '" + parent_comp_ids + "'.\n\n"
                    break
                #
            #
        #
        if noErrorFlag and synonyms and (not errorMessage):
            cifObj.UpdateSingleRowValue("chem_comp", "pdbx_synonyms", 0, synonyms)
            cifObj.WriteCif(outputFilePath=self.__sourceFile)
        #
        return errorMessage

    # def __checkPeptideBackboneAssigned(self):
    #     """Check peptide CCDs have expected backbone and terminal flags

    #     For Peptide CCDs return error if they have:
    #       - <2 backbone atoms flagged as 'Y'
    #       - No N-terminal atoms flagged as 'Y'
    #       - No C-terminal atoms flagged as 'Y'
    #     """

    #     peptide_types = [
    #         "L-PEPTIDE LINKING",
    #         "PEPTIDE-LIKE",
    #         "D-PEPTIDE LINKING",
    #         "PEPTIDE LINKING",
    #         "L-PEPTIDE NH3 AMINO TERMINUS",
    #         "L-PEPTIDE COOH CARBOXY TERMINUS",
    #         "D-PEPTIDE COOH CARBOXY TERMINUS",
    #         "L-PEPTIDE NH3 AMINO TERMINUS",
    #         "D-PEPTIDE NH3 AMINO TERMINUS",
    #         "L-GAMMA-PEPTIDE, C-DELTA LINKING",
    #         "D-BETA-PEPTIDE, C-GAMMA LINKING",
    #         "D-GAMMA-PEPTIDE, C-DELTA LINKING",
    #         "L-BETA-PEPTIDE, C-GAMMA LINKING",
    #     ]

    #     error_message = ""

    #     if (not self.__sourceFile) or (not os.access(self.__sourceFile, os.R_OK)):
    #         return "WARNING - Backbone check failed, CCD source file could not be read."

    #     cifObj = mmCIFUtil(filePath=self.__sourceFile)

    #     # Set check to run only if peptide CCD
    #     ccd_pdbx_type = cifObj.GetSingleValue("chem_comp", "pdbx_type")
    #     ccd_type = cifObj.GetSingleValue("chem_comp", "type")

    #     run_check = False
    #     if ccd_pdbx_type.upper() == "ATOMP":
    #         run_check = True
    #     elif ccd_type.upper() in peptide_types:
    #         run_check = True

    #     if run_check:
    #         num_backbone_atoms_assigned = 0
    #         n_term_atoms_assigned = False
    #         c_term_atoms_assigned = False

    #         # Check backbone/terminal annotation
    #         chem_comp_atom = cifObj.GetValue("chem_comp_atom")
    #         for d in chem_comp_atom:
    #             if (
    #                 "pdbx_backbone_atom_flag" in d
    #                 and d["pdbx_backbone_atom_flag"] == "Y"
    #             ):
    #                 num_backbone_atoms_assigned += 1

    #             if (
    #                 "pdbx_n_terminal_atom_flag" in d
    #                 and d["pdbx_n_terminal_atom_flag"] == "Y"
    #             ):
    #                 n_term_atoms_assigned = True

    #             if (
    #                 "pdbx_c_terminal_atom_flag" in d
    #                 and d["pdbx_c_terminal_atom_flag"] == "Y"
    #             ):
    #                 c_term_atoms_assigned = True

    #         # Set error message
    #         if num_backbone_atoms_assigned < 2:
    #             error_message = (
    #                 "WARNING - Fewer than 2 backbone items flagged in peptide CCD."
    #                 " Check backbone and terminal atoms have been correctly assigned."
    #                 "\n\n"
    #             )

    #         elif (not n_term_atoms_assigned) and (not c_term_atoms_assigned):
    #             error_message = (
    #                 "WARNING - Terminal atom flags have not been assigned for peptide "
    #                 "CCD. Check terminal atoms have been correctly assigned.\n\n"
    #             )

    #         elif not n_term_atoms_assigned:
    #             error_message = (
    #                 "WARNING - N-terminal atom flag has not been assigned for peptide "
    #                 "CCD. Check N-terminal atoms have been correctly assigned.\n\n"
    #             )

    #         elif not c_term_atoms_assigned:
    #             error_message = (
    #                 "WARNING - C-terminal atom flag has not been assigned for peptide "
    #                 "CCD. Check C-terminal atoms have been correctly assigned.\n\n"
    #             )

    #     return error_message

    def __updateExistingValues(self, existingFile):
        """
        """
        if self.__existingFlag == "yes":
            return
        #
        cifObj = mmCIFUtil(filePath=existingFile)
        #
        myDataList = []
        ifh = open(self.__sourceFile, "r")
        pRd = PdbxReader(ifh)
        pRd.read(myDataList)
        ifh.close()
        #
        myBlock = myDataList[0]
        compCat = myBlock.getObj("chem_comp")
        for item in ("pdbx_initial_date", "pdbx_release_status", "pdbx_replaced_by", "pdbx_replaces"):
            val = cifObj.GetSingleValue("chem_comp", item)
            if val:
                compCat.setValue(val, item, 0)
            #
        #
        existing_audits = cifObj.GetValue("pdbx_chem_comp_audit")
        if existing_audits:
            items = ["comp_id", "action_type", "date", "processing_site", "annotator", "details"]
            newAuditCat = DataCategory("pdbx_chem_comp_audit")
            for item in items:
                newAuditCat.appendAttribute(item)
            #
            uniqueList = []
            row = 0
            for auditDict in existing_audits:
                uniqueValue = ""
                for item in items:
                    if item not in auditDict:
                        continue
                    #
                    if uniqueValue:
                        uniqueValue += "|"
                    #
                    uniqueValue += auditDict[item]
                #
                if uniqueValue in uniqueList:
                    continue
                #
                uniqueList.append(uniqueValue)
                #
                for item in items:
                    if item in auditDict:
                        newAuditCat.setValue(auditDict[item], item, row)
                    #
                #
                row += 1
            #
            auditCat = myBlock.getObj("pdbx_chem_comp_audit")
            if auditCat:
                today = datetime.today().strftime("%Y-%m-%d")
                iList = auditCat.getAttributeList()
                for rowDic in auditCat.getRowList():
                    auditDict = {}
                    for idxIt, itName in enumerate(iList):
                        if rowDic[idxIt] != '?' and rowDic[idxIt] != '.':
                            auditDict[itName] = rowDic[idxIt]
                        #
                    #
                    if not auditDict:
                        continue
                    #
                    if ("date" not in auditDict) or (auditDict["date"] != today):
                        continue
                    #
                    if ("action_type" not in auditDict) or (auditDict["action_type"] == "Create component"):
                        continue
                    #
                    uniqueValue = ""
                    for item in items:
                        if item not in auditDict:
                            continue
                        #
                        if uniqueValue:
                            uniqueValue += "|"
                        #
                        uniqueValue += auditDict[item]
                    #
                    if uniqueValue in uniqueList:
                        continue
                    #
                    uniqueList.append(uniqueValue)
                    #
                    for item in items:
                        if item in auditDict:
                            newAuditCat.setValue(auditDict[item], item, row)
                        #
                    #
                    row += 1
                #
            #
            myBlock.replace(newAuditCat)
        #
        ofh = open(self.__sourceFile, "w")
        pdbxW = PdbxWriter(ofh)
        pdbxW.write(myDataList)
        ofh.close()

    def __cvsCommit(self, ccId, sourceFilePath):
        """ Run CVS commit
        """
        if (not sourceFilePath) or (not os.access(sourceFilePath, os.R_OK)):
            return "CVS commit failed - Cannot update nonexistent file"
        #
        targetFile = self.getSandBoxFilePath(ccId)
        textList = []

        proj, rel_path = self._crpi.getCvsProjectInfo(ccId, "CC")

        relDir = os.path.dirname(rel_path)
        projFile = os.path.join(proj, rel_path)

        try:
            if targetFile and os.access(targetFile, os.F_OK):
                self._cvsAdmin.checkOut(projFile)
                shutil.copy2(sourceFilePath, targetFile)
            else:
                dstPath = self._crpi.getFileDir(ccId, "CC")
                targetFile = self._crpi.getFilePath(ccId, "CC")
                if (not os.access(dstPath, os.F_OK)):
                    os.makedirs(dstPath)
                    ok, text = self._cvsAdmin.add(proj, relDir)
                    if (not ok) and text:
                        textList.append(text)
                    #
                #
                shutil.copy2(sourceFilePath, targetFile)
                ok, text = self._cvsAdmin.add(proj, rel_path)
                if (not ok) and text:
                    textList.append(text)
                #
            #
            ok, text = self._cvsAdmin.commit(proj, rel_path)
            if (not ok) and text:
                textList.append(text)
            #
        except:  # noqa: E722 pylint: disable=bare-except
            textList.append("CVS commit failed - CVS update exception")
            traceback.print_exc(file=self._lfh)
        #
        self._cvsAdmin.cleanup()
        #
        if not os.access(targetFile, os.R_OK):
            textList.append("CVS commit " + ccId + " failed")
        #
        if textList:
            return "\n".join(textList)
        #
        return ""

    def __processTemplate(self, fn, parameterDict=None):
        """ Read the input HTML template data file and perform the key/value substitutions in the
            input parameter dictionary.

            :Params:
                ``parameterDict``: dictionary where
                key = name of subsitution placeholder in the template and
                value = data to be used to substitute information for the placeholder

            :Returns:
                string representing entirety of content with subsitution placeholders now replaced with data
        """
        if parameterDict is None:
            parameterDict = {}
        fPath = os.path.join(self.__templatePath, fn)
        ifh = open(fPath, "r")
        sIn = ifh.read()
        ifh.close()
        return (sIn % parameterDict)
