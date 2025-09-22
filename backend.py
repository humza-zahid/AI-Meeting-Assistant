#!/usr/bin/env python3
"""
Simple FastAPI Backend for Google Calendar OAuth 2.0 Authentication
Standalone backend with all necessary functionality
"""

import os
import pickle
import json
import smtplib
from datetime import datetime, timedelta
from email.message import EmailMessage
from typing import List, Dict, Any, Optional

import uvicorn
from fastapi import FastAPI, HTTPException, Response, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, HTMLResponse
from pydantic import BaseModel

from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

import os
import re
import time
import json
import shutil
import asyncio
import subprocess
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path
import sys

from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, HttpUrl
import uvicorn

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import (
    TimeoutException,
    WebDriverException,
    SessionNotCreatedException,
    ElementClickInterceptedException,
)

from webdriver_manager.chrome import ChromeDriverManager

# Make backend utilities (FFmpegRecorder, etc.) available when running from this folder
BACKEND_ROOT = Path(__file__).resolve().parent.parent / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from recorder import FFmpegRecorder  # noqa: E402





# Environment loading
ENV_FILE_PATH = Path(__file__).resolve().parent / '.env'


def load_env_file(env_path: Path) -> None:
    """Populate os.environ with values from a .env file if present."""
    if not env_path.exists():
        return

    try:
        content = env_path.read_text()
    except Exception as exc:
        print(f"⚠️ Unable to read .env file: {exc}")
        return

    for line in content.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith('#') or '=' not in stripped:
            continue

        key, value = stripped.split('=', 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")

        if key and key not in os.environ:
            os.environ[key] = value


load_env_file(ENV_FILE_PATH)


# Configuration
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
CREDENTIALS_FILE = 'credentials.json'
TOKEN_FILE = 'token.pickle'
REDIRECT_URI = 'http://localhost:8000/auth/callback'
SUMMARY_REPORT_URL = 'https://docs.google.com/document/d/1RwhUXsPEGBzz92d_kJ_U7iNxTKTNOMsvcqd5CBZKMKI/edit?tab=t.0'
SUMMARY_DELAY_SECONDS = int(os.getenv('SUMMARY_DELAY_SECONDS', '300'))
SUMMARY_PDF_FILENAME = 'Google Meet Summary Report.pdf'
SUMMARY_PDF_PATH = Path(__file__).resolve().parent / SUMMARY_PDF_FILENAME
SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', '465'))
EMAIL_SENDER = os.getenv('EMAIL_SENDER')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
EMAIL_RECIPIENT = os.getenv('EMAIL_RECIPIENT')

# FastAPI app
app = FastAPI(
    title="Google Calendar OAuth 2.0 Simple",
    description="Simple standalone backend for Google Calendar authentication",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080", "http://127.0.0.1:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables
calendar_service = None
current_credentials = None
current_user_email = None

# Pydantic models
class AuthStatus(BaseModel):
    authenticated: bool
    user_email: Optional[str] = None
    message: str

class CalendarEvent(BaseModel):
    id: str
    title: str
    start: str
    end: str
    description: Optional[str] = None
    location: Optional[str] = None
    meeting_url: Optional[str] = None
    attendees: List[str] = []

class CalendarResponse(BaseModel):
    events: List[CalendarEvent]
    count: int
    user_email: str


# Pydantic models
class MeetJoinRequest(BaseModel):
    meet_url: HttpUrl
    headless: bool = False

class RecordingStopRequest(BaseModel):
    session_id: str


class SummaryEmailRequest(BaseModel):
    meet_url: Optional[HttpUrl] = None

class MeetSession:
    def __init__(self, session_id: str, meet_url: str):
        self.session_id = session_id
        self.meet_url = meet_url
        self.driver = None
        self.is_recording = False
        self.recording_start_time = None
        self.recording_path = None
        self.participant_count = 0
        self.recorder: Optional[FFmpegRecorder] = None

# Global session storage
active_sessions: Dict[str, MeetSession] = {}

def _detect_chrome_binary() -> Optional[str]:
    """Return the first Chrome/Chromium binary found on PATH."""
    for candidate in ("google-chrome", "chrome", "chromium-browser", "chromium"):
        path = shutil.which(candidate)
        if path:
            return path
    return None


def _resolve_driver_path() -> str:
    """Locate or download a chromedriver that matches the installed Chrome version."""
    # Allow explicit override via environment variable so users can pin to a custom driver.
    env_path = os.getenv("CHROMEDRIVER_PATH")
    if env_path and os.path.exists(env_path):
        return env_path

    system_driver = shutil.which("chromedriver")
    if system_driver and os.path.exists(system_driver):
        return system_driver

    chrome_binary = _detect_chrome_binary()
    chrome_version: Optional[str] = None
    if chrome_binary:
        try:
            output = subprocess.check_output([chrome_binary, "--version"], stderr=subprocess.STDOUT)
            decoded = output.decode().strip()
            match = re.search(r"(\d+\.\d+\.\d+\.\d+)", decoded)
            if match:
                chrome_version = match.group(1)
        except Exception:
            chrome_version = None

    try:
        manager = ChromeDriverManager()
        if chrome_version:
            manager.driver._browser_version = chrome_version
        driver_path = manager.install()
        return driver_path
    except Exception as exc:
        hint = (
            "Failed to obtain a compatible chromedriver automatically. "
            "Install one manually and set CHROMEDRIVER_PATH to its location."
        )
        raise HTTPException(status_code=500, detail=f"{hint} (error: {exc})")


def setup_chrome_driver(*, headless: bool = False):
    """Setup Chrome driver with appropriate options for Ubuntu"""
    chrome_options = Options()

    if headless:
        chrome_options.add_argument("--headless=new")

    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--start-maximized")

    # Reduce Selenium fingerprints so Meet renders the standard UI
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
    chrome_options.add_experimental_option("useAutomationExtension", False)
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")

    # Audio/Video permissions
    chrome_options.add_argument("--use-fake-ui-for-media-stream")
    chrome_options.add_argument("--use-fake-device-for-media-stream")

    # Media permissions
    prefs = {
        "profile.default_content_setting_values.media_stream_mic": 1,
        "profile.default_content_setting_values.media_stream_camera": 1,
        "profile.default_content_settings.popups": 0,
        "profile.managed_default_content_settings.images": 1
    }
    chrome_options.add_experimental_option("prefs", prefs)
    
    try:
        # First rely on Selenium Manager to locate a compatible driver. This succeeds when
        # Chrome/Selenium can auto-manage the matching binary.
        driver = webdriver.Chrome(options=chrome_options)
    
        # Mask webdriver hints so the Meet UI matches a real browser
        driver.execute_cdp_cmd(
            "Page.addScriptToEvaluateOnNewDocument",
            {
                "source": """
                    Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                    window.navigator.chrome = { runtime: {} };
                    Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
                    Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4]});
                """
            },
        )
        return driver
    except SessionNotCreatedException:
        # Selenium Manager likely provided an incompatible driver version. Fall back to
        # webdriver_manager with explicit version matching.
        try:
            driver_path = _resolve_driver_path()
            service = Service(driver_path)
            driver = webdriver.Chrome(service=service, options=chrome_options)

            driver.execute_cdp_cmd(
                "Page.addScriptToEvaluateOnNewDocument",
                {
                    "source": """
                        Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                        window.navigator.chrome = { runtime: {} };
                        Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
                        Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4]});
                    """
                },
            )
            return driver
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=(
                    "Failed to initialize Chrome driver after compatibility fallback: "
                    f"{e}. Please install chromedriver manually and set CHROMEDRIVER_PATH."
                ),
            )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to initialize Chrome driver: "
                f"{e}. Please install chromedriver: sudo apt-get install chromium-chromedriver"
            ),
        )

def join_google_meet(driver, meet_url: str) -> bool:
    """Join Google Meet and configure settings"""

    def click_with_fallback(target) -> bool:
        """Click an element with retries to work around intercepts."""
        if target is None:
            return False

        for attempt in range(4):
            try:
                driver.execute_script(
                    "if (arguments[0]) { arguments[0].scrollIntoView({block: 'center', inline: 'center'}); }",
                    target,
                )
            except Exception:
                pass

            time.sleep(0.3)

            try:
                target.click()
                return True
            except ElementClickInterceptedException:
                try:
                    ActionChains(driver).move_to_element(target).pause(0.2).click().perform()
                    return True
                except ElementClickInterceptedException:
                    time.sleep(0.4)
                    try:
                        driver.execute_script("arguments[0].click();", target)
                        return True
                    except Exception:
                        pass
            except Exception as exc:
                if "stale element" in str(exc).lower():
                    break

            time.sleep(0.4)

        return False

    def should_skip_join_candidate(element) -> bool:
        try:
            text = (element.text or '').strip().lower()
            aria = (element.get_attribute('aria-label') or '').lower()
            tooltip = (element.get_attribute('data-tooltip') or '').lower()
            combined = ' '.join(filter(None, [text, aria, tooltip]))
            if not combined:
                return False

            allowed_phrases = (
                'join now',
                'ask to join',
                'request to join',
                'join meeting',
            )
            if any(phrase in combined for phrase in allowed_phrases):
                return False

            return ('joined' in combined) or ('people' in combined and 'join' not in combined)
        except Exception:
            return False

    try:
        driver.get(meet_url)
        wait = WebDriverWait(driver, 30)
        
        # Wait for page to load
        time.sleep(5)
        
        # Try to find and fill name field
        name_selectors = [
            'input[placeholder*="name"]',
            'input[aria-label*="name"]',
            'input[type="text"]',
            '#name-field',
            '.name-input'
        ]
        
        name_entered = False
        for selector in name_selectors:
            try:
                name_field = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                name_field.clear()
                name_field.send_keys("AI Assistant")
                name_entered = True
                break
            except TimeoutException:
                continue
        
        if not name_entered:
            print("Warning: Could not find name field")
        
        # Turn off microphone and camera
        mic_selectors = [
            '[data-tooltip*="microphone"]',
            '[aria-label*="microphone"]',
            'button[data-is-muted="false"]',
            '.mic-button'
        ]
        
        camera_selectors = [
            '[data-tooltip*="camera"]',
            '[aria-label*="camera"]',
            'button[data-is-camera-on="true"]',
            '.camera-button'
        ]
        
        # Try to turn off microphone
        for selector in mic_selectors:
            try:
                mic_button = driver.find_element(By.CSS_SELECTOR, selector)
                if mic_button.is_enabled():
                    mic_button.click()
                    break
            except Exception:
                continue
        
        # Try to turn off camera
        for selector in camera_selectors:
            try:
                camera_button = driver.find_element(By.CSS_SELECTOR, selector)
                if camera_button.is_enabled():
                    camera_button.click()
                    break
            except Exception:
                continue
        
        time.sleep(2)
        
        # Try to click "Ask to join" or "Join now" button
        join_selectors = [
            'button[jsname="Qx7uuf"]',  # Google Meet specific
            'div[jsname="Qx7uuf"]',
            '.join-button',
            'button[data-mdc-dialog-action="primary-action"]',
        ]
        # sept21/test.py:268
        join_texts = [
            "Ask to join",
            "Request to join",
            "Join now",
            "Join meeting",
            "Request entry",
        ]
        join_xpaths = [
            f"//button[normalize-space()='{text}']" for text in join_texts
        ] + [
            f"//button[contains(., '{text}')]" for text in join_texts
        ] + [
            f"//span[contains(., '{text}')]/ancestor::button" for text in join_texts
        ] + [
            "//button[contains(@aria-label, 'join')]",
            "//div[@role='button' and contains(@aria-label, 'join')]",
            "//button[contains(@jsname, 'Qx7uuf')]",  # current Meet join button jsname
        ]

        join_clicked = False
        for xpath in join_xpaths:
            try:
                join_button = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
                if should_skip_join_candidate(join_button):
                    continue
                if click_with_fallback(join_button):
                    join_clicked = True
                    break
            except TimeoutException:
                continue
            except Exception:
                continue

        if not join_clicked:
            for selector in join_selectors:
                try:
                    join_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                    if should_skip_join_candidate(join_button):
                        continue
                    if click_with_fallback(join_button):
                        join_clicked = True
                        break
                except TimeoutException:
                    continue
                except Exception:
                    continue
        
        if not join_clicked:
            print("Warning: Could not find join button, but continuing...")
        
        # Wait a bit for the join process
        time.sleep(5)
        return True
        
    except Exception as e:
        print(f"Error joining meet: {str(e)}")
        return False

def get_participant_count(driver) -> int:
    """Get the number of participants in the meeting"""
    try:
        # Common selectors for participant count
        participant_selectors = [
            '[data-participant-count]',
            '.participant-count',
            '[aria-label*="participant"]',
            '[title*="participant"]'
        ]
        
        for selector in participant_selectors:
            try:
                element = driver.find_element(By.CSS_SELECTOR, selector)
                text = element.text or element.get_attribute('data-participant-count')
                if text and text.isdigit():
                    return int(text)
            except Exception:
                continue
        
        # Fallback: try to count visible participant elements
        participant_elements = driver.find_elements(By.CSS_SELECTOR, '[data-participant-id], .participant-item, [data-sender-id]')
        return len(participant_elements)
        
    except Exception as e:
        print(f"Error getting participant count: {str(e)}")
        return 0



def load_credentials():
    """Load existing credentials from token file"""
    global current_credentials, current_user_email
    
    if os.path.exists(TOKEN_FILE):
        try:
            with open(TOKEN_FILE, 'rb') as token:
                creds = pickle.load(token)
                
            if creds and creds.valid:
                current_credentials = creds
                # Try to get user email
                try:
                    service = build('calendar', 'v3', credentials=creds)
                    calendar_list = service.calendarList().list().execute()
                    primary_calendar = next((cal for cal in calendar_list['items'] if cal.get('primary')), None)
                    if primary_calendar:
                        current_user_email = primary_calendar.get('id', 'unknown@gmail.com')
                except Exception as e:
                    print(f"Warning: Could not get user email: {e}")
                    current_user_email = 'authenticated@gmail.com'
                
                print(f"✅ Loaded existing credentials for: {current_user_email}")
                return True
            elif creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(GoogleRequest())
                    save_credentials(creds)
                    current_credentials = creds
                    print("✅ Refreshed expired credentials")
                    return True
                except Exception as e:
                    print(f"❌ Failed to refresh credentials: {e}")
                    return False
        except Exception as e:
            print(f"❌ Failed to load credentials: {e}")
            return False
    
    return False

def save_credentials(creds):
    """Save credentials to token file"""
    try:
        with open(TOKEN_FILE, 'wb') as token:
            pickle.dump(creds, token)
        print("✅ Credentials saved successfully")
    except Exception as e:
        print(f"❌ Failed to save credentials: {e}")

def get_calendar_service():
    """Get authenticated calendar service"""
    global calendar_service, current_credentials
    
    if current_credentials and current_credentials.valid:
        if not calendar_service:
            calendar_service = build('calendar', 'v3', credentials=current_credentials)
        return calendar_service
    
    return None

def extract_meeting_url(event_data: Dict) -> Optional[str]:
    """Extract meeting URL from event data"""
    # Check hangout link (Google Meet)
    if event_data.get('hangoutLink'):
        return event_data['hangoutLink']
    
    # Check conference data
    conference_data = event_data.get('conferenceData', {})
    entry_points = conference_data.get('entryPoints', [])
    for entry_point in entry_points:
        if entry_point.get('entryPointType') == 'video':
            return entry_point.get('uri')
    
    # Check description for meeting links
    description = event_data.get('description', '')
    if description:
        # Common meeting URL patterns
        import re
        patterns = [
            r'https://meet\.google\.com/[a-z-]+',
            r'https://zoom\.us/j/\d+',
            r'https://teams\.microsoft\.com/l/meetup-join/[^\\s]+',
            r'https://[^\\s]*meet[^\\s]*'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, description)
            if match:
                return match.group(0)
    
    # Check location field
    location = event_data.get('location', '')
    if location and ('meet.google.com' in location or 'zoom.us' in location or 'teams.microsoft.com' in location):
        return location
    
    return None


def send_summary_email(recipient_email: Optional[str], meet_url: Optional[str] = None) -> None:
    """Send the summary PDF via SMTP to the requested recipient."""
    if not EMAIL_SENDER or not EMAIL_PASSWORD:
        print("⚠️ Email sender credentials not configured; skipping summary email.")
        return

    recipient = recipient_email or EMAIL_RECIPIENT
    if not recipient:
        print("⚠️ No recipient email available; skipping summary email.")
        return

    if not SUMMARY_PDF_PATH.exists():
        print(f"⚠️ Summary PDF not found at: {SUMMARY_PDF_PATH}")
        return

    try:
        message = EmailMessage()
        message['Subject'] = 'Google Meet Summary Report'
        message['From'] = EMAIL_SENDER
        message['To'] = recipient
        document_link = SUMMARY_REPORT_URL
        body_meet_url = meet_url or 'Not provided'
        message.set_content(
            (
                "Hello,\n\n"
                "Here is the summary report for your recent meeting.\n\n"
                f"Meet URL: {body_meet_url}\n"
                f"Summary Document: {document_link}\n\n"
                "The PDF summary is attached.\n\n"
                "Regards,\nGoogle Meet Dashboard"
            )
        )

        pdf_bytes = SUMMARY_PDF_PATH.read_bytes()
        message.add_attachment(
            pdf_bytes,
            maintype='application',
            subtype='pdf',
            filename=SUMMARY_PDF_FILENAME,
        )

        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as smtp:
            smtp.login(EMAIL_SENDER, EMAIL_PASSWORD)
            smtp.send_message(message)

        print(f"📧 Summary email sent to {recipient}")

    except Exception as exc:
        print(f"❌ Failed to send summary email: {exc}")
        raise


async def schedule_summary_email(meet_url: str, recipient_email: Optional[str] = None) -> None:
    """Delay summary email sending by configured interval."""
    try:
        await asyncio.sleep(SUMMARY_DELAY_SECONDS)
        await asyncio.to_thread(send_summary_email, recipient_email, meet_url)
    except Exception as exc:
        print(f"❌ Summary email scheduling failed: {exc}")

@app.on_event("startup")
async def startup_event():
    """Initialize the application"""
    print("🚀 Starting Google Calendar OAuth 2.0 Simple Backend...")
    
    # Check if credentials file exists
    if not os.path.exists(CREDENTIALS_FILE):
        print(f"❌ Credentials file not found: {CREDENTIALS_FILE}")
        print("Please ensure credentials.json is in the same directory as this script")
        return
    
    # Load existing credentials if available
    load_credentials()
    
    print("✅ Backend initialized successfully")
    print(f"📁 Working directory: {os.getcwd()}")
    print(f"🔐 Credentials file: {CREDENTIALS_FILE}")
    print(f"🎫 Token file: {TOKEN_FILE}")
    print(f"🌐 Redirect URI: {REDIRECT_URI}")

@app.get("/")
async def root():
    """Root endpoint with basic info"""
    return {
        "message": "Google Calendar OAuth 2.0 Simple Backend",
        "status": "running",
        "authenticated": current_credentials is not None and current_credentials.valid,
        "user_email": current_user_email,
        "endpoints": {
            "/auth/status": "Check authentication status",
            "/auth/connect": "Start OAuth flow",
            "/auth/callback": "OAuth callback handler",
            "/auth/logout": "Logout and clear credentials",
            "/calendar/events": "Get calendar events"
        }
    }

@app.get("/auth/status")
async def auth_status() -> AuthStatus:
    """Check current authentication status"""
    global current_credentials, current_user_email
    
    if current_credentials and current_credentials.valid:
        return AuthStatus(
            authenticated=True,
            user_email=current_user_email,
            message="User is authenticated"
        )
    else:
        return AuthStatus(
            authenticated=False,
            message="User is not authenticated"
        )

@app.post("/auth/connect")
async def connect_calendar():
    """Start OAuth 2.0 flow"""
    try:
        if not os.path.exists(CREDENTIALS_FILE):
            raise HTTPException(status_code=500, detail="Credentials file not found")
        
        # Create OAuth flow
        flow = Flow.from_client_secrets_file(
            CREDENTIALS_FILE,
            scopes=SCOPES,
            redirect_uri=REDIRECT_URI
        )
        
        # Generate authorization URL
        auth_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'
        )
        
        print(f"🔗 Generated OAuth URL: {auth_url}")
        
        return {
            "auth_url": auth_url,
            "message": "Please visit the URL to authorize the application"
        }
        
    except Exception as e:
        print(f"❌ Failed to generate auth URL: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate auth URL: {str(e)}")

@app.get("/auth/callback")
async def auth_callback(response: Response, code: str, state: str = None):
    """Handle OAuth callback"""
    global current_credentials, current_user_email, calendar_service
    
    try:
        print(f"🔄 OAuth callback received - Code: {code[:20]}...")
        
        if not code:
            raise HTTPException(status_code=400, detail="Authorization code is required")
        
        # Create OAuth flow
        flow = Flow.from_client_secrets_file(
            CREDENTIALS_FILE,
            scopes=SCOPES,
            redirect_uri=REDIRECT_URI
        )
        
        # Exchange code for token
        flow.fetch_token(code=code)
        current_credentials = flow.credentials
        
        # Save credentials
        save_credentials(current_credentials)
        
        # Build calendar service
        calendar_service = build('calendar', 'v3', credentials=current_credentials)
        
        # Get user email
        try:
            calendar_list = calendar_service.calendarList().list().execute()
            primary_calendar = next((cal for cal in calendar_list['items'] if cal.get('primary')), None)
            if primary_calendar:
                current_user_email = primary_calendar.get('id', 'authenticated@gmail.com')
            else:
                current_user_email = 'authenticated@gmail.com'
        except Exception as e:
            print(f"Warning: Could not get user email: {e}")
            current_user_email = 'authenticated@gmail.com'
        
        print(f"✅ OAuth authentication successful for: {current_user_email}")
        
        # Redirect to frontend with success
        return RedirectResponse(
            url="http://localhost:8080/auth.html?auth=success",
            status_code=302
        )
        
    except Exception as e:
        print(f"❌ OAuth callback failed: {e}")
        return RedirectResponse(
            url=f"http://localhost:8080/auth.html?auth=error&message={str(e)}",
            status_code=302
        )

@app.post("/auth/logout")
async def logout():
    """Logout and clear credentials"""
    global current_credentials, current_user_email, calendar_service
    
    try:
        # Clear global variables
        current_credentials = None
        current_user_email = None
        calendar_service = None
        
        # Remove token file
        if os.path.exists(TOKEN_FILE):
            os.remove(TOKEN_FILE)
            print("✅ Token file removed")
        
        return {"message": "Successfully logged out"}
        
    except Exception as e:
        print(f"❌ Logout failed: {e}")
        raise HTTPException(status_code=500, detail=f"Logout failed: {str(e)}")

@app.get("/calendar/events")
async def get_calendar_events(days: int = 7) -> CalendarResponse:
    """Get calendar events for the specified number of days"""
    global current_credentials, current_user_email
    
    if not current_credentials or not current_credentials.valid:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        service = get_calendar_service()
        if not service:
            raise HTTPException(status_code=500, detail="Calendar service not available")
        
        # Calculate time range - include past events for dashboard
        now = datetime.utcnow()
        start_time = now - timedelta(days=1)  # Include events from yesterday
        end_time = now + timedelta(days=days)

        start_time_iso = start_time.isoformat() + 'Z'
        end_time_iso = end_time.isoformat() + 'Z'
        
        print(f"📅 Fetching events from {start_time_iso} to {end_time_iso}")

        # Get events from primary calendar
        events_result = service.events().list(
            calendarId='primary',
            timeMin=start_time_iso,
            timeMax=end_time_iso,
            maxResults=100,  # Increased limit for dashboard
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        print(f"✅ Found {len(events)} events")
        
        # Convert to our format
        calendar_events = []
        for event in events:
            # Get start and end times
            start = event['start'].get('dateTime', event['start'].get('date'))
            end = event['end'].get('dateTime', event['end'].get('date'))
            
            # Handle all-day events
            if 'T' not in start:
                start += 'T00:00:00Z'
            if 'T' not in end:
                end += 'T23:59:59Z'
            
            # Get attendees
            attendees = []
            if 'attendees' in event:
                attendees = [attendee.get('email', '') for attendee in event['attendees']]
            
            # Extract meeting URL
            meeting_url = extract_meeting_url(event)
            
            calendar_event = CalendarEvent(
                id=event['id'],
                title=event.get('summary', 'Untitled Event'),
                start=start,
                end=end,
                description=event.get('description', ''),
                location=event.get('location', ''),
                meeting_url=meeting_url,
                attendees=attendees
            )
            
            calendar_events.append(calendar_event)
        
        return CalendarResponse(
            events=calendar_events,
            count=len(calendar_events),
            user_email=current_user_email or 'unknown@gmail.com'
        )
        
    except Exception as e:
        print(f"❌ Failed to get calendar events: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get calendar events: {str(e)}")


@app.post("/summary/email")
async def trigger_summary_email(request: Optional[SummaryEmailRequest] = None):
    """Send the summary PDF to the authenticated user via SMTP."""
    global current_credentials, current_user_email

    if not current_credentials or not current_credentials.valid:
        raise HTTPException(status_code=401, detail="Not authenticated")

    recipient = current_user_email or EMAIL_RECIPIENT
    if not recipient:
        raise HTTPException(status_code=400, detail="No recipient email available")

    meet_url = request.meet_url if request else None

    try:
        await asyncio.to_thread(send_summary_email, recipient, meet_url)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to send summary email: {exc}")

    return {
        "message": "Summary report emailed successfully",
        "recipient": recipient
    }


@app.post("/join-and-record")
async def join_and_record_meet(request: MeetJoinRequest):
    """Join Google Meet and start recording"""
    session_id = f"session_{int(time.time())}"
    meet_url = str(request.meet_url)
    
    try:
        # Create session
        session = MeetSession(session_id, meet_url)
        
        # Setup driver
        session.driver = setup_chrome_driver(headless=request.headless)

        def _join_and_prepare():
            # Join meet (blocking call)
            if not join_google_meet(session.driver, meet_url):
                session.driver.quit()
                raise HTTPException(status_code=400, detail="Failed to join Google Meet")

            # Prepare recording directories and start FFmpeg capture
            recordings_root = Path(os.getenv("MEET_RECORDINGS_ROOT", Path(__file__).resolve().parent.parent / "recordings"))
            recordings_root.mkdir(parents=True, exist_ok=True)

            dated_dir = recordings_root / datetime.now().strftime("%Y-%m-%d")
            dated_dir.mkdir(exist_ok=True)

            base_name = f"meet_recording_{datetime.now().strftime('%H%M%S')}"
            recorder = FFmpegRecorder(out_dir=str(dated_dir), base_name=base_name)

            if not recorder.start():
                session.driver.quit()
                raise HTTPException(status_code=500, detail="Failed to start screen recording")

            session.recorder = recorder
            session.is_recording = True
            session.recording_start_time = datetime.now()
            session.recording_path = Path(recorder.out_path)

            metadata_path = session.recording_path.with_suffix(".json")
            metadata = {
                "session_id": session_id,
                "meet_url": meet_url,
                "recording_started_at": session.recording_start_time.isoformat(),
                "output_path": str(session.recording_path),
                "headless": request.headless,
            }
            try:
                metadata_path.write_text(json.dumps(metadata, indent=2))
            except Exception:
                pass

            active_sessions[session_id] = session

        # Perform the join/record preparation in background threads to avoid blocking the event loop
        try:
            await asyncio.to_thread(_join_and_prepare)
        except HTTPException:
            raise
        except Exception as exc:
            if session.driver:
                try:
                    session.driver.quit()
                except Exception:
                    pass
            raise HTTPException(status_code=500, detail=f"Failed to initialize recording: {exc}")

        recipient_email = current_user_email or EMAIL_RECIPIENT
        asyncio.create_task(schedule_summary_email(meet_url, recipient_email))
        return {
            "success": True,
            "session_id": session_id,
            "message": "Recording started",
            "recording_started_at": session.recording_start_time.isoformat(),
            "recording_path": str(session.recording_path),
        }
        
    except Exception as e:
        if 'session' in locals() and session.driver:
            session.driver.quit()
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.get("/participant-count/{session_id}")
async def get_participants(session_id: str):
    """Get the number of participants in the meeting"""
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = active_sessions[session_id]
    
    if not session.driver:
        raise HTTPException(status_code=400, detail="Session driver not available")
    
    try:
        participant_count = get_participant_count(session.driver)
        session.participant_count = participant_count
        
        return {
            "session_id": session_id,
            "participant_count": participant_count,
            "is_recording": session.is_recording
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting participant count: {str(e)}")

@app.post("/stop-recording")
async def stop_recording(request: RecordingStopRequest):
    """Stop recording and return the recording path"""
    session_id = request.session_id
    
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = active_sessions[session_id]
    
    try:
        recording_path: Optional[str] = None
        recording_duration: Optional[str] = None
        recording_end_time = datetime.now()

        if session.is_recording:
            session.is_recording = False

            if session.recorder:
                stopped_path = session.recorder.stop()
                recording_path = stopped_path or (
                    str(session.recording_path) if session.recording_path else None
                )
            else:
                recording_path = str(session.recording_path) if session.recording_path else None

            if session.recording_start_time:
                recording_duration = str(recording_end_time - session.recording_start_time)

        # Always attempt to shut down the browser
        if session.driver:
            try:
                session.driver.quit()
            except Exception:
                pass

        # Remove session bookkeeping
        del active_sessions[session_id]

        return {
            "success": True,
            "session_id": session_id,
            "message": "Recording stopped successfully",
            "recording_path": recording_path,
            "recording_duration": recording_duration,
            "stopped_at": recording_end_time.isoformat(),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error stopping recording: {str(e)}")

@app.get("/active-sessions")
async def get_active_sessions():
    """Get all active recording sessions"""
    sessions_info = []
    for session_id, session in active_sessions.items():
        sessions_info.append({
            "session_id": session_id,
            "meet_url": session.meet_url,
            "is_recording": session.is_recording,
            "start_time": session.recording_start_time.isoformat() if session.recording_start_time else None,
            "participant_count": session.participant_count
        })
    
    return {"active_sessions": sessions_info}

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up all sessions on shutdown"""
    for session in active_sessions.values():
        if session.recorder:
            try:
                session.recorder.stop()
            except Exception:
                pass
        if session.driver:
            try:
                session.driver.quit()
            except Exception:
                pass
    active_sessions.clear()



if __name__ == "__main__":
    print("🚀 Starting Google Calendar OAuth 2.0 Simple Backend...")
    print("📁 Make sure credentials.json is in the same directory")
    print("🌐 Frontend should be running on http://localhost:8080")
    print("⚠️  Press Ctrl+C to stop the server")
    default_root = Path(__file__).resolve().parent
    recordings_dir = Path(os.getenv("MEET_RECORDINGS_ROOT", default_root.parent / "recordings"))
    recordings_dir.mkdir(parents=True, exist_ok=True)

    uvicorn.run(
        "backend:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
