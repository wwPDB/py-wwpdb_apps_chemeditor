##
# File: ImportTests.py
# Date:  06-Oct-2018  E. Peisach
#
# Updates:
##
"""Test cases for release module"""

__docformat__ = "restructuredtext en"
__author__ = "Ezra Peisach"
__email__ = "peisach@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.01"

import unittest

from wwpdb.apps.chemeditor.webapp.ChemEditorWebApp import ChemEditorWebApp


class ImportTests(unittest.TestCase):
    def setUp(self):
        pass

    def testInstantiate(self):
        """Tests simple instantiation"""
        ChemEditorWebApp()
