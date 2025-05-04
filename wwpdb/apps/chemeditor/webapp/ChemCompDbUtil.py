##
# File:  ChemCompDbUtil.py
# Date:  07-Mar-2025
#
# Updated
"""
Wrapper for utilities for database loading of chemical reference data
"""

__author__ = "Zukang Feng"
__email__ = "zfeng@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.07"

import os
import sys
import traceback

from mmcif.io.IoAdapterCore import IoAdapterCore

from wwpdb.utils.db.ChemCompSchemaDef import ChemCompSchemaDef
from wwpdb.utils.db.MyConnectionBase import MyConnectionBase
from wwpdb.utils.db.MyDbUtil import MyDbQuery
from wwpdb.utils.db.SchemaDefLoader import SchemaDefLoader


class ChemCompDbUtil(MyConnectionBase):
    """Wrapper for utilities for database loading of chemical reference data"""

    def __init__(self, reqObj=None, verbose=False, log=sys.stderr):
        self.__reqObj = reqObj
        self.__siteId = self.__reqObj.getValue("WWPDB_SITE_ID")
        super(ChemCompDbUtil, self).__init__(siteId=self.__siteId, verbose=verbose, log=log)
        self.__verbose = verbose
        self.__lfh = log
        # self.__debug = verbose
        #
        self.__sObj = self.__reqObj.newSessionObj()
        self.__sessionPath = self.__sObj.getPath()
        self.__ioObj = IoAdapterCore(verbose=self.__verbose, log=self.__lfh)
        self.setResource(resourceName="CC")

    def loadCCD(self, ccdFilePath=None):
        """Load CCD definition into compv4 database"""
        if self.__verbose:
            self.__lfh.write("+ChemCompDbUtil.loadCCD() - loading %s\n" % ccdFilePath)
        if (ccdFilePath is None) or (not os.access(ccdFilePath, os.R_OK)):
            return False
        try:
            ok = self.openConnection()
            if ok:
                sdl = SchemaDefLoader(
                    schemaDefObj=ChemCompSchemaDef(),
                    ioObj=self.__ioObj,
                    dbCon=self._dbCon,
                    workPath=self.__sessionPath,
                    cleanUp=False,
                    warnings="error",
                    verbose=self.__verbose,
                    log=self.__lfh,
                )
                ok = sdl.load(inputPathList=[ccdFilePath], loadType="batch-insert", deleteOpt="selected")
                self.closeConnection()
            elif self.__verbose:
                self.__lfh.write("+ChemCompDbUtil.loadCCD() - database connection failed\n")
        except:  # noqa: E722 pylint: disable=bare-except
            self.closeConnection()
            if self.__verbose:
                self.__lfh.write("+ChemCompDbUtil.loadCCD():\n")
                traceback.print_exc(file=self.__lfh)
            ok = False
        return ok

    def searchSameCCDs(self, ccdFilePath=None):
        """Search same CCDs with same OpenEye stereo SMILES descriptor, same CACTVS stereo SMILES descriptor,
        and same InChI descriptor.
        """
        if self.__verbose:
            self.__lfh.write("+ChemCompDbUtil.searchSameCCDs() - searching for %s\n" % ccdFilePath)
        if (ccdFilePath is None) or (not os.access(ccdFilePath, os.R_OK)):
            return []
        try:
            containerList = self.__ioObj.readFile(ccdFilePath)
            if (containerList is None) or (len(containerList) == 0):
                return []
            descriptorRowList = self.__getValueList(containerList[0], "pdbx_chem_comp_descriptor")
            if len(descriptorRowList) == 0:
                return []
            checkValueLists = []
            for descriptorRow in descriptorRowList:
                valueList = []
                for item in ("type", "program", "descriptor"):
                    if (item not in descriptorRow) or (not descriptorRow[item]):
                        continue
                    valueList.append(descriptorRow[item])
                if len(valueList) != 3:
                    continue
                if (
                    (valueList[0] == "SMILES_CANONICAL")
                    and ((valueList[1] == "CACTVS") or (valueList[1] == "OpenEye OEToolkits"))
                ) or ((valueList[0] == "InChI") and (valueList[1] == "InChI")):
                    checkValueLists.append(valueList)
            if len(checkValueLists) < 3:
                return []
            ok = self.openConnection()
            if ok:
                myq = MyDbQuery(dbcon=self._dbCon, verbose=self.__verbose, log=self.__lfh)
                ccdIdList = self.__searchDuplicateIdList(myq, checkValueLists[0])
                if len(ccdIdList) > 0:
                    for valueList in checkValueLists[1:]:
                        ccdIdList1 = self.__searchDuplicateIdList(myq, valueList)
                        if len(ccdIdList1) > 0:
                            ccdIdList = list(set(ccdIdList).intersection(ccdIdList1))
                        else:
                            ccdIdList = []
                        if len(ccdIdList) == 0:
                            break
                    if len(ccdIdList) > 0:
                        ccdIdList = self.__removeOBSCCDs(myq, ccdIdList)
                self.closeConnection()
                return ccdIdList
        except:  # noqa: E722 pylint: disable=bare-except
            self.closeConnection()
            if self.__verbose:
                self.__lfh.write("+ChemCompDbUtil.searchSameCCDs():\n")
                traceback.print_exc(file=self.__lfh)
        return []

    def __getValueList(self, containerObj, catName):
        """ """
        valueList = []
        catObj = containerObj.getObj(catName)
        if not catObj:
            return valueList
        attribList = catObj.getAttributeList()
        rowList = catObj.getRowList()
        for row in rowList:
            tD = {}
            for idxIt, itName in enumerate(attribList):
                if row[idxIt] != "?" and row[idxIt] != ".":
                    tD[itName] = row[idxIt]
            if tD:
                valueList.append(tD)
        return valueList

    def __searchDuplicateIdList(self, myq, valueList):
        """ """
        retIdList = []
        try:
            sql = (
                'select comp_id from pdbx_chem_comp_descriptor where type = "'
                + valueList[0]
                + '" and program = "'
                + valueList[1]
                + '" and descriptor = "'
                + valueList[2]
                + '"'
            )  # noqa: S608
            rows = myq.selectRows(queryString=sql)
            if rows and (len(rows) > 0):
                for row in rows:
                    retIdList.append(row[0])
        except:  # noqa: E722 pylint: disable=bare-except
            if self.__verbose:
                self.__lfh.write("+ChemCompDbUtil.__searchDuplicateIdList():\n")
                traceback.print_exc(file=self.__lfh)
        return retIdList

    def __removeOBSCCDs(self, myq, inputCcdIdList):
        """ """
        retIdList = []
        try:
            sql = (
                "select id from chem_comp where (pdbx_release_status != 'OBS') and ((pdbx_replaced_by is null) or (pdbx_replaced_by = '')) and id in ('"
                + "', '".join(inputCcdIdList)
                + "')"
            )  # noqa: S608
            rows = myq.selectRows(queryString=sql)
            if rows and (len(rows) > 0):
                for row in rows:
                    retIdList.append(row[0])
        except:  # noqa: E722 pylint: disable=bare-except
            if self.__verbose:
                self.__lfh.write("+ChemCompDbUtil.__removeOBSCCDs():\n")
                traceback.print_exc(file=self.__lfh)
        return retIdList
