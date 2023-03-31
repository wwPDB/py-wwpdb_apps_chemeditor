import json
import tempfile
import sys
import unittest
import os
import os.path
from unittest.mock import Mock, MagicMock, patch
from wwpdb.apps.chemeditor.webapp.ChemEditorWebApp import ChemEditorWebAppWorker
from wwpdb.utils.session.WebRequest import InputRequest

sessionsTopDir = tempfile.mkdtemp()
configInfo = {
    'SITE_DEPOSIT_STORAGE_PATH': tempfile.mkdtemp(),
    'SITE_PREFIX': 'PDBE_LOCALHOST',
    'SITE_WEB_APPS_TOP_SESSIONS_PATH': sessionsTopDir,
    'SITE_WEB_APPS_SESSIONS_PATH': os.path.join(sessionsTopDir, 'sessions'),
    'SITE_CC_APPS_PATH': tempfile.mkdtemp(),
    'SITE_CC_CVS_PATH': tempfile.mkdtemp(),
    'SITE_DB_PORT_NUMBER': 10,
}

configInfoMockConfig = {
    'return_value': configInfo,
}

configMock = MagicMock(**configInfoMockConfig)

sys.modules['wwpdb.utils.config.ConfigInfo'] = Mock(ConfigInfo=configMock)


class ChemEditorWebAppTests(unittest.TestCase):
    '''This class tests ChemCompEditor API.

    '''
    def setUp(self):
        self._verbose = True
        self._lfh = sys.stderr
        self._topPath = os.getenv("WWPDB_CCMODULE_TOP_PATH")
        self._reqObj = InputRequest(paramDict={}, verbose=self._verbose, log=self._lfh)
        self._reqObj.setValue("WWPDB_SITE_ID", "PDBE_LOCALHOST")

    @patch('wwpdb.apps.chemeditor.webapp.ChemEditorWebApp.DaInternalCombineDb', autospec=True)
    def testGetEntriesWithLigand(self, mockDb):
        # Context manager... (not used)
        # mockDb().return_value.__enter__.return_value.getEntriesWithLigand.return_value = ['D_800001']
        # Generic
        mockDb().getEntriesWithLigand.return_value = ['D_800001']

        self._reqObj.setValue("ccid", "AAA")

        cewa = ChemEditorWebAppWorker(self._reqObj, self._verbose, self._lfh)
        response = json.loads(cewa._getEntriesWithLigands().get()['RETURN_STRING'])  # pylint: disable=protected-access
        self.assertEqual(response['datacontent'], ['D_800001'])

        # Context (not used)
        # mockDb().return_value.__enter__.return_value.getEntriesWithLigand.side_effect = IOError('failed to connect to db')
        # Generic
        mockDb().getEntriesWithLigand.side_effect = IOError('failed to connect to db')

        self._reqObj.setValue("request_path", "/service/chemeditor/get_entries_with_ligand")
        response = json.loads(cewa.doOp().get()['RETURN_STRING'])
        self.assertEqual(response['errortext'], "Could not open a connection to the database")
