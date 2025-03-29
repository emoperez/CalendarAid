import os
import pickle
import datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import dateparser
import re

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

# Function to parse time range
def parse_time_range(time_str):
    match = re.match(r'(\d{1,2}:\d{2} [APMapm]+) - (\d{1,2}:\d{2} [APMapm]+)', time_str.strip())
    if match:
        start_time = dateparser.parse(match.group(1))
        end_time = dateparser.parse(match.group(2))
        if start_time and end_time:
            return start_time.time(), end_time.time()
    return None, None

# Function to create an event
def create_event(service, start_date, repeat_days, title, location, description, end_date, start_time, end_time):
    current_date = start_date

    # Event details
    event = {
        'summary': title,
        'location': location or 'No location provided',
        'description': description or 'No description provided',
        'start': {'dateTime': datetime.datetime.combine(current_date, start_time).isoformat(), 'timeZone': 'America/New_York'},
        'end': {'dateTime': datetime.datetime.combine(current_date, end_time).isoformat(), 'timeZone': 'America/New_York'},
        'reminders': {'useDefault': True},
    }

    add_event(service, event, current_date, repeat_days, end_date, start_time, end_time)

# Recursively add event until the end date or 1-year limit
def add_event(service, event, current_date, repeat_days, end_date, start_time, end_time):
    one_year_later = current_date + datetime.timedelta(days=365)
    if current_date > end_date or current_date > one_year_later:
        print("Stopping event creation: reached end date or 1-year limit.")
        return

    # Adjust time for current date
    event['start']['dateTime'] = datetime.datetime.combine(current_date, start_time).isoformat()
    event['end']['dateTime'] = datetime.datetime.combine(current_date, end_time).isoformat()

    try:
        event_result = service.events().insert(calendarId='primary', body=event).execute()
        print(f"Event created: {event_result['summary']} on {event_result['start']['dateTime']}")
    except Exception as e:
        print(f"An error occurred: {e}")

    next_date = get_next_valid_day(current_date, repeat_days)
    if next_date:
        add_event(service, event, next_date, repeat_days, end_date, start_time, end_time)

# Get the next valid day for recurrence
def get_next_valid_day(current_date, repeat_days):
    weekday_names = {'M': 0, 'Tu': 1, 'W': 2, 'Th': 3, 'F': 4, 'S': 5, 'Su': 6}
    next_day = current_date.weekday()
    
    for i in range(1, 8):
        next_possible_day = (next_day + i) % 7
        if next_possible_day in [weekday_names[day] for day in repeat_days]:
            return current_date + datetime.timedelta(days=i)
    return None

# Main function to authenticate and create event
def main():
    service = authenticate_google_calendar()
    title = input("Enter event title: ")

    while True:
        date_str = input("Enter event start date (e.g., April 2, 2025, 4/2/2025, 4-2-2025): ")
        start_date = dateparser.parse(date_str.strip())
        if start_date:
            break
        print("Invalid date format. Please try again.")

    while True:
        end_date_str = input("Enter event end date (e.g., June 30, 2025, or press Enter for 1-year limit): ")
        if not end_date_str:
            end_date = start_date + datetime.timedelta(days=365)
            break
        end_date = dateparser.parse(end_date_str.strip())
        if end_date:
            break
        print("Invalid end date format. Please try again.")

    while True:
        repeat_days_input = input("Enter repeat days (M, Tu, W, Th, F, S, Su, separated by commas): ")
        repeat_days = [day.strip() for day in repeat_days_input.split(",") if day.strip()]
        valid_days = {'M', 'Tu', 'W', 'Th', 'F', 'S', 'Su'}
        if all(day in valid_days for day in repeat_days):
            break
        print("Invalid repeat days format. Please try again.")

    location = input("Enter event location (Enter to skip): ")
    description = input("Enter event description (Enter to skip): ")

    while True:
        time_range_str = input("Enter event time range (e.g., 1:00 PM - 3:00 PM): ")
        start_time, end_time = parse_time_range(time_range_str)
        if start_time and end_time:
            break
        print("Invalid time format. Please try again.")

    create_event(service, start_date, repeat_days, title, location, description, end_date, start_time, end_time)

if __name__ == '__main__':
    main()
