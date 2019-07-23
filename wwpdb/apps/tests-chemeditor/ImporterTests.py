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

try:
    # openeye issue
    from wwpdb.apps.chemeditor.webapp.ChemEditorWebApp import ChemEditorWebApp
except ImportError:
    from wwpdb.io.file.mmCIFUtil import mmCIFUtil
    from wwpdb.utils.config.ConfigInfo import ConfigInfo
    from wwpdb.utils.session.WebRequest import InputRequest, ResponseContent

    from wwpdb.apps.chemeditor.webapp.AtomMatch import AtomMatch
    from wwpdb.apps.chemeditor.webapp.CVSCommit import CVSCommit
    from wwpdb.apps.chemeditor.webapp.ChemCompHash import ChemCompHash
    from wwpdb.apps.chemeditor.webapp.Get2D import Get2D
    from wwpdb.apps.chemeditor.webapp.GetLigand import GetLigand
 #   from wwpdb.apps.chemeditor.webapp.SaveLigand import SaveLigand
    from wwpdb.apps.chemeditor.webapp.Search import Search
    from wwpdb.apps.chemeditor.webapp.UpdateLigand import UpdateLigand
    from wwpdb.apps.chemeditor.webapp.Upload import Upload


class ImportTests(unittest.TestCase):
    def setUp(self):
        pass

    def testInstantiate(self):
        """Tests simple instantiation"""
        pass
