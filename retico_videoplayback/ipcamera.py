import cv2
import numpy as np
from PIL import Image
import threading
import time
import requests
from urllib.parse import urlparse
import retico_core

from retico_vision import ImageIU


class IPCameraModule(retico_core.AbstractProducingModule):
    """A module that produces IUs containing images from an IP camera feed.
    
    Supports various IP camera protocols including:
    - HTTP/HTTPS streams (MJPEG)
    - RTSP streams
    - Direct IP camera URLs
    """

    @staticmethod
    def name():
        return "IP Camera Module"

    @staticmethod
    def description():
        return "A producing module that captures images from IP camera feeds."

    @staticmethod
    def output_iu():
        return ImageIU

    def __init__(self, 
                 camera_url=None, 
                 username=None, 
                 password=None,
                 width=None, 
                 height=None, 
                 rate=30,
                 pil=True,
                 timeout=10,
                 retry_attempts=3,
                 retry_delay=5,
                 **kwargs):
        """
        Initialize the IP Camera Module.
        
        Args:
            camera_url (str): URL of the IP camera feed (e.g., "http://192.168.1.100:8080/video")
            username (str): Username for camera authentication (optional)
            password (str): Password for camera authentication (optional)
            width (int): Desired width of captured frames (optional)
            height (int): Desired height of captured frames (optional)
            rate (int): Frame rate for capture (default: 30)
            pil (bool): Whether to convert frames to PIL Image format (default: True)
            timeout (int): Connection timeout in seconds (default: 10)
            retry_attempts (int): Number of retry attempts on connection failure (default: 3)
            retry_delay (int): Delay between retry attempts in seconds (default: 5)
        """
        super().__init__(**kwargs)
        
        self.camera_url = camera_url
        self.username = username
        self.password = password
        self.width = width
        self.height = height
        self.rate = rate
        self.timeout = timeout
        self.retry_attempts = retry_attempts
        self.retry_delay = retry_delay
        self.pil = pil
        
        self.cap = None
        self.is_connected = False
        self.connection_thread = None
        self.should_stop = False
        
        if not self.camera_url:
            raise ValueError("camera_url must be provided")
            
        self.setup()

    def setup(self):
        """Set up the IP camera connection."""
        self._connect_to_camera()

    def _connect_to_camera(self):
        """Establish connection to the IP camera with retry logic."""
        for attempt in range(self.retry_attempts):
            try:
                print(f"Attempting to connect to IP camera: {self.camera_url} (attempt {attempt + 1}/{self.retry_attempts})")
                
                # Create capture object with appropriate settings
                if self.username and self.password:
                    # For authenticated streams, modify URL to include credentials
                    parsed_url = urlparse(self.camera_url)
                    auth_url = f"{parsed_url.scheme}://{self.username}:{self.password}@{parsed_url.netloc}{parsed_url.path}"
                    if parsed_url.query:
                        auth_url += f"?{parsed_url.query}"
                    self.cap = cv2.VideoCapture(auth_url)
                else:
                    self.cap = cv2.VideoCapture(self.camera_url)
                
                # Set capture properties
                if self.cap is not None:
                    self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Reduce buffer to minimize latency
                    
                    if self.width:
                        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
                    if self.height:
                        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
                    if self.rate:
                        self.cap.set(cv2.CAP_PROP_FPS, self.rate)
                
                # Test connection by reading a frame
                ret, frame = self.cap.read()
                if ret and frame is not None:
                    self.is_connected = True
                    print("Successfully connected to IP camera")
                    
                    # Get actual frame properties
                    self.actual_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                    self.actual_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                    self.actual_fps = self.cap.get(cv2.CAP_PROP_FPS)
                    
                    print(f"Camera properties - Width: {self.actual_width}, Height: {self.actual_height}, FPS: {self.actual_fps}")
                    return True
                else:
                    print("Failed to read frame from camera")
                    if self.cap:
                        self.cap.release()
                        self.cap = None
                        
            except Exception as e:
                print(f"Connection attempt {attempt + 1} failed: {str(e)}")
                if self.cap:
                    self.cap.release()
                    self.cap = None
            
            if attempt < self.retry_attempts - 1:
                print(f"Retrying in {self.retry_delay} seconds...")
                time.sleep(self.retry_delay)
        
        print("Failed to connect to IP camera after all retry attempts")
        self.is_connected = False
        return False

    def process_update(self, _):
        """Process update to capture and return a frame from the IP camera."""
        if not self.should_stop and (not self.is_connected or not self.cap):
            self._connect_to_camera()
            return None
            
        try:
            ret, frame = self.cap.read()
            
            if ret:
                output_iu = self.create_iu()
                
                if self.pil:
                    # Convert BGR to RGB for PIL
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    frame = Image.fromarray(frame)
                
                output_iu.set_image(frame, 1, self.rate)
                return retico_core.UpdateMessage.from_iu(output_iu, retico_core.UpdateType.ADD)
            else:
                print("Failed to read frame from IP camera")
                self.is_connected = False
                
        except Exception as e:
            print(f"Error reading from IP camera: {str(e)}")
            self.is_connected = False

    def shutdown(self):
        """Close the IP camera connection."""
        self.should_stop = True
        if self.cap:
            self.cap.release()
            self.cap = None
        self.is_connected = False
        print("IP camera connection closed")
