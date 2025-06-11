import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

from ignite_travel.sdk import DimsInventoryClient


class TestGetAvailability(unittest.TestCase):
    """
    Test the get_availability method
    """

    def setUp(self):
        self.client = DimsInventoryClient()
        self.resort_id = 1056
        self.start_date = datetime.now()
        self.end_date = self.start_date + timedelta(days=15)  # 15 days from now

    def test_retrieve_availability(self):
        """
        Test the retrieve_availability method
        """
        room_list = self.client.get_roomlist(self.resort_id)
        room = room_list.rooms[0]
        availability = self.client.retrieve_availability(room.room_id, self.resort_id, self.start_date.strftime("%Y-%m-%d"), self.end_date.strftime("%Y-%m-%d"))
        self.assertTrue(len(availability) > 0)
    
    def test_retrieve_availability_invalid_room_id(self):
        """
        Test the retrieve_availability method with an invalid room id
        """
        availability = self.client.retrieve_availability(10000, self.resort_id, self.start_date.strftime("%Y-%m-%d"), self.end_date.strftime("%Y-%m-%d"))
        self.assertTrue(len(availability) == 0)

    def test_update_availability(self):
        """
        Test the update_availability method
        """
        room_list = self.client.get_roomlist(self.resort_id)
        room = room_list.rooms[0]
        message = self.client.update_availability(room.room_id, self.resort_id, self.end_date.strftime("%d-%m-%Y"), 10)
        self.assertEqual(message, "Update Successful")

    def test_availability_mass_update(self):
        """
        Test the availability_mass_update method
        """
        room_list = self.client.get_roomlist(self.resort_id)
        room = room_list.rooms[0]
        dates = [self.end_date + timedelta(days=i) for i in range(365)]
        qty = [10 for _ in range(365)]
        message = self.client.availability_mass_update(room.room_id, self.resort_id, [date.strftime("%d-%m-%Y") for date in dates], qty)
        self.assertEqual(message, "Update Successful")


if __name__ == '__main__':
    unittest.main()