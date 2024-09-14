##
# File: ChemCompHashTests.py
# Date:  06-Oct-2018  E. Peisach
#
# Updates:
##
"""Test cases for ChemCompHash module"""

__docformat__ = "restructuredtext en"
__author__ = "Ezra Peisach"
__email__ = "peisach@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.01"

import unittest
from wwpdb.apps.chemeditor.webapp.ChemCompHash import ChemCompHash


class HashTests(unittest.TestCase):
    def setUp(self):
        self.__sites = ["RCSB", "PDBJ", "PDBE"]
        self.characters = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z"]
        self.numbers = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]

    def testSomeHash(self):
        """Tests running through hash"""
        cch = ChemCompHash()
        idlist3 = ["AA0", "AA1", "AA2", "AA3", "AA4", "AA5", "AA6", "AA7", "AA8", "AA9"]
        idlist2 = ["A0", "A1", "A2", "A3", "A4", "A5", "A6", "A7", "A8", "A9"]
        idlist1 = self.characters + self.numbers
        idlist = idlist1 + idlist2 + idlist3

        for ccid in idlist:
            self.assertIn(cch.getChemCompIdSite(ccid), self.__sites, "Generated id not in sites")

    def testAllHash(self):
        """Tests all three letter CC ids"""
        cch = ChemCompHash()
        allchars = self.characters + self.numbers
        for i in allchars:
            for j in allchars:
                for k in allchars:
                    self.assertIn(cch.getChemCompIdSite("%s%s%s" % (i, j, k)), self.__sites, "Generated id not in sites")


if __name__ == "__main__":
    unittest.main()
