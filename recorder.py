# recorder.py


import os, subprocess, datetime, platform, sys
import logging
import fcntl  # For Linux file locking

logger = logging.getLogger(__name__)

class FFmpegRecorder:
    def __init__(self, out_dir: str, base_name: str, fps: int = 25):
        # Set platform detection first, before any other methods are called
        self.is_linux = 'linux' in platform.system().lower()
        
        os.makedirs(out_dir, exist_ok=True)
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        safe = "".join(c for c in base_name if c.isalnum() or c in " _-").strip()
        self.out_path = os.path.join(out_dir, f"{safe}_{ts}.mp4")
        self.proc = None
        self.fps = str(fps)
        self.is_recording = False
        self.start_time = None
        self.log_file = os.path.join(out_dir, 'recording.log')
        
        # Setup logging before building command
        self._setup_logging()
        
        print(f"\n[{datetime.datetime.now().strftime('%H:%M:%S')}] 🎥 Initializing recorder for: {base_name}")
        logger.info(f"Initializing recorder to: {self.out_path}")

        self.setup_ubuntu_env()
        
        # Build command after all attributes are set
        self.cmd = self._build_cmd()

    def _setup_logging(self):
        """Setup file logging for Linux"""
        if self.is_linux:
            try:
                os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
                self.log_handler = logging.FileHandler(self.log_file)
                self.log_handler.setFormatter(
                    logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
                )
                logger.addHandler(self.log_handler)
                # Write to both file and terminal
                self._log_message(f"Recording session started for: {self.out_path}")
            except Exception as e:
                print(f"Error setting up logging: {e}")

    def _log_message(self, message, level='info'):
        """Log message to both file and terminal on Linux"""
        timestamp = datetime.datetime.now().strftime('%H:%M:%S')
        formatted = f"\n[{timestamp}] {message}"
        print(formatted, flush=True)
        if self.is_linux:
            try:
                with open(self.log_file, 'a') as f:
                    fcntl.flock(f, fcntl.LOCK_EX)
                    f.write(formatted + '\n')
                    fcntl.flock(f, fcntl.LOCK_UN)
            except Exception as e:
                print(f"Error writing to log file: {e}")

    def setup_ubuntu_env(self):
        """Ensure Ubuntu environment variables are set"""
        if 'linux' in platform.system().lower():
            if 'DISPLAY' not in os.environ:
                os.environ['DISPLAY'] = ':0.0'
            if 'REC_SIZE' not in os.environ:
                os.environ['REC_SIZE'] = '1920x1080'
            
            self._log_message(f"Ubuntu environment: DISPLAY={os.environ.get('DISPLAY')}, REC_SIZE={os.environ.get('REC_SIZE')}")

    def _build_cmd(self):
        sys = platform.system().lower()
        if 'linux' in sys:
            # Get environment variables with fallbacks
            display = os.environ.get("DISPLAY", ":0.0")
            rec_size = os.environ.get("REC_SIZE", "1920x1080")
            
            # Log environment status
            self._log_message(f"Recording with: display={display}, size={rec_size}")
            
            # For Ubuntu/Linux, get both system audio and mic
            audio_sources = self._get_linux_audio_sources()

            if audio_sources.get('use_alsa', False):
                # Use ALSA fallback (video + mic only, no system audio)
                cmd = [
                    "ffmpeg", "-y",
                    "-video_size", rec_size,
                    "-framerate", self.fps, "-f", "x11grab", "-i", display,
                    "-f", "alsa", "-i", audio_sources['alsa_device'],  # Hardware microphone
                    "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "192k",
                    "-loglevel", "warning",
                    self.out_path
                ]
                self._log_message(f"Using ALSA fallback command with: {display}, {audio_sources['alsa_device']}")
            else:
                # Use PulseAudio (original method)
                cmd = [
                    "ffmpeg", "-y",
                    "-video_size", rec_size,
                    "-framerate", self.fps, "-f", "x11grab", "-i", display,
                    "-f", "pulse", "-i", audio_sources['monitor'],  # System audio
                    "-f", "pulse", "-i", audio_sources['mic'],      # Microphone
                    "-filter_complex", "amix=inputs=2:duration=first",  # Mix both audio sources
                    "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "192k",
                    "-loglevel", "warning",
                    self.out_path
                ]
                self._log_message(f"Using PulseAudio command with: {display}, {audio_sources}")

            return cmd
        if 'darwin' in sys:  # macOS
            return [
                "ffmpeg","-y",
                "-f","avfoundation","-framerate", self.fps, "-i", os.environ.get("AVF_INPUT","1:0"),
                "-c:v","libx264","-preset","veryfast","-pix_fmt","yuv420p",
                "-c:a","aac","-b:a","128k", self.out_path
            ]
        # Windows
        ffmpeg_path = r"C:\ffmpeg\bin\ffmpeg.exe"  # full path to ffmpeg.exe
        return [
            ffmpeg_path, "-y",
            "-f", "gdigrab", "-framerate", self.fps, "-i", "desktop",
            "-f", "dshow", "-i", "audio=Microphone (Realtek High Definition Audio)",
            "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "128k", self.out_path
        ]

    def _get_linux_audio_sources(self):
        """Get both system audio and microphone sources for Linux with ALSA fallback"""
        sources = {'monitor': 'default', 'mic': 'default', 'use_alsa': False}

        pulse_working = False
        try:
            # Test if PulseAudio is actually working
            test_result = subprocess.run(
                ["pactl", "info"],
                capture_output=True, text=True, timeout=5
            )

            if test_result.returncode == 0 and "Server String" in test_result.stdout:
                # PulseAudio is working, get sources
                # Get default microphone
                mic_result = subprocess.run(
                    ["pactl", "get-default-source"],
                    capture_output=True, text=True, timeout=5
                )
                if mic_result.returncode == 0:
                    sources['mic'] = mic_result.stdout.strip()

                # Get system audio monitor
                monitor_cmd = "pactl list sources | grep -A 2 'Monitor of'"
                monitor_result = subprocess.run(
                    monitor_cmd, shell=True, capture_output=True, text=True, timeout=5
                )
                if monitor_result.returncode == 0:
                    for line in monitor_result.stdout.splitlines():
                        if 'Name:' in line:
                            sources['monitor'] = line.split('Name: ')[-1].strip()
                            break

                # Verify sources exist
                list_result = subprocess.run(
                    ["pactl", "list", "sources"],
                    capture_output=True, text=True, timeout=5
                )
                if list_result.returncode == 0:
                    available_sources = list_result.stdout.lower()
                    if sources['monitor'] not in available_sources:
                        sources['monitor'] = 'default'
                    if sources['mic'] not in available_sources:
                        sources['mic'] = 'default'

                    pulse_working = True
                    self._log_message("✅ PulseAudio sources detected successfully")
            else:
                raise Exception("PulseAudio server not responding")

        except Exception as e:
            self._log_message(f"⚠️ PulseAudio failed: {e}, trying ALSA fallback", 'warning')

        # If PulseAudio failed, try ALSA fallback
        if not pulse_working:
            try:
                # Check if ALSA devices are available
                alsa_result = subprocess.run(
                    ["arecord", "-l"],
                    capture_output=True, text=True, timeout=5
                )
                if alsa_result.returncode == 0 and "card" in alsa_result.stdout:
                    sources['use_alsa'] = True
                    sources['alsa_device'] = 'hw:0,0'  # Default hardware device
                    self._log_message("✅ ALSA audio device detected, using hardware fallback")
                else:
                    self._log_message("❌ No audio devices available", 'error')
            except Exception as alsa_e:
                self._log_message(f"❌ ALSA fallback also failed: {alsa_e}", 'error')

        return sources

    def start(self):
        try:
            self._log_message("🎥 Starting recording process...")
            
            # Ensure output directory exists
            os.makedirs(os.path.dirname(self.out_path), exist_ok=True)
            
            self.proc = subprocess.Popen(
                self.cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            
            # Check if process started successfully
            if self.proc.poll() is None:
                logger.info("Recording process started successfully")
                print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] ✅ Recording started successfully")
                return True
            else:
                logger.error("Failed to start recording process")
                print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] ❌ Failed to start recording")
                return False
                
        except Exception as e:
            logger.error(f"Error starting recording: {e}")
            print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] ❌ Error starting recording: {str(e)}")
            return False

    def stop(self):
        if not self.proc:
            return None
            
        try:
            self._log_message("🛑 Stopping recording...")
            
            if self.is_linux:
                # Graceful shutdown for Linux
                self.proc.terminate()
                try:
                    self.proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self._log_message("⚠️ Force stopping FFmpeg process...")
                    # Send SIGTERM then SIGKILL if needed
                    self.proc.kill()
                    self.proc.wait(timeout=2)
            else:
                self.proc.terminate()
                self.proc.wait(timeout=5)
            
            # Verify recording
            if os.path.exists(self.out_path):
                file_size = os.path.getsize(self.out_path)
                if file_size > 0:
                    duration = self._get_video_duration()
                    status_msg = (f"✅ Recording saved: {os.path.basename(self.out_path)}\n"
                                f"   📊 Size: {file_size/1024/1024:.1f} MB, Duration: {duration:.1f} seconds")
                    self._log_message(status_msg)
                    return self.out_path
                else:
                    self._log_message("❌ Recording file is empty", 'error')
            else:
                self._log_message("❌ Recording file not found", 'error')
            
            return None
            
        except Exception as e:
            self._log_message(f"❌ Error stopping recording: {str(e)}", 'error')
            return None
        finally:
            self.proc = None
            # Cleanup Linux logging
            if self.is_linux and hasattr(self, 'log_handler'):
                logger.removeHandler(self.log_handler)
                self.log_handler.close()

    def _get_video_duration(self):
        """Get duration of recorded video in seconds"""
        try:
            if not os.path.exists(self.out_path):
                return 0
                
            cmd = [
                'ffprobe',
                '-v', 'error',
                '-show_entries', 'format=duration',
                '-of', 'default=noprint_wrappers=1:nokey=1',
                self.out_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0 and result.stdout.strip():
                return float(result.stdout.strip())
            return 0
            
        except Exception as e:
            logger.error(f"Error getting video duration: {e}")
            return 0

    def is_active(self):
        """Check if recording is active"""
        if not self.proc:
            return False

        poll_result = self.proc.poll()
        is_running = poll_result is None

        # Log if process has terminated unexpectedly
        if not is_running and hasattr(self, '_was_active') and self._was_active:
            self._log_message(f"⚠️ FFmpeg process terminated unexpectedly with exit code: {poll_result}", 'warning')
            self._was_active = False
        elif is_running and not hasattr(self, '_was_active'):
            self._was_active = True

        return is_running
