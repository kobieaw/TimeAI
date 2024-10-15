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
                    "client_secret": "YOUR_CLIENT_SECRET",
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
    """
    Function to find the next available time slot in the calendar
    Args:
        service: Google Calendar API service instance
        duration_hours: Desired duration for the hobby event in hours
    Returns:
        start_time, end_time: Tuple containing the start and end times for the event
    """
    # Assume the start time is the next hour from now
    now = datetime.datetime.now(tz.tzlocal())
    start_time = now.replace(minute=0, second=0, microsecond=0) + datetime.timedelta(hours=1)
    
    # Calculate the end time based on the given duration
    end_time = start_time + datetime.timedelta(hours=duration_hours)
    
    # For simplicity, no check is made against the user's actual calendar events
    return start_time, end_time

def split_hobby_duration(duration_hours):
    """
    Function to split a hobby duration into acceptable chunks if it exceeds a maximum duration
    Args:
        duration_hours: Total duration of the hobby in hours
    Returns:
        List of durations split into acceptable chunks
    """
    # Maximum duration for a single chunk
    max_duration = 2

    durations = []
    
    # Split the total duration into 2-hour chunks
    while duration_hours > max_duration:
        durations.append(max_duration)
        duration_hours -= max_duration
    
    # Add the remaining time, if any
    if duration_hours > 0:
        durations.append(duration_hours)
    
    return durations

def add_hobby_event(service, hobby, duration_hours):
    """
    Function to add a hobby event to the Google Calendar
    Args:
        service: Google Calendar API service instance
        hobby: Name of the hobby to add to the calendar
        duration_hours: Duration in hours for the hobby
    """
    # Convert current time to local timezone
    local_zone = tz.tzlocal()
    now_local = datetime.datetime.now(local_zone)

    # Check if the hobby duration is longer than 2 hours and split it if necessary
    if duration_hours > 2:
        durations = split_hobby_duration(duration_hours)
    else:
        durations = [duration_hours]

    # Loop through each split duration to create events
    for duration in durations:
        # Find the next available time slot for the given duration
        start_time, end_time = find_next_available_time(service, duration)
        if not start_time or not end_time:
            print("Could not find an available time slot.")
            return

        # Define the event details
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

        # Try adding the event to the user's primary calendar
        try:
            event = service.events().insert(calendarId='primary', body=event).execute()
            print(f"Event created: {event.get('htmlLink')}")
        except Exception as e:
            print(f"An error occurred: {e}")

if __name__ == '__main__':
    # Prompt user for hobby name and duration
    hobby = input("Enter your hobby: ")
    try:
        # Ensure the input duration is valid
        duration_hours = float(input("Enter the duration in hours for your hobby: "))
        if duration_hours <= 0:
            raise ValueError("Duration must be a positive number.")
    except ValueError as e:
        print(f"Invalid input: {e}")
        exit(1)

    # Get Google Calendar service instance
    service = get_calendar_service()
    # Add the hobby event to the calendar
    add_hobby_event(service, hobby, duration_hours)