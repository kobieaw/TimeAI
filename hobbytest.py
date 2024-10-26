# filename: add_hobby_to_calendar.py
import datetime
import os
import pickle
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from dateutil import tz
from dateutil.parser import parse

# If modifying these SCOPES, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/calendar']

def get_calendar_service():
    """
    Function to authenticate and get Google Calendar API service instance
    Returns:
        service: Google Calendar API service instance
    """
    creds = None
    token_path = 'token.pickle'
    
    # Load existing token if available
    if os.path.exists(token_path):
        with open(token_path, 'rb') as token:
            creds = pickle.load(token)
    
    # If credentials are not valid or do not exist, initiate a new authentication flow
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())  # Refresh expired credentials
        else:
            # Prompt user to sign in to their Google account
            flow = InstalledAppFlow.from_client_config({
                "installed": {
                    "client_id": "747007421824-juh0dhucbs8323lgj3r81gufqm1f82nq.apps.googleusercontent.com",
                    "project_id": "aesthetic-nova-418303",
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                    "client_secret": "",
                    "redirect_uris": [
                        "urn:ietf:wg:oauth:2.0:oob",
                        "http://localhost"
                    ]
                }
            }, SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(token_path, 'wb') as token:
            pickle.dump(creds, token)

    # Build the Google Calendar service
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

# Additional Function 1: Check for Conflicting Events
def is_time_slot_available(service, start_time, end_time):
    events_result = service.events().list(
        calendarId='primary',
        timeMin=start_time.isoformat(),
        timeMax=end_time.isoformat(),
        singleEvents=True,
        orderBy='startTime'
    ).execute()
    events = events_result.get('items', [])
    return len(events) == 0

# Additional Function 2: Find the Next Available Time with No Conflicts
def find_next_available_time_no_conflict(service, duration_hours):
    now = datetime.datetime.now(tz.tzlocal())
    start_time = now.replace(minute=0, second=0, microsecond=0) + datetime.timedelta(hours=1)
    end_time = start_time + datetime.timedelta(hours=duration_hours)

    while not is_time_slot_available(service, start_time, end_time):
        start_time += datetime.timedelta(hours=1)
        end_time = start_time + datetime.timedelta(hours=duration_hours)
    
    return start_time, end_time

# Additional Function 3: Set a Recurring Hobby Event
def add_recurring_hobby_event(service, hobby, duration_hours, recurrence_interval):
    start_time, end_time = find_next_available_time_no_conflict(service, duration_hours)

    event = {
        'summary': hobby,
        'description': f'Time allocated for {hobby}',
        'start': {
            'dateTime': start_time.isoformat(),
            'timeZone': 'America/New_York',
        },
        'end': {
            'dateTime': end_time.isoformat(),
            'timeZone': 'America/New_York',
        },
        'recurrence': [
            f'RRULE:FREQ=WEEKLY;INTERVAL={recurrence_interval}'
        ],
    }

    try:
        event = service.events().insert(calendarId='primary', body=event).execute()
        print(f"Recurring event created: {event.get('htmlLink')}")
    except Exception as e:
        print(f"An error occurred: {e}")

# Additional Function 4: Delete All Events by Name
def delete_all_events_by_name(service, event_name):
    try:
        now = datetime.datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
        events_result = service.events().list(
            calendarId='primary',
            timeMin=now,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        events = events_result.get('items', [])

        deleted = False
        for event in events:
            if event['summary'].lower() == event_name.lower():
                service.events().delete(calendarId='primary', eventId=event['id']).execute()
                print(f"Event '{event_name}' deleted successfully.")
                deleted = True
        if not deleted:
            print(f"No event found with the name '{event_name}'.")
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

    recurrence = input("Would you like this to be a recurring event? (yes/no): ").strip().lower()
    service = get_calendar_service()

    if recurrence == 'yes':
        try:
            recurrence_interval = int(input("Enter the recurrence interval in weeks: "))
            if recurrence_interval <= 0:
                raise ValueError("Recurrence interval must be a positive number.")
            add_recurring_hobby_event(service, hobby, duration_hours, recurrence_interval)
        except ValueError as e:
            print(f"Invalid input: {e}")
            exit(1)
    else:
        add_hobby_event(service, hobby, duration_hours)
    
    delete = input("Would you like to delete an event? (yes/no): ").strip().lower()
    if delete == 'yes':
        event_name = input("Enter the event name to delete: ")
        delete_all_events_by_name(service, event_name)
