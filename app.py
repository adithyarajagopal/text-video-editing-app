
import streamlit as st
import requests
import tempfile
import os
from gtts import gTTS
import subprocess
from pyngrok import ngrok

# Step 1: Title and Video Upload
st.title("Text-Based Video Editing Tool")

# Upload a video file
uploaded_video = st.file_uploader("Upload a Video File", type=["mp4", "mov", "avi"], key="unique_video_upload")

if uploaded_video is not None:
    # Save the uploaded video to a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_video:
        temp_video.write(uploaded_video.read())
        video_path = temp_video.name

    # Display success and video
    st.success("Video uploaded successfully!")
    st.video(uploaded_video)

    # Assuming we already have the transcription from Whisper step
    # Read the transcription from the generated file (assuming you saved it in a text file)
    transcription_file_path = "/content/transcription.txt"
    try:
        with open(transcription_file_path, "r") as file:
            transcription = file.read().strip()
    except FileNotFoundError:
        transcription = "Transcription file not found. Please run the transcription step again."

    # Display transcription and allow editing
    edited_transcript = st.text_area("Edit the Transcript Here", transcription, key="unique_edit_transcript")

    # Step to generate new audio from the edited transcript
    if st.button("Generate Edited Audio", key="unique_generate_audio"):
        with st.spinner('Generating new audio...'):
            try:
                # Use gTTS to generate the audio from the edited transcript
                tts = gTTS(text=edited_transcript, lang='en')
                raw_audio_path = "raw_edited_audio.mp3"
                tts.save(raw_audio_path)

                # Check if the MP3 file was generated
                if os.path.exists(raw_audio_path):
                    st.success("MP3 audio generated successfully!")

                    # Convert the generated audio to WAV format with proper metadata using FFmpeg
                    edited_audio_path = "edited_audio.wav"
                    try:
                        result = subprocess.run(['ffmpeg', '-y', '-i', raw_audio_path, '-ar', '16000', '-ac', '1', edited_audio_path], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                        st.success("Audio converted successfully to WAV format!")
                        
                        # Display an audio player to play the generated audio
                        st.audio(edited_audio_path)

                    except subprocess.CalledProcessError as e:
                        st.error(f"Failed to convert audio to WAV format. FFmpeg error: {e.stderr.decode('utf-8')}")
                else:
                    st.error("MP3 audio file was not generated successfully.")

            except Exception as e:
                st.error(f"Failed to generate or convert audio: {e}")

    # Step 6: Generate Lip-Synced Video Using SyncLabs API
    if os.path.exists("edited_audio.wav") and os.path.exists(video_path):
        if st.button("Generate Lip-Synced Video", key="unique_generate_lipsync"):
            with st.spinner('Generating new lip-synced video...'):
                try:
                    # Set up ngrok tunnel to access files from SyncLabs API
                    public_url = ngrok.connect(port='8000')
                    ngrok_url = public_url.public_url
                    st.success(f"Ngrok URL: {ngrok_url}")

                    # Upload the video and audio to the public path using ngrok URL
                    video_filename = os.path.basename(video_path)
                    audio_filename = "edited_audio.wav"

                    video_url = f"{ngrok_url}/{video_filename}"
                    audio_url = f"{ngrok_url}/{audio_filename}"

                    # Set the SyncLabs API endpoint and headers
                    sync_api_url = "https://api.sync.so/v2/generate"
                    headers = {
                        "Content-Type": "application/json",
                        "x-api-key": "sk-wZBsgKSiQmGkJGWk7EfqMw.-ZbCnuLErRRFPcQFJjNpxGnOifBa0thm"  # Your SyncLabs API key here
                    }

                    # Payload for SyncLabs API
                    payload = {
                        "model": "lipsync-1.7.1",
                        "input": [
                            {"type": "video", "url": video_url},
                            {"type": "audio", "url": audio_url}
                        ],
                        "options": {"output_format": "mp4"}
                    }

                    # Send request to SyncLabs API
                    response = requests.post(sync_api_url, headers=headers, json=payload)

                    # Handle API response
                    if response.status_code == 201:
                        result = response.json()
                        output_url = result.get("outputUrl")
                        st.success("Lip-synced video generated successfully!")
                        st.video(output_url)
                    else:
                        st.error(f"Failed to create lip-sync job: {response.json()}")

                except Exception as e:
                    st.error(f"Failed to generate lip-synced video: {e}")

