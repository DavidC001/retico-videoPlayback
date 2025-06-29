import cv2
import time
from PIL import Image
import retico_core
import os

from retico_vision.vision import ImageIU

class VideoPlaybackModule(retico_core.AbstractProducingModule):
    """A module that produces IUs containing images from a video file,
    simulating a webcam stream."""

    @staticmethod
    def name():
        return "Video Playback Module"

    @staticmethod
    def description():
        return "A producing module that plays back video files frame by frame."

    @staticmethod
    def output_iu():
        return ImageIU

    def __init__(self, video_path, fps=None, loop=True, **kwargs):
        """
        Initialize the Video Playback Module.
        
        Args:
            video_path (str): Path to the video file to play
            fps (float): Target frames per second for playback; uses video's original fps if None
            loop (bool): Whether to loop the video when it reaches the end
        """
        super().__init__(**kwargs)
        self.video_path = video_path
        self.fps = fps
        self.loop = loop
        self.cap = None
        self.total_frames = 0
        self.current_frame = 0
        self.video_fps = 0
        self.frame_delay = 0
        self.last_frame_time = 0
        self._setup_video()

    def _setup_video(self):
        """Set up the video capture and get video properties."""
        if not os.path.exists(self.video_path):
            raise FileNotFoundError(f"Video file not found: {self.video_path}")
        
        self.cap = cv2.VideoCapture(self.video_path)
        if not self.cap.isOpened():
            raise RuntimeError(f"Could not open video file: {self.video_path}")
        
        # Get video properties
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.video_fps = self.cap.get(cv2.CAP_PROP_FPS)
        
        # Set target fps
        if self.fps is None:
            self.fps = self.video_fps
        
        # Calculate frame delay for timing
        self.frame_delay = 1.0 / self.fps if self.fps > 0 else 0
        
        print(f"Video loaded: {self.video_path}")
        print(f"Total frames: {self.total_frames}, Original FPS: {self.video_fps}, Target FPS: {self.fps}")

    def process_update(self, _):
        """Process update to read and send the next video frame."""
        current_time = time.time()
        
        # Control frame rate timing
        if self.last_frame_time > 0:
            elapsed = current_time - self.last_frame_time
            if elapsed < self.frame_delay:
                time.sleep(self.frame_delay - elapsed)
        
        self.last_frame_time = time.time()
        
        ret, frame = self.cap.read()
        
        if not ret:
            if self.loop and self.total_frames > 0:
                # Reset to beginning of video
                self.restart_video()
                ret, frame = self.cap.read()
                if not ret:
                    print("Error: Could not read frame after reset")
                    return None
            else:
                print("End of video reached")
                return None
        
        self.current_frame += 1
        
        if ret:
            output_iu = self.create_iu()
            
            # Convert frame format if needed
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = Image.fromarray(frame)

            output_iu.set_image(frame, 1, self.fps)
            return retico_core.UpdateMessage.from_iu(output_iu, retico_core.UpdateType.ADD)
        
        return None

    def setup(self):
        """Set up the video playback module."""
        if self.cap is None or not self.cap.isOpened():
            self._setup_video()

    def shutdown(self):
        """Release the video capture."""
        if self.cap is not None:
            self.cap.release()
            self.cap = None

    def restart_video(self):
        """Restart the video from the beginning."""
        if self.cap is not None:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            self.current_frame = 0

    def seek_to_frame(self, frame_number):
        """Seek to a specific frame number."""
        if self.cap is not None and 0 <= frame_number < self.total_frames:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
            self.current_frame = frame_number

    def seek_to_time(self, time_seconds):
        """Seek to a specific time in seconds."""
        if self.cap is not None and self.video_fps > 0:
            frame_number = int(time_seconds * self.video_fps)
            self.seek_to_frame(frame_number)

    def get_video_info(self):
        """Get information about the current video."""
        if self.cap is not None:
            return {
                'path': self.video_path,
                'total_frames': self.total_frames,
                'current_frame': self.current_frame,
                'fps': self.video_fps,
                'target_fps': self.fps,
                'duration': self.total_frames / self.video_fps if self.video_fps > 0 else 0,
                'current_time': self.current_frame / self.video_fps if self.video_fps > 0 else 0
            }
        return None
