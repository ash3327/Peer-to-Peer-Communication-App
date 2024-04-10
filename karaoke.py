from pytube import YouTube
from moviepy.editor import *
from spleeter.separator import Separator
import os

import warnings
warnings.filterwarnings('ignore')

ROOT_PATH = "Karaoke"

def del_file(path):
    try:
         os.remove(path)
    except Exception:
        pass

def dn_ytvideo(youtube_url, room_name):
    try:
        base_path = os.path.join(ROOT_PATH, room_name, "video")
        os.makedirs(base_path, exist_ok=True)
        
        print("Downloading YouTube video ...")
        yt = YouTube(youtube_url)
        vid_name = yt.title
        for char in '\/:*?"<>|':
            vid_name = vid_name.replace(char, '')

        video = yt.streams.filter(progressive=True).first()
        out_file = video.download(output_path=base_path)
        print("Download successful")
    except Exception as e:
        print(f"An error occurred while downloading the video: {e}")
        return None
    
    return out_file

def extract_audio(video_path):
    print("Extracting audio ...")
    audio_clip = AudioFileClip(video_path)
    audio_path = os.path.dirname(video_path)
    audio_path = video_path.replace("video", "audio")
    audio_path = audio_path.replace(".mp4", ".mp3")
    os.makedirs(os.path.dirname(audio_path), exist_ok=True)
    audio_clip.write_audiofile(audio_path)
    audio_clip.close()
    print("Audio extracted")
    #del_file(video_path)
    return audio_path

def separate_vocals(audio_path, room_name):
    separator = Separator('spleeter:2stems')
    file_name = os.path.splitext(audio_path)[0]
    instrumental_dir = os.path.join(ROOT_PATH, room_name, 'extracted')
    os.makedirs(instrumental_dir, exist_ok=True)
    separator.separate_to_file(audio_path, instrumental_dir)

    return os.path.join(instrumental_dir, os.path.basename(file_name), 'accompaniment.wav')

def extract_music(audio_path, room_name):
    # reference: stackoverflow.com/questions/49279425/extract-human-vocals-from-song (question by ashish)
    # which adopts a cancelling technique.
    from pydub import AudioSegment
    from pydub.playback import play

    instrumental_dir = os.path.join(ROOT_PATH, room_name, 'extracted')
    os.makedirs(instrumental_dir, exist_ok=True)

    # read in audio file and get the two mono tracks
    sound_stereo = AudioSegment.from_file(audio_path, format='mp3')
    sound_l, sound_r = sound_stereo.split_to_mono()
    sound_centers_out:AudioSegment = sound_l.overlay(sound_r.invert_phase())

    stor_path = os.path.join(instrumental_dir, os.path.basename(audio_path))
    sound_centers_out.export(stor_path, format='mp3')
    return stor_path

def get_pure_music(youtube_url, room):
    vid_path = dn_ytvideo(youtube_url, room)
    audio_path = extract_audio(vid_path)
    print('Output to:', audio_path)
    # output_file = separate_vocals(audio_path, room)
    output_file = extract_music(audio_path, room)
    print('Result outputted in:', output_file)
    return output_file

if __name__ == '__main__':
    youtube_urls = [
        "https://www.youtube.com/watch?v=8xg3vE8Ie_E&list=RD8xg3vE8Ie_E&start_radio=1&rv=ptSjNWnzpjg",
        "https://www.youtube.com/watch?v=qzwsQTY-99o&ab_channel=%E5%91%A8%E6%9D%B0%E5%80%ABJayChou"
    ]
    for youtube_url in youtube_urls:
        get_pure_music(youtube_url=youtube_url, room='test')


    


