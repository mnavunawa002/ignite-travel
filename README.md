# Ignite Travel SDK

The Ignite Travel Unofficial SDK provides a client to interact with the Ignite Travel SOAP-based web services. It allows you to manage room lists, retrieve availability, update inventory, and get bookings for resorts.

[GitHub Repository](https://github.com/mnavunawa002/ignite-travel.git)


## Installation

To install the Ignite Travel SDK, you can use pip, the Python package installer. Run the following command in your terminal:

`pip install ignite-travel`

## Getting Starged

## Usage

To use the Ignite Travel SDK, you need to set up your environment with the necessary credentials and create an instance of the `DimsInventoryClient`. Below is a basic example of how to get started:

1. **Set Environment Variables**: Ensure you have the following environment variables set in your system:
   - `IGNITE_USERNAME`: Your Ignite Travel username.
   - `IGNITE_PASSWORD`: Your Ignite Travel password.
   - `IGNITE_TOKEN`: Your Ignite Travel API token.

2. **Create a Client Instance**: Use the `DimsInventoryClient` to interact with the Ignite Travel services.

    ```python
    # import client
    from ignite_travel.sdk import DimsInventoryClient

    # Example usage
    client = DimsInventoryClient()

    # Retrieve room list for a specific resort
    resort_id = 123
    room_list = client.get_roomlist(resort_id)
    print(room_list)

    # Retrieve availability for a specific date range
    start_date = "01-01-2023"
    end_date = "07-01-2023"
    availability = client.retrieve_availability(resort_id, start_date, end_date)
    print(availability)

    # Update inventory for a specific room and date
    room_id = 456
    date = "01-01-2023"
    quantity = 10
    update_response = client.update_availability(room_id, resort_id, date, quantity)
    print(update_response)

    # update inventory for a given date range
    room_id = 456
    dates = ["01-01-2023", "02-01-2023", "03-01-2023"]
    quantities = [10, 15, 20]
    update_response = client.availability_mass_update(room_id, resort_id, dates, quantities)
    print(update_response)

    # Get bookings for a specific date range
    bookings = client.get_bookings(resort_id, start_date, end_date)
    print(bookings)

    # Get cancelled bookings for a specific date range
    cancelled_bookings = client.get_cancelled_bookings(resort_id, start_date, end_date)
    print(cancelled_bookings)
    ```