import unittest
from ignite_travel.sdk import DimsInventoryClient
from unittest.mock import patch, MagicMock
import requests
from ignite_travel.sdk.entities import RoomList, Room, LinkedRate


class TestGetRoomList(unittest.TestCase):
    """
    Test the get_roomlist method
    """

    def setUp(self):
        self.client = DimsInventoryClient()

    @patch.object(DimsInventoryClient, 'get_roomlist')
    def test_get_roomlist(self, mock_get_roomlist):
        """
        Test the get_roomlist method
        """
        mock_room = Room(room_id=1, room_name="Single Room", linked_rate=LinkedRate(rate_id=1, rate_description="Single Room", room_id=1))
        mock_room_list = RoomList(rooms=[mock_room])
        mock_get_roomlist.return_value = mock_room_list

        room_list = self.client.get_roomlist("1056")
        self.assertEqual(len(room_list.rooms), 1)
        self.assertEqual(room_list.rooms[0].room_id, 1)
        self.assertEqual(room_list.rooms[0].room_name, "Single Room")
        self.assertEqual(room_list.rooms[0].linked_rate.rate_id, 1)
        self.assertEqual(room_list.rooms[0].linked_rate.rate_description, "Single Room")
        self.assertEqual(room_list.rooms[0].linked_rate.room_id, 1)

    @patch.object(DimsInventoryClient, 'get_roomlist')
    def test_get_roomlist_no_linked_rate(self, mock_get_roomlist):
        """
        Test the get_roomlist method when there is no linked rate
        """
        mock_room = Room(room_id=1, room_name="Single Room", linked_rate=None)
        mock_room_list = RoomList(rooms=[mock_room])
        mock_get_roomlist.return_value = mock_room_list

        room_list = self.client.get_roomlist("1056")
        self.assertEqual(len(room_list.rooms), 1)
        self.assertEqual(room_list.rooms[0].room_id, 1)
        self.assertEqual(room_list.rooms[0].room_name, "Single Room")
        self.assertIsNone(room_list.rooms[0].linked_rate)


    def test_get_roomlist_invalid_resort_id(self):
        """
        Test the get_roomlist method when the resort ID is invalid
        """
        with self.assertRaises(ValueError):
            self.client.get_roomlist("#&**")


if __name__ == '__main__':
    unittest.main()