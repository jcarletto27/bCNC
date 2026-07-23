import os
import sys
import unittest
from unittest.mock import Mock


BCNC_DIR = os.path.join(os.path.dirname(__file__), "..", "bCNC")
sys.path.insert(0, BCNC_DIR)
sys.path.insert(0, os.path.join(BCNC_DIR, "lib"))

from Sender import Sender


class SenderRunCompletionTest(unittest.TestCase):
    def test_final_idle_wait_ends_run(self):
        sender = Sender.__new__(Sender)
        sender._runEndWait = True
        sender.sio_wait = False
        sender.runEnded = Mock()

        sender.finishRunWait()

        sender.runEnded.assert_called_once_with()
        self.assertFalse(sender._runEndWait)

    def test_intermediate_idle_wait_does_not_end_run(self):
        sender = Sender.__new__(Sender)
        sender._runEndWait = False
        sender.sio_wait = False
        sender.runEnded = Mock()

        sender.finishRunWait()

        sender.runEnded.assert_not_called()

    def test_pending_final_wait_does_not_end_run(self):
        sender = Sender.__new__(Sender)
        sender._runEndWait = True
        sender.sio_wait = True
        sender.runEnded = Mock()

        sender.finishRunWait()

        sender.runEnded.assert_not_called()
        self.assertTrue(sender._runEndWait)


if __name__ == "__main__":
    unittest.main()
