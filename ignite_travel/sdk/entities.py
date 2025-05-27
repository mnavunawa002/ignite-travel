from pydantic import BaseModel, Field, field_validator, model_validator

from typing import List, Optional
from datetime import date, datetime
from dateutil.parser import parse


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
  date_booked: datetime = Field()  # date of the booking
  check_in: date = Field()  # check in date
  nights: int = Field()  # number of nights
  adults: int = Field()  # number of adults
  children: int = Field(default=0)  # number of children
  infants: int = Field(default=0)  # number of infants
  special_requests: Optional[str] = Field(default=None)  # special requests
  first_name: Optional[str] = Field(default=None)  # first name of the guest
  surname: Optional[str] = Field(default=None)  # surname of the guest
  address: Optional[str] = Field(default=None)  # address of the guest
  suburb: Optional[str] = Field(default=None)  # suburb of the guest
  state: Optional[str] = Field(default=None)  # state of the guest
  postcode: Optional[str] = Field(default=None)  # postcode of the guest
  email_address: Optional[str] = Field(default=None)  # email address of the guest
  phone_number: Optional[str] = Field(default=None)  # phone number of the guest

  @field_validator("date_booked", mode="before")
  def parse_date_booked(cls, value):
    if isinstance(value, str):
      return parse(value)
    return value
  
  @field_validator("check_in", mode="before")
  def parse_check_in(cls, value):
    if isinstance(value, str):
      return datetime.strptime(value, "%d-%m-%Y").date()
    return value


class BookingDetail(BaseModel):
  booking_number: str = Field()
  resort_id: int = Field()
  resort_name: str = Field()
  resort_currency: Optional[str] = Field(default=None)
  booking_status_id: int = Field()
  booking_status_description: str = Field()
  rooms: List[RoomDetail] = Field()


class CancelledBooking(BaseModel):
  booking_id: int = Field()
  booking_number: str = Field()
  booking_status_id: int = Field()
  booking_status_description: str = Field()
  booking_change_date: datetime = Field()

  @field_validator("booking_change_date", mode="before")
  def parse_booking_change_date(cls, value):
    if isinstance(value, str):
      return parse(value)
    return value
