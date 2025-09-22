#!/usr/bin/env python3
"""
Google Meet Recorder API
FastAPI application to join and record Google Meet sessions
"""

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
from selenium.common.exceptions import TimeoutException, WebDriverException, SessionNotCreatedException

from webdriver_manager.chrome import ChromeDriverManager

# Make backend utilities (FFmpegRecorder, etc.) available when running from this folder
BACKEND_ROOT = Path(__file__).resolve().parent.parent / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from recorder import FFmpegRecorder  # noqa: E402

# Pydantic models
class MeetJoinRequest(BaseModel):
    meet_url: HttpUrl
    headless: bool = False

class RecordingStopRequest(BaseModel):
    session_id: str

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

app = FastAPI(
    title="Google Meet Recorder API",
    description="API to join and record Google Meet sessions",
    version="1.0.0"
)
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
            'button:contains("Ask to join")',
            'button:contains("Join now")',
            '[data-tooltip*="join"]',
            '[aria-label*="join"]',
            '.join-button',
            'button[jsname="Qx7uuf"]'  # Google Meet specific
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
                join_button.click()
                join_clicked = True
                break
            except TimeoutException:
                continue

        for selector in join_selectors:
            try:
                if 'contains' in selector:
                    # Use XPath for text-based selectors
                    xpath_selector = f"//button[contains(text(), '{selector.split('\"')[1]}')]"
                    join_button = wait.until(EC.element_to_be_clickable((By.XPATH, xpath_selector)))
                else:
                    join_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                
                join_button.click()
                join_clicked = True
                break
            except TimeoutException:
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
    # Ensure recordings directory exists (outside the watched source tree to avoid reload loops)
    default_root = Path(__file__).resolve().parent
    recordings_dir = Path(os.getenv("MEET_RECORDINGS_ROOT", default_root.parent / "recordings"))
    recordings_dir.mkdir(parents=True, exist_ok=True)

    uvicorn.run(
        "test:app",
        host=os.getenv("MEET_API_HOST", "0.0.0.0"),
        port=int(os.getenv("MEET_API_PORT", "8000")),
        reload=os.getenv("MEET_API_RELOAD", "false").lower() == "true"
    )
