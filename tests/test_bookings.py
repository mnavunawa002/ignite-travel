import unittest
from ignite_travel.sdk import DimsInventoryClient
from unittest.mock import patch, MagicMock

from ignite_travel.sdk.entities import *
from datetime import datetime, timedelta


class TestGetAvailability(unittest.TestCase):
    """
    Test the get_availability method
    """
    def setUp(self):
        self.client = DimsInventoryClient()
        self.resort_id = 1056
        self.start_date = datetime.now()
        self.end_date = self.start_date + timedelta(days=15)  # 15 days from now

    def test_get_bookings(self):
        """
        Test the get_bookings method
        """
        bookings = self.client.get_bookings(self.resort_id, self.start_date.strftime("%Y-%m-%d"), self.end_date.strftime("%Y-%m-%d"))
        self.assertTrue(isinstance(bookings, list))


if __name__ == '__main__':
    unittest.main()