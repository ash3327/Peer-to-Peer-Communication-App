from pytube import YouTube
from moviepy.editor import *
from spleeter.separator import Separator
import os
import torch
import openunmix

ROOT_PATH = "Karaoke"

def del_file(path):
    try:
         os.remove(path)
    except Exception:
        pass

def dn_ytvideo(youtube_url, room_name):
    try:
        base_path = os.path.join(ROOT_PATH, room_name, "video")
        if not os.path.exists(base_path):
            os.makedirs(base_path)
        
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
    video_clip = VideoFileClip(video_path)
    audio_path = os.path.dirname(video_path)
    if not os.path.exists(audio_path):
        os.makedirs(audio_path)
    audio_path = video_path.replace("video", "audio")
    audio_path = audio_path.replace(".mp4", ".mp3")
    audio_clip = video_clip.audio
    audio_clip.write_audiofile(audio_path)
    audio_clip.close()
    video_clip.close()
    print("Audio extracted")
    #del_file(video_path)
    return audio_path

def separate_vocals(audio_path, room_name):
    separator = Separator('spleeter:2stems')
    file_name = os.path.splitext(audio_path)[0]
    instrumental_dir = os.path.join(ROOT_PATH, room_name)
    if not os.path.exists(instrumental_dir):
        os.makedirs(instrumental_dir)
    separator.separate_to_file(audio_path, instrumental_dir)
    '''
    spleeter_output_folder = os.path.join(instrumental_dir, file_name)
    output_folder = spleeter_output_folder.replace(file_name, 'instrumental')
    if os.path.exists(spleeter_output_folder):
        os.rename(spleeter_output_folder, output_folder)
        print("Directory renamed")
    else:
        print("Directory does not exist")

    original_instrumental_path = os.path.join(output_folder, 'accompaniment.wav')
    new_instrumental_path = original_instrumental_path.replace('accompaniment.wav', f"{file_name}.wav")

    if os.path.exists(original_instrumental_path):
        os.rename(original_instrumental_path, new_instrumental_path) '''

def remove_vocals(audio_path, room_name):
    model = openunmix.umxhq()
    mix = torch.load(audio_path)
    estimates = model(mix)
    accompaniment = estimates['accompaniment']
    accompaniment_path = os.path.join(ROOT_PATH, room_name, "audio.wav")
    torch.save(accompaniment, accompaniment_path)


#if __name__ == '__main__':
youtube_url = "https://www.youtube.com/watch?v=8xg3vE8Ie_E&list=RD8xg3vE8Ie_E&start_radio=1&rv=ptSjNWnzpjg"
room = "test"
vid_path = dn_ytvideo(youtube_url, room)
audio_path = extract_audio(vid_path)
print(audio_path)
remove_vocals(audio_path, room)


    


