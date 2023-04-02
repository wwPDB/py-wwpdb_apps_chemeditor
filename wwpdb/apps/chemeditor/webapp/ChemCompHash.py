##
# File:  ChemCompHash.py
# Date:  08-Nov-2016
# Updates:
##
"""
Hash function to ensure equal distribution of available CCDs

This software was developed as part of the World Wide Protein Data Bank
Common Deposition and Annotation System Project
Copyright (c) 2016 wwPDB

"""
__docformat__ = "restructuredtext en"
__author__ = "ezra Peisach"
__email__ = "peisach@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.01"


class ChemCompHash(object):
    def getChemCompIdSite(self, ccId, sites=None):
        if sites is None:
            sites = ["RCSB", "PDBE", "PDBJ"]
        try:
            i = self.chemCompIdToInt(ccId)
            return sites[i % len(sites)]
        except:  # noqa: E722 pylint: disable=bare-except,try-except-raise
            raise

    def chemCompIdToInt(self, ccId):
        """Convert ccId to a ~base36 (A-Z,0-9) integer --"""
        characters = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z"]
        numbers = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]
        iret = 0
        cList = characters + numbers
        base = len(cList)
        ccIdU = ccId.upper()
        #
        try:
            for i, c in enumerate(ccIdU[::-1]):
                iret += cList.index(c) * pow(base, i)
        except:  # noqa: E722 pylint: disable=bare-except,try-except-raise
            raise

        return iret


if __name__ == "__main__":
    cCH = ChemCompHash()
    idList3 = ["AA0", "AA1", "AA2", "AA3", "AA4", "AA5", "AA6", "AA7", "AA8", "AA9"]
    idList2 = ["A0", "A1", "A2", "A3", "A4", "A5", "A6", "A7", "A8", "A9"]
    characters_ = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z"]
    numbers_ = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]
    idList1 = characters_ + numbers_
    idList = idList1 + idList2 + idList3
    for id_ in idList:
        print(id, cCH.getChemCompIdSite(id_))
    #
    #
