# retico-videoPlayback

A retico module for using a video file as a video stream source.

## Overview

The `retico-videoPlayback` module provides functionality to use a video file as a video stream source, allowing for reproducible experiments and testing of other modules that require a video stream input.

## Installation

### Step 1: Install the package

```bash
pip install git+https://github.com/retico-team/retico-videoPlayback.git
```

### Step 2: Install retico-vision dependency
Since this module depends on `retico-vision`, you need to install it and add it to your Python path:
```bash
git clone https://github.com/retico-team/retico-vision.git
```
**Important**: Make sure to add the path to the `retico-vision` library to your `PYTHONPATH` environment variable. This is required for the module to properly import the vision components.

## Usage
This module can be used as a drop-in substitute for the `WebcamModule` in the ReTiCo framework. You just need to populate the `video_path` parameter with the path to the video file you want to use as a stream source during the instantiation of the `VideoPlaybackModule`.

```python
from retico_core import *
from retico_videoPlayback.player import VideoPlaybackModule

video_path = "path/to/your/video.mp4"
video_player = VideoPlaybackModule(video_path=video_path)
```

## Project Structure

```
retico-screen/
├── retico_screen/
│   ├── __init__.py
│   ├── player.py               # video playback module
│   └── version.py              # Version information
├── setup.py                    # Package setup
├── example.py                  # Example usage script
├── README.md                   # This file
└── LICENSE                     # License file
```

## Related Projects

- [ReTiCo Core](https://github.com/retico-team/retico-core) - The core ReTiCo framework
- [ReTiCo Vision](https://github.com/retico-team/retico-vision) - Vision components for ReTiCo
