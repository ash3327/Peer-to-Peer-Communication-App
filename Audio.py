from pydub import AudioSegment
import os

CHANNELS = 1
RATE = 22050
sample_width = 2 #pyaudio.paInt16
ROOT_PATH = 'recordings'

def output_audio(recordings, room_name):
    list_audio = []

    for clients in recordings[room_name]:
        list_audio.append(recordings[room_name][clients])
    
    for audio in list_audio:
        segment = AudioSegment(
            data=audio,
            sample_width=sample_width,
            frame_rate=RATE,
            channels=CHANNELS
        )
        mixed_audio = mixed_audio.overlay(segment)
    
    base_path = os.path.join(ROOT_PATH, room_name)
    os.makedirs(base_path, exist_ok=True)
    path = os.path.join(base_path, 'recording.mp3')
    mixed_audio.export(path, format="mp3")

