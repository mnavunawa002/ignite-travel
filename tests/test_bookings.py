import unittest
from ignite_travel.sdk import DimsInventoryClient
from unittest.mock import patch

from ignite_travel.sdk.entities import *
from datetime import datetime, timedelta


class TestBookings(unittest.TestCase):
    """
    Test the bookings methods
    """
    def setUp(self):
        self.client = DimsInventoryClient()
        self.resort_id = 1056
        self.start_date = datetime(2025, 6, 1) # 1st June 2025
        self.end_date = datetime(2025, 6, 30)  # 30th June 2025

    @patch('ignite_travel.sdk.client.DimsInventoryClient.make_request')
    def test_get_bookings_list_with_room_rate_ids(self, mock_make_request):
        """
        Test the get_bookings_list_with_room_rate_ids method
        """
        mock_make_request.return_value = """<?xml version="1.0" encoding="utf-8"?>
        <soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
               xmlns:xsd="http://www.w3.org/2001/XMLSchema"
               xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
    <soap:Body>
        <GetBookingsListWithRoomRateIdsResponse xmlns="https://dims.ignitetravel.com/IMSXML">
            <GetBookingsListWithRoomRateIdsResult>
                <RewardsCorpIMS xmlns="">
                    <Bookings>
                        <Booking>
                            <BookingDetails>
                                <BookingNumber>E-IG10443355RT</BookingNumber>
                                <Rooms>
                                    <Room>
                                        <RoomDetails>
                                            <BookingId>11111</BookingId>
                                            <RoomDescription>Prestige Water Villa</RoomDescription>
                                            <RoomId>18178</RoomId>
                                            <DateBooked>01-06-2025 00:00:00</DateBooked>
                                            <CheckIn>01-06-2025</CheckIn>
                                            <Nights>1</Nights>
                                            <Adults>2</Adults>
                                            <Children>0</Children>
                                            <Infants>0</Infants>
                                            <SpecialRequests></SpecialRequests>
                                            <GivenNames>John</GivenNames>
                                            <Surname>Doe</Surname>
                                            <Address>123 Main St</Address>
                                            <Suburb>Anytown</Suburb>
                                            <State>NSW</State>
                                            <Postcode>2000</Postcode>
                                            <EmailAddress>john.doe@example.com</EmailAddress>
                                            <PhoneNumber>1234567890</PhoneNumber>
                                        </RoomDetails>
                                    </Room>
                                </Rooms>
                                <ResortId>1056</ResortId>
                                <ResortName>Best In Town</ResortName>
                                <ResortCurrency>USD</ResortCurrency>
                                <BookingStatusId>2</BookingStatusId>
                                <BookingStatusDescription>Booking Confirmed</BookingStatusDescription>
                            </BookingDetails>
                        </Booking>
                    </Bookings>
                </RewardsCorpIMS>
            </GetBookingsListWithRoomRateIdsResult>
        </GetBookingsListWithRoomRateIdsResponse>
    </soap:Body>
</soap:Envelope>"""
        bookings = self.client.get_bookings(self.resort_id, self.start_date.strftime("%Y-%m-%d"), self.end_date.strftime("%Y-%m-%d"))
        self.assertTrue(isinstance(bookings, list))
        self.assertEqual(len(bookings), 1)
        booking = bookings[0]
        self.assertEqual(booking.booking_number, "E-IG10443355RT")
        self.assertEqual(booking.booking_status_id, 2)
        self.assertEqual(booking.booking_status_description, "Booking Confirmed")
        self.assertEqual(booking.resort_id, 1056)
        self.assertEqual(booking.resort_name, "Best In Town")
        self.assertEqual(booking.resort_currency, "USD")

    @patch('ignite_travel.sdk.client.DimsInventoryClient.make_request')
    def test_get_cancelled_bookings(self, mock_make_request):
        """
        Test the get_cancelled_bookings method
        """
        mock_make_request.return_value = """<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" 
               xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
               xmlns:xsd="http://www.w3.org/2001/XMLSchema">
    <soap:Body>
        <RetrieveCancelledBookingsResponse xmlns="https://dims.ignitetravel.com/IMSXML">
            <RetrieveCancelledBookingsResult>
                <RewardsCorpIMS xmlns="">
                    <Message>List of Cancelled Bookings</Message>
                    <Bookings>
                        <Booking>
                            <BookingId>1644663</BookingId>
                            <BookingNumber>E-IG1237837MG</BookingNumber>
                            <BookingStatusId>5</BookingStatusId>
                            <BookingStatusDescription>Cancelled booking</BookingStatusDescription>
                            <BookingChangeDate>26-05-2025 09:48:00</BookingChangeDate>
                        </Booking>
                    </Bookings>
                </RewardsCorpIMS>
            </RetrieveCancelledBookingsResult>
        </RetrieveCancelledBookingsResponse>
    </soap:Body>
</soap:Envelope>"""
        start_date = datetime(2025, 5, 25)
        end_date = datetime(2025, 5, 31)
        bookings = self.client.get_cancelled_bookings(self.resort_id, start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))
        self.assertTrue(isinstance(bookings, list))
        booking = bookings[0]
        self.assertEqual(booking.booking_id, 1644663)
        self.assertEqual(booking.booking_number, "E-IG1237837MG")
        self.assertEqual(booking.booking_status_id, 5)
        self.assertEqual(booking.booking_status_description, "Cancelled booking")
        self.assertEqual(booking.booking_change_date, datetime(2025, 5, 26, 9, 48, 0))


    def test_get_actual_bookings(self):
        """
        Test the get_actual_bookings method
        """
        # As of this writing, the only booking is for 2025-05-20
        start_date = datetime(2025, 5, 20)
        end_date = datetime(2025, 5, 31)
        bookings = self.client.get_bookings(self.resort_id, start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))
        self.assertTrue(isinstance(bookings, list))
        self.assertEqual(len(bookings), 1)
        print(bookings)

if __name__ == '__main__':
    unittest.main()