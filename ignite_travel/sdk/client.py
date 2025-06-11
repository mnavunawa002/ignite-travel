"""
Main client for interacting with the Ignite Travel API
"""
import xml.etree.ElementTree as ET
import os
import requests

from .entities import *

from datetime import date, datetime

import logging

logging.basicConfig(level=logging.INFO)


class DimsInventoryClient:
  # URLs for the inventory and rates services
  _INVENTORY_SERVICE_URL_ = "https://dims.ignitetravel.com/IMSXML/RewardsCorpIMS.asmx?wsdl"
  _RATES_SERVICE_URL_ = "https://dims.ignitetravel.com/RMSXML/RateInterfaceService.asmx?wsdl"

  def __init__(self):
    self.username = os.getenv("IGNITE_USERNAME", None)
    self.password = os.getenv("IGNITE_PASSWORD", None)
    self.token = os.getenv("IGNITE_TOKEN", None)

    # check if the username, password and token are set
    if not all([self.username, self.password, self.token]):
      raise ValueError("Username, password and token must be set in the environment variables.")

  def format_soap_envelope(self, payload: str):
    return f"""<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
               xmlns:xsd="http://www.w3.org/2001/XMLSchema"
               xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
    <soap:Header>
        <Authentication xmlns="https://dims.ignitetravel.com/IMSXML">
            <UserName>{self.username}</UserName>
            <PassWord>{self.password}</PassWord>
            <Token>{self.token}</Token>
        </Authentication>
    </soap:Header>
    <soap:Body>
        {payload}
    </soap:Body>
</soap:Envelope>"""
  
  def make_request(self, method:str, payload: str, action_header: str = "GetRoomList", service_type: str = "inventory"):
    """Payload is the XML payload for the request"""
    data = self.format_soap_envelope(payload)
    response = requests.request(
      method=method,
      url=self._INVENTORY_SERVICE_URL_ if service_type == 'inventory' else self._RATES_SERVICE_URL_,
      headers={
        "Content-Type": "text/xml; charset=utf-8",
        "SOAPAction": f"https://dims.ignitetravel.com/IMSXML/{action_header}"
      },
      data=data
    )
    response.raise_for_status()
    return response.text
  
  def get_roomlist(self, resort_id: int, action_header: str = "GetRoomList") -> RoomList:
    """
    Get the room list for a given resort
    """
    try:
      resort_id = int(resort_id)
    except ValueError:
      raise ValueError("Resort ID must be an integer")
    
    soap_body = f"""<GetRoomList xmlns="https://dims.ignitetravel.com/IMSXML">
            <Message>
                <RewardsCorpIMS xmlns="">
                    <Request>RoomsList</Request>
                    <ResortId>{resort_id}</ResortId>
                </RewardsCorpIMS>
            </Message>
        </GetRoomList>"""
    response = self.make_request("POST", soap_body, action_header)
    # parse the xml response into a RoomList object
    root = ET.fromstring(response)
    rooms = []
    # Extract the rooms from the response
    for room in root.findall(".//Room"):
      room_id = room.find("RoomTypeId").text
      description = room.find("Description").text
      room_model = Room(room_id=int(room_id), room_name=description)
      rooms.append(room_model)
    # Extract linked rates
    for linked_rate in root.findall(".//LinkedRate"):
      # handle the case where the linked rate is not present
      if linked_rate.find("RateId") is None or linked_rate.find("RoomId") is None or linked_rate.find("RateDescription") is None:
        continue
      rate_id = linked_rate.find("RateId").text
      rate_description = linked_rate.find("RateDescription").text
      room_id = linked_rate.find("RoomId").text
      linked_rate_model = LinkedRate(rate_id=int(rate_id), rate_description=rate_description, room_id=int(room_id))
      # get the room model that matches the room_type_id
      room_model = next((r for r in rooms if r.room_id == int(room_id)), None)
      if room_model:
        room_model.linked_rate = linked_rate_model
    
    return RoomList(rooms=rooms)
  
  def retrieve_availability(self, room_id:int, resort_id:int, start_date:str, end_date:str, action_header: str = "RetrieveAvailability") -> List[Availability]:
    """
    Get the availability for a given room and date range
    """
    # convert the start and end dates to the format YYYY-MM-DD
    # check if resort id and room id can be converted to int
    try:
      resort_id = int(resort_id)
      room_id = int(room_id)
    except ValueError:
      raise ValueError("Resort ID and Room ID must be integers")
    # check if the start and end dates are valid
    try:
      start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
      end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
    except ValueError:
      raise ValueError("Invalid date format")
    if start_date > end_date:
      raise ValueError("Start date must be before end date")
    if start_date < datetime.now().date():
      raise ValueError("Start date must be in the future")
    if end_date < datetime.now().date():
      raise ValueError("End date must be in the future")
    start_date = start_date.strftime("%Y-%m-%d")
    end_date = end_date.strftime("%Y-%m-%d")
    soap_body = f"""<RetrieveAvailability xmlns="https://dims.ignitetravel.com/IMSXML">
            <Message>
                <RewardsCorpIMS xmlns="">
                    <Request>Availability</Request>
                    <RoomId>{room_id}</RoomId>
                    <ResortId>{resort_id}</ResortId>
                    <Dates>
                        <Date>{start_date}</Date>
                        <Date>{end_date}</Date>
                    </Dates>
                </RewardsCorpIMS>
            </Message>
        </RetrieveAvailability>"""
    response = self.make_request("POST", soap_body, action_header)
    root = ET.fromstring(response)
    availability = []
    for dateset in root.findall(".//DateSet"):
      inventory_available = dateset.find("InventoryAvailable").text
      literal_inventory = dateset.find("LiteralInventory").text
      dtm = datetime.strptime(dateset.find("Date").text, "%d-%m-%Y").date()
      availability.append(Availability(inventory_available=int(inventory_available), literal_inventory=int(literal_inventory), dtm=dtm))
    # ensure the availability is sorted by dtm
    availability.sort(key=lambda x: x.dtm)  # sort the availability by dtm i,e current date to end date
    return availability
  
  def availability_mass_update(self, room_id:int, resort_id:int, dates:List[str], qty:int, action_header: str = "UpdateInventory") -> str:
    """
    Update the availability for a given room and date range
    """
    try:
      room_id = int(room_id)
      resort_id = int(resort_id)
    except ValueError:
      raise ValueError("Room ID, Resort ID and Quantity must be integers")
    # check if the dates are valid
    dates_list = []
    qty_list = []
    for date, qty in zip(dates, qty):
      try:
        date = datetime.strptime(date, "%d-%m-%Y").date()
        qty = int(qty)
      except ValueError:
        raise ValueError("Invalid date format")
      dates_list.append(date)
      qty_list.append(qty)
    
    # create the dates set
    dates_set = []
    for date, qty in zip(dates_list, qty_list):
      dates_set.append(f"<DatesSet><Date>{date}</Date><InventoryAllocation>{qty}</InventoryAllocation></DatesSet>")
    
    dates_set = "\n".join(dates_set)

    # create the soap body
    soap_body = f"""<UpdateInventory xmlns="https://dims.ignitetravel.com/IMSXML">
            <Message>
                <RewardsCorpIMS xmlns="">
                    <Request>InventoryUpdate</Request>
                    <RoomId>{room_id}</RoomId>
                    <ResortId>{resort_id}</ResortId>
                    <Dates>
                        {dates_set}
                    </Dates>
                </RewardsCorpIMS>
            </Message>
        </UpdateInventory>"""
    response = self.make_request("POST", soap_body, action_header)
    root = ET.fromstring(response)
    message = root.find(".//Message").text
    return message

  
  def update_availability(self, room_id:int, resort_id:int, date:str, qty:int, action_header: str = "UpdateInventory") -> str:
    """
    Update the availability for a given room and date
    """
    try:
      room_id = int(room_id)
      resort_id = int(resort_id)
      qty = int(qty)
    except ValueError:
      raise ValueError("Room ID, Resort ID and Quantity must be integers")
    # check if the date is valid
    try:
      date = datetime.strptime(date, "%d-%m-%Y").date()
    except ValueError:
      raise ValueError("Invalid date format")
    soap_body = f"""<UpdateInventory xmlns="https://dims.ignitetravel.com/IMSXML">
            <Message>
                <RewardsCorpIMS xmlns="">
                    <Request>InventoryUpdate</Request>
                    <RoomId>{room_id}</RoomId>
                    <ResortId>{resort_id}</ResortId>
                    <Dates>
                        <DatesSet>
                            <Date>{date}</Date>
                            <InventoryAllocation>{qty}</InventoryAllocation>
                        </DatesSet>
                    </Dates>
                </RewardsCorpIMS>
            </Message>
        </UpdateInventory>"""
    response = self.make_request("POST", soap_body, action_header)
    root = ET.fromstring(response)
    message = root.find(".//Message").text
    return message
  
  def get_bookings(self, resort_id:int, start_date:str, end_date:str, action_header: str = "GetBookingsListWithRoomRateIds") -> List[BookingDetail]:
    """
    Get the bookings for a given resort and date range
    """
    try:
      resort_id = int(resort_id)
    except ValueError:
      raise ValueError("Resort ID must be an integer")
    try:
      start_date = datetime.strptime(start_date, "%Y-%m-%d").date().strftime("%d-%b-%Y")  # 1st June 2025
      end_date = datetime.strptime(end_date, "%Y-%m-%d").date().strftime("%d-%b-%Y")  # 30th June 2025
    except ValueError:
      raise ValueError("Invalid date format")
    soap_body = f"""<GetBookingsListWithRoomRateIds xmlns="https://dims.ignitetravel.com/IMSXML">
            <Message>
                <RewardsCorpIMS xmlns="">
                    <Request>GetBookingsListWithRoomRateIds</Request>
                    <ResortId>{resort_id}</ResortId>
                    <Dates>
                        <Date>{start_date}</Date>
                        <Date>{end_date}</Date>
                    </Dates>
                </RewardsCorpIMS>
            </Message>
        </GetBookingsListWithRoomRateIds>"""
    response = self.make_request("POST", soap_body, action_header)
    root = ET.fromstring(response)
    # first check if there are any bookings before parsing each booking
    message_type = root.find(".//MessageType")
    message = root.find(".//Message")
    if message_type and message_type.text == "Error":
        return []
    # parse the bookings
    bookings = []
    for booking in root.findall(".//Booking"):
      booking_number = booking.find(".//BookingNumber").text
      booking_details = booking.find(".//BookingDetails")
      booking_status_id = booking_details.find(".//BookingStatusId").text
      booking_status_description = booking_details.find(".//BookingStatusDescription").text
      resort_id = booking_details.find(".//ResortId").text
      resort_name = booking_details.find(".//ResortName").text
      resort_currency = booking_details.find(".//ResortCurrency").text
      rooms = []
      for room in booking.findall(".//Rooms/Room"):
        booking_id = room.find(".//BookingId").text
        room_details = room.find(".//RoomDetails")
        room_id = room_details.find(".//RoomId").text
        room_description = room_details.find(".//RoomDescription").text
        date_booked = room_details.find(".//DateBooked").text
        check_in = room_details.find(".//CheckIn").text
        nights = room_details.find(".//Nights").text
        adults = room_details.find(".//Adults").text
        children = room_details.find(".//Children").text
        infants = room_details.find(".//Infants").text
        special_requests = room_details.find(".//SpecialRequests").text if room_details.find(".//SpecialRequests") is not None else None
        first_name = room_details.find(".//GivenNames").text if room_details.find(".//GivenNames") is not None else None
        surname = room_details.find(".//Surname").text if room_details.find(".//Surname") is not None else None
        address = room_details.find(".//Address").text if room_details.find(".//Address") is not None else None
        suburb = room_details.find(".//Suburb").text if room_details.find(".//Suburb") is not None else None
        state = room_details.find(".//State").text if room_details.find(".//State") is not None else None
        postcode = room_details.find(".//Postcode").text if room_details.find(".//Postcode") is not None else None
        email_address = room_details.find(".//EmailAddress").text if room_details.find(".//EmailAddress") is not None else None
        phone_number = room_details.find(".//PhoneNumber").text if room_details.find(".//PhoneNumber") is not None else None
        room_detail = RoomDetail(
          booking_id=booking_id,
          room_id=room_id,
          room_description=room_description,
          date_booked=date_booked,
          check_in=check_in,
          nights=nights,
          adults=adults,
          children=children,
          infants=infants,
          special_requests=special_requests,
          first_name=first_name,
          surname=surname,
          address=address,
          suburb=suburb,
          state=state,
          postcode=postcode,
          email_address=email_address,
          phone_number=phone_number
        )
        rooms.append(room_detail)
      booking_detail = BookingDetail(
        booking_number=booking_number,
        booking_status_id=booking_status_id,
        booking_status_description=booking_status_description,
        rooms=rooms,
        resort_id=resort_id,
        resort_name=resort_name,
        resort_currency=resort_currency
      )
      bookings.append(booking_detail)
    return bookings
  

  def get_cancelled_bookings(self, resort_id:int, start_date:str, end_date:str, action_header: str = "RetrieveCancelledBookings"):
    """
    Get the cancelled bookings for a given resort and date range
    """
    try:
      resort_id = int(resort_id)
    except ValueError:
      raise ValueError("Resort ID must be an integer")
    try:
      start_date = datetime.strptime(start_date, "%Y-%m-%d").date().strftime("%d-%m-%Y")
      end_date = datetime.strptime(end_date, "%Y-%m-%d").date().strftime("%d-%m-%Y")
    except ValueError:
      raise ValueError("Invalid date format")
    soap_body = f"""<RetrieveCancelledBookings xmlns="https://dims.ignitetravel.com/IMSXML">
            <Message>
                <RewardsCorpIMS xmlns="">
                    <Request>RetrieveCancelledBookings</Request>
                    <ResortId>{resort_id}</ResortId>
                    <Dates>
                        <Date>{start_date}</Date>
                        <Date>{end_date}</Date>
                    </Dates>
                </RewardsCorpIMS>
            </Message>
        </RetrieveCancelledBookings>"""
    response = self.make_request("POST", soap_body, action_header)
    root = ET.fromstring(response)
    # first check if there are any bookings before parsing each booking
    message_type = root.find(".//MessageType")
    message = root.find(".//Message")
    if message_type and message_type.text == "Error":
        return []
    # parse the bookings
    bookings = []
    for booking in root.findall(".//Booking"):
      booking_id = booking.find(".//BookingId").text
      booking_number = booking.find(".//BookingNumber").text
      booking_status_id = booking.find(".//BookingStatusId").text
      booking_status_description = booking.find(".//BookingStatusDescription").text
      booking_change_date = booking.find(".//BookingChangeDate").text
      cancelled_booking = CancelledBooking(
        booking_id=booking_id,
        booking_number=booking_number,
        booking_status_id=booking_status_id,
        booking_status_description=booking_status_description,
        booking_change_date=booking_change_date
      )
      bookings.append(cancelled_booking)
    return bookings