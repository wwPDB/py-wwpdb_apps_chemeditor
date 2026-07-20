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
__author__ = "Zukang Feng"
__email__ = "zfeng@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.07"

import copy
import json
import os
import sys
import traceback

from operator import itemgetter

from mmcif.api.DataCategory import DataCategory
from mmcif.io.PdbxReader import PdbxReader
from mmcif.io.PdbxWriter import PdbxWriter

from wwpdb.apps.chemeditor.webapp.ChemEditorBase import ChemEditorBase
from wwpdb.io.file.mmCIFUtil import mmCIFUtil
from wwpdb.utils.dp.RcsbDpUtility import RcsbDpUtility

class UpdateLigand(ChemEditorBase):
    """
    """
    def __init__(self, reqObj=None, verbose=False, log=sys.stderr):
        super(UpdateLigand, self).__init__(reqObj=reqObj, verbose=verbose, log=log)
        self.__pdbId = str(self._reqObj.getValue("pdbid"))
        self.__annotator = str(self._reqObj.getValue("annotator"))
        self.__processing_site = str(self._reqObj.getValue("processingsite"))
        if (not self.__processing_site) or (self.__processing_site == "null") or (self.__processing_site == "NULL"):
            self.__processing_site = self._cI.get("SITE_NAME").upper()
        #
        self.__ccId = str(self._reqObj.getValue("ccid"))
        self.__instanceid = str(self._reqObj.getValue("instanceid"))
        self.__origCcId = ""
        if self.__instanceid != "":
            splitList = self.__instanceid.split("_")
            if len(splitList) == 1:
                self.__origCcId = splitList[0]
            elif len(splitList) == 5:
                self.__origCcId = splitList[2]
            #
        #
        self.__aaList = [ "ALA", "ARG", "ASN", "ASP", "CYS", "DAL", "DAR", "DSG", "DAS", "DCY", "DGN", "DGL", "DHI", "DIL", "DLE", \
                          "DLY", "DPN", "DPR", "DSN", "DTH", "DTR", "DTY", "DVA", "GLN", "GLU", "GLY", "HIS", "ILE", "LEU", "LYS", \
                          "MED", "MET", "PHE", "PRO", "PYL", "SEC", "SER", "THR", "TRP", "TYR", "VAL" ]
        #
        self.__metalElementList = [ "AC", "AG", "AL", "AM", "AU", "BA", "BE", "BH", "BI", "BK", "CA", "CD", "CE", "CF", "CM", "CN", "CO", "CR", "CS", "CU",
                                    "DB", "DS", "DY", "ER", "ES", "EU", "FE", "FL", "FM", "FR", "GA", "GD", "HF", "HG", "HO", "HS", "IN", "IR", "K", "LA",
                                    "LI", "LR", "LU", "LV", "MC", "MD", "MG", "MN", "MO", "MT", "NA", "NB", "ND", "NH", "NI", "NO", "NP", "OS", "PA", "PB",
                                    "PD", "PM", "PR", "PT", "PU", "RA", "RB", "RE", "RF", "RG", "RH", "RN", "RU", "SC", "SG", "SM", "SN", "SR", "TA", "TB",
                                    "TC", "TH", "TI", "TL", "TM", "U", "V", "W", "YB", "Y", "ZN", "ZR" ]
        #
        self.__changedCcIdentifier = False

    def GetResult(self):
        """
        """
        self._getInputCifData(os.path.join(self._sessionPath, "in.cif"))
        self.__getCCLinkFile()
        self._updateCompCif(self._sessionPath, "in.cif")
        #
        hasMetalCoordinationInfo = False
        polyatomic_metal_flag = str(self._reqObj.getValue("polyatomic_metal"))
        if polyatomic_metal_flag == "yes":
            hasMetalCoordinationInfo = self.__runMetalCoordinationTools()
        #
        self.__updateDefaultValue(hasMetalCoordinationInfo)
        return self.__returnData()

    def __getCCLinkFile(self):
        """ Fill in the missing coordinates from D_xxxxxxxxxx-cc-link.cif file
        """
        if not self.__instanceid:
            return
        #
        cclinkFile = self.__getFileFromParentSession("-cc-link.cif")
        if not cclinkFile:
            return
        #
        cmd = (
            "cd "
            + self._sessionPath
            + " ; "
            + self._annotBashSetting()
            + " ${BINPATH}/FindMissingCoordinate -comp in.cif -cclink "
            + cclinkFile
            + " -instanceid "
            + self.__instanceid
            + " -log merge_log > _merge_log 2>&1 ; "
        )
        self._runCmd(cmd)

    def __getFileFromParentSession(self, suffix):
        """ Get a file matched with the suffix from the parent session directory
        """
        pSessionDir = self.__getParentSessionDirectory()
        identifier = str(self._reqObj.getValue("identifier"))
        if (not pSessionDir) or (not identifier):
            return ""
        #
        identifierList = []
        identifierList.append(identifier)
        identifierList.append(identifier.upper())
        identifierList.append(identifier.lower())
        for Id in identifierList:
            filename = os.path.join(pSessionDir, Id + suffix)
            if os.access(filename, os.R_OK):
                return filename
            #
        #
        return ""

    def __getParentSessionDirectory(self):
        """ Get parent session directory
        """
        topPath = str(self._reqObj.getValue("TopSessionPath"))
        p_sessionId = str(self._reqObj.getValue("parent_sessionid"))
        if topPath and p_sessionId:
            return os.path.join(topPath, "sessions", p_sessionId)
        #
        return ""

    def __runMetalCoordinationTools(self):
        """ Run community software tools to get metal coordination geometry annotation. 
        """
        hasMetalCoordinationInfo = False
        #
        modelFile = self.__getFileFromParentSession("-model.cif")
        if modelFile:
            if (self.__origCcId != "") and (self.__ccId != "") and (self.__origCcId != self.__ccId):
                self.__changedCcIdentifier = True
                self.__updateCcIdForCifFile(self.__origCcId, os.path.join(self._sessionPath, "in.cif"))
            #
        #
        outputList = [ os.path.join(self._sessionPath, "servalcat.cif"), os.path.join(self._sessionPath, "metalcoord.json") ]
        #
        for filePath in outputList:
            self._removeFile(filePath)
        #
        dp = RcsbDpUtility(tmpPath=self._sessionPath, siteId=self._siteId, verbose=self._verbose, log=self._lfh)
        dp.setDebugMode(flag=True)
        dp.imp(os.path.join(self._sessionPath, "in.cif"))
        #
        if modelFile:
            dp.addInput(name="pdb", value=modelFile, type="file")
        #
        rt = dp.op("metal-metalcoord-update")
        if rt == 0:
            dp.expList(outputList)
            if os.access(os.path.join(self._sessionPath, "servalcat.cif"), os.R_OK) and \
               os.access(os.path.join(self._sessionPath, "metalcoord.json"), os.R_OK):
                hasMetalCoordinationInfo = True
            #
        #
        return hasMetalCoordinationInfo

    def __updateCcIdForCifFile(self, ccId, cifFilePath):
        """ Reset the CCID as input 'ccId'
        """
        if not os.access(cifFilePath, os.R_OK):
            return
        #
        myDataList = []
        ifh = open(cifFilePath)
        pRd = PdbxReader(ifh)
        pRd.read(myDataList)
        ifh.close()
        #
        self.__updateCcIdForDataBlock(ccId, myDataList[0])
        #
        ofh = open(cifFilePath, "w")
        pdbxW = PdbxWriter(ofh)
        pdbxW.write(myDataList)
        ofh.close()

    def __updateCcIdForDataBlock(self, ccId, myBlock):
        """ Reset the CCID as input 'ccId'
        """
        myBlock.setName(ccId)
        #
        for objName in myBlock.getObjNameList():
            catObj = myBlock.getObj(objName)
            if catObj is None:
                continue
            #
            attrbuteList = catObj.getAttributeList()
            if objName == "chem_comp":
                for item in ( "id", "three_letter_code" ):
                    if item in attrbuteList:
                        catObj.setValue(ccId, item, 0)
                    #
                #
            elif "comp_id" in attrbuteList:
                for row in range(catObj.getRowCount()):
                    catObj.setValue(ccId, "comp_id", row)
                #
            #
        #

    def __updateDefaultValue(self, hasMetalCoordinationInfo):
        filePath = os.path.join(self._sessionPath, "in.cif")
        if not os.access(filePath, os.R_OK):
            return
        #
        myDataList = []
        ifh = open(filePath)
        pRd = PdbxReader(ifh)
        pRd.read(myDataList)
        ifh.close()
        #
        myBlock = myDataList[0]
        compCat = myBlock.getObj("chem_comp")
        ccType = compCat.getValue("type", 0)
        if (ccType == "?") or (ccType == "."):
            compCat.setValue("NON-POLYMER", "type", 0)
        #
        pdbxType = compCat.getValue("pdbx_type", 0)
        if (pdbxType == "?") or (pdbxType == "."):
            compCat.setValue("HETAIN", "pdbx_type", 0)
        #
        ccId = compCat.getValue("id", 0)
        compCat.setValue(ccId, "three_letter_code", 0)
        synonyms = self.__get_synonyms(ccId)
        if synonyms:
            compCat.setValue(synonyms, "pdbx_synonyms", 0)
        #
        if self.__pdbId:
            pdbId = compCat.getValue("pdbx_model_coordinates_db_code", 0)
            if (pdbId == "?") or (pdbId == "."):
                compCat.setValue(self.__pdbId, "pdbx_model_coordinates_db_code", 0)
            #
        #
        if self.__processing_site:
            site = compCat.getValue("pdbx_processing_site", 0)
            if (site == "?") or (site == ".") or (site == "ChemCompOB"):
                compCat.setValue(self.__processing_site, "pdbx_processing_site", 0)
            #
            auditCat = myBlock.getObj("pdbx_chem_comp_audit")
            site = auditCat.getValue("processing_site", 0)
            if (site == "?") or (site == ".") or (site == "ChemCompOB"):
                auditCat.setValue(self.__processing_site, "processing_site", 0)
            #
        #
        if self.__annotator:
            anno = auditCat.getValue("annotator", 0)
            if (anno == "?") or (anno == "."):
                auditCat = myBlock.getObj("pdbx_chem_comp_audit")
                auditCat.setValue(self.__annotator, "annotator", 0)
            #
        #
        if hasMetalCoordinationInfo:
            auditCatCopy = None
            auditCat = myBlock.getObj("pdbx_chem_comp_audit")
            if auditCat is not None:
                auditCatCopy = copy.deepcopy(auditCat)
                myBlock.remove("pdbx_chem_comp_audit")
            #
            self.__integrateMetalCoordinationAnnotation(ccId, myBlock, compCat)
            #
            # Put "pdbx_chem_comp_audit" category at the end of data block.
            if auditCatCopy is not None:
                myBlock.append(auditCatCopy)
            #
        #
        if self.__changedCcIdentifier:
            self.__updateCcIdForDataBlock(self.__ccId, myDataList[0])
        #
        ofh = open(filePath, "w")
        pdbxW = PdbxWriter(ofh)
        pdbxW.write(myDataList)
        ofh.close()

    def __get_synonyms(self, ccId):
        """ Get synonyms from existing CCD definition.
        """
        existingCcdFilePath = self.getSandBoxFilePath(ccId)
        if (not existingCcdFilePath) or (not os.access(existingCcdFilePath, os.F_OK)):
            return ""
        #
        cifObj = mmCIFUtil(filePath=existingCcdFilePath)
        return cifObj.GetSingleValue("chem_comp", "pdbx_synonyms")

    def __integrateMetalCoordinationAnnotation(self, ccId, myBlock, compCat):
        """ Read "servalcat.cif", "metalcoord.json", and "findgeo.json" result files.
        """
        idealCoordData = self.__readServalcatCif(ccId)
        #
        annotationData,pcmList,chargeData = self.__readCoordinationJson(ccId, myBlock)
        #
        if len(idealCoordData) > 0:
            for atom_id,dataList in idealCoordData.items():
                if atom_id in chargeData:
                    dataList[0] = chargeData[atom_id]
                else:
                    dataList[0] = str(int(float(dataList[0])))
                #
            #
            self.__updateChemCompAtomCategory(myBlock, compCat, idealCoordData)
        #
        if len(annotationData) > 0:
            self.__updateChemCompAtomCoordinationCategories(myBlock, annotationData)
        #
        if len(pcmList) > 0:
            self.__updateChemCompPcmCategory(myBlock, pcmList)
            #
            attrbuteList = compCat.getAttributeList()
            if "pdbx_pcm" in attrbuteList:
                compCat.setValue("Y", "pdbx_pcm", 0)
            else:
                compCat.appendAttributeExtendRows("pdbx_pcm", defaultValue="Y")
            #
        #

    def __readServalcatCif(self, ccId):
        """ Read "servalcat.cif" file
        """
        myDataList = []
        ifh = open(os.path.join(self._sessionPath, "servalcat.cif"))
        pRd = PdbxReader(ifh)
        pRd.read(myDataList)
        ifh.close()
        #
        idealCoordData = {}
        for dataBlock in myDataList:
            atomCat = dataBlock.getObj("chem_comp_atom")
            if atomCat is None:
                continue
            #
            iList = atomCat.getAttributeList()
            itNameNotFound = False
            for itName in ( "comp_id", "atom_id", "charge", "model_Cartn_x", "model_Cartn_y", "model_Cartn_z" ):
                if itName not in iList:
                    itNameNotFound = True
                    break
                #
            #
            if itNameNotFound:
                continue
            #
            incorrectData = False
            for row in range(atomCat.getRowCount()):
                dataVec = []
                for itName in ( "comp_id", "atom_id", "charge", "model_Cartn_x", "model_Cartn_y", "model_Cartn_z" ):
                    try:
                        val = atomCat.getValue(itName, row)
                        if (val is not None) and (val != "?") and (val != "."):
                            dataVec.append(val)
                        #
                    except:
                        traceback.print_exc(file=self._lfh)
                    #
                #
                if (len(dataVec) != 6) or (dataVec[0] != ccId):
                    incorrectData = True
                    break
                #
                idealCoordData[dataVec[1]] = dataVec[2:]
            #
            if incorrectData:
                idealCoordData = {}
            #
        #
        return idealCoordData

    def __readCoordinationJson(self, ccId, myBlock):
        """ Read "metalcoord.json" and "findgeo.json" files.
        """
        annotationData = {}
        pcmList = []
        chargeData = {}
        #
        coordinationList = []
        findgeoJsonFile = self.__getFileFromParentSession("_findgeo-annotation.json")
        if findgeoJsonFile and self.__isValidJsonFile(findgeoJsonFile, "FindGeo"):
            coordinationList.append(( "FindGeo", findgeoJsonFile ))
        #
        metalcoordJsonFile = self.__getFileFromParentSession("_metalcoord-annotation.json")
        if metalcoordJsonFile and self.__isValidJsonFile(metalcoordJsonFile, "MetalCoord"):
            coordinationList.append(( "MetalCoord", metalcoordJsonFile ))
        #
        ligandOnlyFlag = False
        modifiedMetalAtomNameMap = {}
        if len(coordinationList) == 0:
            metalCoordJsonFile = os.path.join(self._sessionPath, "metalcoord.json")
            if os.access(metalCoordJsonFile, os.R_OK) and self.__isValidJsonFile(metalCoordJsonFile, "MetalCoord"):
                coordinationList.append(( "MetalCoord", metalCoordJsonFile ))
                ligandOnlyFlag = True
            else:
                return annotationData,pcmList,chargeData
            #
        else:
            modifiedMetalAtomNameMap = self.__getModifiedMetalAtomNameMap(myBlock)
        #
        for resultTupl in coordinationList:
            with open(resultTupl[1]) as DATA:
                jsonObj = json.load(DATA)
                for coordObj in jsonObj:
                    dataList = []
                    for item in ( "residue", "metal", "coordination", "class", "class_generic", "class_abbr" ):
                        val = ""
                        if item in coordObj:
                            val = str(coordObj[item])
                            if (val != "") and (val != "?") and (val != ".") and (val.lower() != "irregular"):
                                dataList.append(val)
                            #
                        #
                    #
                    tag = ""
                    if "tag" in coordObj:
                        tag = str(coordObj["tag"])
                    #
                    if (len(dataList) == 6) and (dataList[0] == ccId) and (tag.lower() == "regular"):
                        if not ligandOnlyFlag:
                            # Update the metal atom name if it is changed inside chemical editor
                            if dataList[1] in modifiedMetalAtomNameMap:
                                dataList[1] = modifiedMetalAtomNameMap[dataList[1]]
                            #
                        #
                        dataList[2] = int(dataList[2])
                        descriptor = ""
                        if "descriptor" in coordObj:
                            val = str(coordObj["descriptor"])
                            if (val != "") and (val != "?") and (val != ".") and (val.lower() != "irregular"):
                                descriptor = val
                            #
                        #
                        dataList.append(resultTupl[0])
                        #
                        if dataList[1] in annotationData:
                            foundSameAnnotation = False
                            for existList in annotationData[dataList[1]]:
                                count = 0
                                for i in range(len(dataList)):
                                    if dataList[i] == existList[i]:
                                        count += 1
                                    #
                                #
                                if count != len(dataList):
                                    continue
                                #
                                foundSameAnnotation = True
                                #
                                if descriptor != "":
                                    foundSameDescriptor = False
                                    for existingDescriptor in existList[7]:
                                        if existingDescriptor == descriptor:
                                            foundSameDescriptor = True
                                            break
                                        #
                                    #
                                    if not foundSameDescriptor:
                                        existList[7].append(descriptor)
                                    #
                                #
                                break
                            #
                            if not foundSameAnnotation:
                                descriptorList = []
                                if descriptor != "":
                                    descriptorList.append(descriptor)
                                #
                                dataList.append(descriptorList)
                                annotationData[dataList[1]].append(dataList)
                            #
                        else:
                            descriptorList = []
                            if descriptor != "":
                                descriptorList.append(descriptor)
                            #
                            dataList.append(descriptorList)
                            annotationData[dataList[1]] = [ dataList ]
                        #
                        if "sphere" in coordObj:
                            for sphereObj in coordObj["sphere"]:
                                dataVec = []
                                for item in ( "residue", "name" ):
                                    val = str(sphereObj[item])
                                    if (val != "") and (val != "?") and (val != "."):
                                        dataVec.append(val)
                                    #
                                #
                                if (len(dataVec) != 2) or (dataVec[0] == ccId) or (dataVec[0] not in self.__aaList):
                                    continue
                                #
                                dataVec.insert(0, dataList[1])
                                dataVec.insert(0, dataList[0])
                                #
                                foundLink = False
                                for dataVec1 in pcmList: 
                                    count = 0
                                    for i in range(len(dataVec)):
                                        if dataVec[i] == dataVec1[i]:
                                            count += 1
                                        #
                                    #
                                    if count == len(dataVec):
                                        foundLink = True
                                        break
                                    #
                                #
                                if not foundLink:
                                    pcmList.append(dataVec)
                                #
                            #
                        #
                    #
                    chargeList = []
                    for item in ( "residue", "metal", "redox_active", "oxidation_state" ):
                        val = ""
                        if item in coordObj:
                            val = str(coordObj[item])
                            if (val != "") and (val != "?") and (val != ".") and (val.lower() != "irregular"):
                                chargeList.append(val)
                            #
                        #
                    #
                    if (len(chargeList) == 4) and (chargeList[0] == ccId):
                        # Update the metal atom name if it is changed inside chemical editor
                        if chargeList[1] in modifiedMetalAtomNameMap:
                            chargeList[1] = modifiedMetalAtomNameMap[chargeList[1]]
                        #
                        if chargeList[1] in chargeData:
                            continue
                        #
                        if chargeList[2].upper() == "Y":
                            chargeData[chargeList[1]] = "?"
                        else:
                            chargeData[chargeList[1]] = chargeList[3]
                        #
                    #
                #
            #
        #
        return annotationData,pcmList,chargeData

    def __isValidJsonFile(self, jsonFilePath, program):
        """ Check if the json file has valid data
        """
        try:
            with open(jsonFilePath) as DATA:
                jsonObj = json.load(DATA)
                if len(jsonObj) == 0:
                    self._lfh.write("Run '%s' failed: no return result.\n" % program)
                    return False
                #
                if "error" in jsonObj:
                    self._lfh.write("Run '%s' failed: %s.\n" % (program, jsonObj["error"]))
                    return False
                #
            #
        except:
            traceback.print_exc(file=self._lfh)
            return False
        #
        return True

    def __getModifiedMetalAtomNameMap(self, myBlock):
        """ Check if any atom name(s) has(ve) been changed inside chemical editor. Only return changed metal atom anme mapping.
        """
        modifiedMetalAtomNameMap = {}
        #
        if not self.__instanceid:
            return modifiedMetalAtomNameMap
        #
        ligandInstanceFile = self.__getLigandInstanceFile(".cif_org")
        if not ligandInstanceFile:
            ligandInstanceFile = self.__getLigandInstanceFile(".cif")
        #
        if not ligandInstanceFile:
            return modifiedMetalAtomNameMap
        #
        myDataList = []
        ifh = open(ligandInstanceFile)
        pRd = PdbxReader(ifh)
        pRd.read(myDataList)
        ifh.close()
        #
        orgCoordMetalAtomNameMap = self.__getCoordMetalAtomNameMap(myDataList[0])
        modCoordMetalAtomNameMap = self.__getCoordMetalAtomNameMap(myBlock)
        #
        for key,val in orgCoordMetalAtomNameMap.items():
            if key not in modCoordMetalAtomNameMap:
                continue
            #
            if val != modCoordMetalAtomNameMap[key]:
                modifiedMetalAtomNameMap[val] = modCoordMetalAtomNameMap[key]
            #
        #
        return modifiedMetalAtomNameMap

    def __getCoordMetalAtomNameMap(self, myBlock):
        """ Read "chem_comp_atom" category and get coordinates vs atom name mapping
        """
        coordMetalAtomNameMap = {}
        #
        atomCat = myBlock.getObj("chem_comp_atom")
        if atomCat is None:
            return coordMetalAtomNameMap
        #
        iList = atomCat.getAttributeList()
        for row in range(atomCat.getRowCount()):
            try:
                dataList = []
                for itName in ( "atom_id", "type_symbol", "model_Cartn_x", "model_Cartn_y", "model_Cartn_z" ):
                    if itName in iList:
                        val = atomCat.getValue(itName, row)
                        if (val != "") and (val != "?") and (val != "."):
                            dataList.append(val)
                        #
                    #
                #
                if (len(dataList) != 5) or (dataList[1].upper() not in self.__metalElementList):
                    continue
                #
                self._lfh.write("Inserting %s -> %s\n" % ("_".join(dataList[2:]), dataList[0]))
                coordMetalAtomNameMap["_".join(dataList[2:])] = dataList[0]
            except:
                pass
            #
        #
        return coordMetalAtomNameMap

    def __getLigandInstanceFile(self, suffix):
        """ Get instance ligand definition cif file
        """
        pSessionDir = self.__getParentSessionDirectory()
        subpath = str(self._reqObj.getValue("subpath"))
        if (not pSessionDir) or (not subpath):
            return ""
        #
        filename = os.path.join(pSessionDir, subpath, self.__instanceid, self.__instanceid + suffix)
        if os.access(filename, os.R_OK):
            return filename
        #
        return ""

    def __updateChemCompAtomCategory(self, myBlock, compCat, idealCoordData):
        """ Integrate ideal coordinates and charge information
        """
        atomCat = myBlock.getObj("chem_comp_atom")
        if atomCat is None:
            return
        #
        iList = atomCat.getAttributeList()
        itNameNotFound = False
        for itName in ( "atom_id", "charge", "pdbx_model_Cartn_x_ideal", "pdbx_model_Cartn_y_ideal", "pdbx_model_Cartn_z_ideal" ):
            if itName not in iList:
                itNameNotFound = True
                break
            #
        #
        if itNameNotFound:
            return
        #
        has_redox_active_metal = False
        total_charge = 0
        for row in range(atomCat.getRowCount()):
            try:
                atom_id = atomCat.getValue("atom_id", row)
                if atom_id in idealCoordData:
                    atomCat.setValue(idealCoordData[atom_id][0], "charge", row)
                    atomCat.setValue(idealCoordData[atom_id][1], "pdbx_model_Cartn_x_ideal", row)
                    atomCat.setValue(idealCoordData[atom_id][2], "pdbx_model_Cartn_y_ideal", row)
                    atomCat.setValue(idealCoordData[atom_id][3], "pdbx_model_Cartn_z_ideal", row)
                #
                charge = atomCat.getValue("charge", row)
                if (charge == "?") or (charge == "."):
                    has_redox_active_metal = True
                else:
                    try:
                        icharge = int(charge)
                        total_charge += icharge
                    except:
                        pass
                    #
                #
            except:
                traceback.print_exc(file=self._lfh)
            #
        #
        if has_redox_active_metal:
            compCat.setValue("?", "pdbx_formal_charge", 0)
        else:
            compCat.setValue(str(total_charge), "pdbx_formal_charge", 0)
        #

    def __updateChemCompAtomCoordinationCategories(self, myBlock, annotationData):
        """ Integrate metal atom coordination information
        """
        existingAnnotData = self.__readCurrentChemCompAtomCoordinationCategories(myBlock)
        #
        # Merging new coordination data with existing coordination data
        #
        for atom_id,dataList in annotationData.items():
            if atom_id not in existingAnnotData:
                existingAnnotData[atom_id] = dataList
            else:
                for dataVec1 in dataList:
                    existingFlag = False
                    for dataVec2 in existingAnnotData[atom_id]:
                        isSameFlag = True
                        for i in range(7): 
                            if dataVec1[i] != dataVec2[i]:
                                isSameFlag = False
                            #
                        #
                        if isSameFlag:
                            existingFlag = True
                            for descriptor in dataVec1[7]:
                                if descriptor not in dataVec2[7]:
                                    dataVec2[7].append(descriptor)
                                #
                            #
                            break
                        #
                    #
                    if not existingFlag:
                        existingAnnotData[atom_id].append(dataVec1)
                    #
                #
            #
        #
        allDataList = []
        for atom_id,dataList in existingAnnotData.items():
            allDataList.extend(dataList)
        #
        if len(allDataList) > 1:
            allDataList.sort(key=itemgetter(1, 2, 4, 6))
        #
        # Create coordDataList and sphereDataList for "pdbx_chem_comp_atom_coordination" and 
        # "pdbx_chem_comp_atom_coordination_sphere" categories 
        #
        keyMap = {}
        coordDataList = []
        sphereDataList = []
        for dataVec in allDataList:
            key = dataVec[0] + "_" + dataVec[1] + "_" + str(dataVec[2]) + "_" + dataVec[4]
            if key not in keyMap:
                keyMap[key] = str(len(keyMap) + 1)
            #
            cDataList = []
            cDataList.append(keyMap[key])
            for idx in range(7):
                cDataList.append(str(dataVec[idx]))
            #
            coordDataList.append(cDataList)
            #
            for descriptor in dataVec[7]:
                sDataList = []
                sDataList.append(str(len(sphereDataList) + 1))
                sDataList.append(keyMap[key])
                sDataList.append(dataVec[0])
                sDataList.append(dataVec[1])
                sDataList.append(descriptor)
                sDataList.append(dataVec[6])
                sphereDataList.append(sDataList)
            #
        #
        if len(coordDataList) > 0:
            items = ( "geometry_id", "comp_id", "atom_id", "number", "geometry", "geometry_generic", "geometry_abbr", "provenance" )
            self.__updateCifDataObj(myBlock, "pdbx_chem_comp_atom_coordination", items, coordDataList)
        #
        if len(sphereDataList) > 0:
            items = ( "id", "geometry_id", "comp_id", "atom_id", "descriptor", "provenance" )
            self.__updateCifDataObj(myBlock, "pdbx_chem_comp_atom_coordination_sphere", items, sphereDataList)
        #

    def __readCurrentChemCompAtomCoordinationCategories(self, myBlock):
        """ Read current metal atom coordination information from "pdbx_chem_comp_atom_coordination" and 
            "pdbx_chem_comp_atom_coordination_sphere" categories
        """
        existingAnnotData = {}
        #
        coordCat = myBlock.getObj("pdbx_chem_comp_atom_coordination")
        if coordCat is None:
            return existingAnnotData
        #
        dataMap = {}
        for row in range(coordCat.getRowCount()):
            dataVec = []
            for itName in ( "comp_id", "atom_id", "number", "geometry", "geometry_generic", "geometry_abbr", "provenance" ):
                try:
                    val = coordCat.getValue(itName, row)
                    if (val is not None) and (val != "?") and (val != "."):
                        dataVec.append(val)
                    #
                except:
                    traceback.print_exc(file=self._lfh)
                #
            #
            if len(dataVec) != 7:
                continue
            #
            dataVec[2] = int(dataVec[2])
            dataVec.append([])
            try:
                val = coordCat.getValue("geometry_id", row)
                dataMap[val + "_" + dataVec[0] + "_" + dataVec[1] + "_" + dataVec[6]] = dataVec
            except:
                traceback.print_exc(file=self._lfh)
            #
        #
        if len(dataMap) == 0:
            return existingAnnotData
        #
        sphereCat = myBlock.getObj("pdbx_chem_comp_atom_coordination_sphere")
        if sphereCat is not None:
            for row in range(sphereCat.getRowCount()):
                dataVec = []
                for itName in ( "geometry_id", "comp_id", "atom_id", "provenance", "descriptor" ):
                    try:
                        val = sphereCat.getValue(itName, row)
                        if (val is not None) and (val != "?") and (val != "."):
                            dataVec.append(val)
                        #
                    except:
                        traceback.print_exc(file=self._lfh)
                    #
                #
                if len(dataVec) != 5:
                    continue
                #
                key = "_".join(dataVec[:-1])
                if key in dataMap:
                    dataMap[key][7].append(dataVec[-1])
                #
            #
        #
        for key,dataVec in dataMap.items():
            if dataVec[1] in existingAnnotData:
                existingAnnotData[dataVec[1]].append(dataVec)
            else:
                existingAnnotData[dataVec[1]] = [ dataVec ]
            #
        #
        return existingAnnotData

    def __updateCifDataObj(self, myBlock, categoryName, itemList, dataList):
        """ Update cif category object.
        """
        catObj = DataCategory(categoryName)
        for item in itemList:
            catObj.appendAttribute(item)
        #
        row = 0
        for dataVec in dataList:
            for idx,item in enumerate(itemList):
                catObj.setValue(str(dataVec[idx]), item, row)
            #
            row += 1
        #
        if myBlock.getObj(categoryName) is not None:
            myBlock.replace(catObj)
        else:
            myBlock.append(catObj)
        #

    def __updateChemCompPcmCategory(self, myBlock, pcmList):
        """ Update "pdbx_chem_comp_pcm" category
        """
        existingPcmList = self.__readCurrentChemCompPcmCategory(myBlock)
        #
        for dataVec in pcmList:
            found = False
            for pcmVec in existingPcmList:
                if (dataVec[0] == pcmVec[1]) and (dataVec[1] == pcmVec[7]) and (dataVec[2] == pcmVec[2]) and (dataVec[3] == pcmVec[8]):
                    found = True
                    break
                #
            #
            if found:
                continue
            #
            dataList = []
            dataList.append(str(len(existingPcmList) + 1))
            dataList.append(dataVec[0])
            dataList.append(dataVec[2])
            dataList.append("None")
            dataList.append("Metal coordination")
            if (dataVec[3] == "N") or (dataVec[3] == "O") or (dataVec[3] == "OXT"):
                dataList.append("Amino-acid backbone")
            else:
                dataList.append("Amino-acid side chain")
            #
            dataList.append("Any position")
            dataList.append(dataVec[1])
            dataList.append(dataVec[3])
            dataList.append("?")
            dataList.append("?")
            dataList.append("?")
            existingPcmList.append(dataList)
        #
        items = ( "pcm_id", "comp_id", "modified_residue_id", "type", "category", "position", "polypeptide_position", \
                  "comp_id_linking_atom", "modified_residue_id_linking_atom", "uniprot_specific_ptm_accession", \
                  "uniprot_generic_ptm_accession", "first_instance_model_db_code" )
        #
        self.__updateCifDataObj(myBlock, "pdbx_chem_comp_pcm", items, existingPcmList)

    def __readCurrentChemCompPcmCategory(self, myBlock):
        """ Read data content from "pdbx_chem_comp_pcm" category
        """
        existingPcmList = []
        #
        catObj = myBlock.getObj("pdbx_chem_comp_pcm")
        if catObj is None:
            return existingPcmList
        #
        attrbuteList = catObj.getAttributeList()
        #
        for row in range(catObj.getRowCount()):
            dataVec = []
            for item in ( "pcm_id", "comp_id", "modified_residue_id", "type", "category", "position", "polypeptide_position", \
                          "comp_id_linking_atom", "modified_residue_id_linking_atom", "uniprot_specific_ptm_accession", \
                          "uniprot_generic_ptm_accession", "first_instance_model_db_code" ):
                if item in attrbuteList:
                    dataVec.append(catObj.getValue(item, row))
                else:
                    dataVec.append("?")
                #
            #
            existingPcmList.append(dataVec)
        #
        return existingPcmList

    def __returnData(self):
        """ Return "in.cif" file's textual data context.
        """
        filePath = os.path.join(self._sessionPath, "in.cif")
        if not os.access(filePath, os.R_OK):
            return ""
        f = open(filePath)
        data = f.read()
        f.close()
        return data
