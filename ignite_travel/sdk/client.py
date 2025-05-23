"""
Main client for interacting with the Ignite Travel API
"""
import xml.etree.ElementTree as ET
import os
import requests

from .entities import *

from datetime import date, datetime


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
  
  def get_bookings(self, resort_id:int, start_date:str, end_date:str, action_header: str = "GetBookingsListWithRoomRateIds"):
    """
    Get the bookings for a given resort and date range
    """
    try:
      resort_id = int(resort_id)
    except ValueError:
      raise ValueError("Resort ID must be an integer")
    try:
      start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
      end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
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
    message_type = root.find(".//MessageType").text
    message = root.find(".//Message").text
    if message_type == "Error":
        # add logging
        return []
    