from pydantic import BaseModel, Field

from typing import List, Optional
from datetime import date


class LinkedRate(BaseModel):
  rate_id: int = Field()
  rate_description: str = Field()
  room_id: int = Field()


class Room(BaseModel):
  room_id: int = Field()
  room_name: str = Field()
  linked_rate: Optional[LinkedRate] = Field(default=None)


class RoomList(BaseModel):
  rooms: List[Room] = Field()
 

class Availability(BaseModel):
  inventory_available: int = Field()  # inventory allocation considering the bookings
  literal_inventory: int = Field()  # inventory allocation excluding the bookings
  dtm: date = Field()  # date of the availability


class RoomDetail(BaseModel):
  booking_id: int = Field()  # The IMS booking id
  room_description: str = Field()
  room_id: int = Field()
  date_booked: date = Field()  # date of the booking
  check_in: date = Field()  # check in date
  nights: int = Field()  # number of nights
  adults: int = Field()  # number of adults
  children: int = Field(default=0)  # number of children
  infants: int = Field(default=0)  # number of infants
  special_requests: Optional[str] = Field(default=None)  # special requests
  surname: Optional[str] = Field(default=None)  # surname of the guest
  address: Optional[str] = Field(default=None)  # address of the guest
  suburb: Optional[str] = Field(default=None)  # suburb of the guest
  state: Optional[str] = Field(default=None)  # state of the guest
  postcode: Optional[str] = Field(default=None)  # postcode of the guest
  email_address: Optional[str] = Field(default=None)  # email address of the guest
  phone_number: Optional[str] = Field(default=None)  # phone number of the guest


class BookingDetail(BaseModel):
  booking_number: str = Field()
  resort_id: int = Field()
  resort_name: str = Field()
  booking_status_id: int = Field()
  booking_status_description: str = Field()
  rooms: List[RoomDetail] = Field()
