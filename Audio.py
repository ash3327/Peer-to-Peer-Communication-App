from pydub import AudioSegment
import os
from datetime import datetime

from chat_client import CHANNELS, RATE

sample_width = 2 #pyaudio.paInt16
ROOT_PATH = 'recordings'

def output_audio(recordings:AudioSegment, room_name):
    base_path = os.path.join(ROOT_PATH, room_name)
    os.makedirs(base_path, exist_ok=True)
    
    # Get current date and time up to seconds
    current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    
    # Modify the file name to include date and time
    file_name = f"recording_{current_time}.mp3"
    
    path = os.path.join(base_path, file_name)
    print(path)
    recordings.export(path, format="mp3")