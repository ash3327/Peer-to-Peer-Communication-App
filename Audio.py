from pydub import AudioSegment
import os

from chat_client import CHANNELS, RATE

sample_width = 2 #pyaudio.paInt16
ROOT_PATH = 'recordings'

def output_audio(recordings, room_name):
    base_path = os.path.join(ROOT_PATH, room_name)
    os.makedirs(base_path, exist_ok=True)
    path = os.path.join(base_path, 'recording.mp3')
    recordings.export(path, format="mp3")

