import os
import pickle
import datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import dateparser


# If modifying or creating events, this scope is needed
SCOPES = ['https://www.googleapis.com/auth/calendar']


# Authenticate and build the calendar service
def authenticate_google_calendar():
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    service = build('calendar', 'v3', credentials=creds)
    return service


# Function to create an event
def create_event(service, start_date, repeat_days, title, location, description, end_date):
    # Start by checking the next possible event date
    current_date = start_date
    # Default time (3:00 PM to 4:00 PM)
    start_time = datetime.datetime(current_date.year, current_date.month, current_date.day, 15, 0)
    end_time = start_time + datetime.timedelta(hours=1)


    # Event details
    event = {
        'summary': title,
        'location': location or 'No location provided',
        'description': description or 'No description provided',
        'start': {
            'dateTime': start_time.isoformat(),
            'timeZone': 'America/New_York',
        },
        'end': {
            'dateTime': end_time.isoformat(),
            'timeZone': 'America/New_York',
        },
        'attendees': [{'email': 'attendee@example.com'}],
        'reminders': {'useDefault': True},
    }
   
    # Recursively add event until the end date or 2-year limit
    add_event(service, event, current_date, repeat_days, end_date)
   
def add_event(service, event, current_date, repeat_days, end_date):
    # Check if current_date is within the allowed range (2 years max from start date)
    two_years_later = current_date + datetime.timedelta(days=730)
    if current_date > end_date or current_date > two_years_later:
        print("Stopping event creation: reached end date or 2-year limit.")
        return
   
    # Adjust time for current date
    start_time = datetime.datetime(current_date.year, current_date.month, current_date.day, 15, 0)
    end_time = start_time + datetime.timedelta(hours=1)
    event['start']['dateTime'] = start_time.isoformat()
    event['end']['dateTime'] = end_time.isoformat()


    # Insert the event into Google Calendar
    try:
        event_result = service.events().insert(calendarId='primary', body=event).execute()
        print(f"Event created: {event_result['summary']} on {event_result['start']['dateTime']}")
    except Exception as e:
        print(f"An error occurred: {e}")


    # Get the next valid day to create the event
    next_date = get_next_valid_day(current_date, repeat_days)
    if next_date:
        add_event(service, event, next_date, repeat_days, end_date)


# Get the next valid day for recurrence
def get_next_valid_day(current_date, repeat_days):
    weekday_names = {
        'M': 0,  # Monday
        'Tu': 1,  # Tuesday
        'W': 2,  # Wednesday
        'Th': 3,  # Thursday
        'F': 4,  # Friday
        'S': 5,  # Saturday
        'Su': 6   # Sunday
    }


    # Find the next valid day from repeat_days
    next_day = current_date.weekday()
    for i in range(1, 8):  # Try 1 week ahead
        next_possible_day = (next_day + i) % 7
        if next_possible_day in [weekday_names[day] for day in repeat_days]:
            next_date = current_date + datetime.timedelta(days=i)
            return next_date
    return None


# Main function to authenticate and create event
def main():
    # Authenticate Google Calendar
    service = authenticate_google_calendar()


    title = input("Enter event title: ")


    # Get the start date
    while True:
        date_str = input("Enter event start date (e.g., April 2, 2025): ")
        start_date = dateparser.parse(date_str.strip())
        if start_date:
            break
        print("Invalid date format. Please try again.")
   
    # Get the end date
    while True:
        end_date_str = input("Enter event end date (e.g., June 30, 2025, or press Enter for no end date): ")
        if not end_date_str:
            end_date = start_date + datetime.timedelta(days=730)  # Default 2-year limit
            break
        end_date = dateparser.parse(end_date_str.strip())
        if end_date:
            break
        print("Invalid end date format. Please try again.")


    # Get repeat days
    repeat_days_input = input("Enter repeat days (M, Tu, W, Th, F, S, Su, separated by commas): ")
    repeat_days = [day.strip() for day in repeat_days_input.split(",") if day.strip()]


    location = input("Enter event location (Enter to skip): ")
    description = input("Enter event description (Enter to skip): ")


    # Call the create_event function
    create_event(service, start_date, repeat_days, title, location, description, end_date)


if __name__ == '__main__':
    main()


