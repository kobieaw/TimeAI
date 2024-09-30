

# filename: add_hobby_to_calendar.py
import datetime
from dotenv import load_dotenv
load_dotenv()
import os
import pickle
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from dateutil import tz
from dateutil.parser import parse

print("Credentials Path:", os.getenv('GOOGLE_CALENDAR_CREDENTIALS'))
print("Token Path:", os.getenv('GOOGLE_CALENDAR_TOKEN'))

# If modifying these SCOPES, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/calendar']

def get_calendar_service():
    creds = None
    # Use environment variables for credentials
    credentials_path = os.getenv('GOOGLE_CALENDAR_CREDENTIALS')
    token_path = os.getenv('GOOGLE_CALENDAR_TOKEN')
    
    if os.path.exists(token_path):
        with open(token_path, 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(token_path, 'wb') as token:
            pickle.dump(creds, token)

    service = build('calendar', 'v3', credentials=creds)
    return service



def find_next_available_time(service, duration_hours):
    # Assume the start time is the next hour from now
    now = datetime.datetime.now(tz.tzlocal())
    start_time = now.replace(minute=0, second=0, microsecond=0) + datetime.timedelta(hours=1)
    
    # Calculate the end time based on the duration
    end_time = start_time + datetime.timedelta(hours=duration_hours)
    
    # For simplicity, no check is made against the user's actual calendar events
    return start_time, end_time


# def split_hobby_duration(duration_hours):
    # Logic to split the hobby duration into acceptable chunks
    # This function should return a list of durations
    # Placeholder for actual implementation
    # pass
def split_hobby_duration(duration_hours):
    # Maximum duration for a single chunk
    max_duration = 2

    durations = []
    
    # Split duration into 2-hour chunks
    while duration_hours > max_duration:
        durations.append(max_duration)
        duration_hours -= max_duration
    
    # Add the remainder, if any
    if duration_hours > 0:
        durations.append(duration_hours)
    
    return durations

def add_hobby_event(service, hobby, duration_hours):
    # Convert to local timezone
    local_zone = tz.tzlocal()
    now_local = datetime.datetime.now(local_zone)

    # Check if the hobby duration is longer than 2 hours and split it if necessary
    if duration_hours > 2:
        durations = split_hobby_duration(duration_hours)
    else:
        durations = [duration_hours]

    for duration in durations:
        start_time, end_time = find_next_available_time(service, duration)
        if not start_time or not end_time:
            print("Could not find an available time slot.")
            return

        event = {
            'summary': hobby,
            'description': f'Time allocated for {hobby}',
             'start': {
                'dateTime': start_time.isoformat(),
                'timeZone': 'America/New_York',  # Example: Use a valid IANA Time Zone ID
            },
            'end': {
                'dateTime': end_time.isoformat(),
                'timeZone': 'America/New_York',  # Same here
            },
        }

        try:
            event = service.events().insert(calendarId='primary', body=event).execute()
            print(f"Event created: {event.get('htmlLink')}")
        except Exception as e:
            print(f"An error occurred: {e}")

if __name__ == '__main__':
    hobby = input("Enter your hobby: ")
    try:
        duration_hours = float(input("Enter the duration in hours for your hobby: "))
        if duration_hours <= 0:
            raise ValueError("Duration must be a positive number.")
    except ValueError as e:
        print(f"Invalid input: {e}")
        exit(1)

    service = get_calendar_service()
    add_hobby_event(service, hobby, duration_hours)