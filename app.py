import streamlit as st
import requests
import tempfile
import os
import subprocess
import base64
from gtts import gTTS
import whisper

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

    # Step 2: Extract Audio and Transcribe
    audio_path = "extracted_audio.wav"
    transcription_file_path = "transcription.txt"

    if st.button("Extract and Transcribe Audio"):
        with st.spinner('Processing audio...'):
            try:
                subprocess.run(['ffmpeg', '-i', video_path, '-q:a', '0', '-map', 'a', audio_path], check=True)
                model = whisper.load_model("base")
                result = model.transcribe(audio_path)
                transcription = result["text"]
                with open(transcription_file_path, "w") as file:
                    file.write(transcription)
                st.success("Audio extracted and transcribed successfully!")
                st.session_state["transcription"] = transcription
            except Exception as e:
                st.error(f"Error: {e}")

    # Step 3: Edit Transcript and Generate Edited Audio
    if "transcription" in st.session_state:
        transcription = st.session_state["transcription"]
        edited_transcript = st.text_area("Edit the Transcript Here", transcription)

        if st.button("Generate Edited Audio"):
            with st.spinner('Generating new audio...'):
                try:
                    tts = gTTS(text=edited_transcript, lang='en')
                    raw_audio_path = "raw_edited_audio.mp3"
                    tts.save(raw_audio_path)
                    edited_audio_path = "edited_audio.wav"
                    subprocess.run(['ffmpeg', '-i', raw_audio_path, '-ar', '16000', '-ac', '1', edited_audio_path], check=True)
                    st.success("Edited audio generated successfully!")
                    st.audio(edited_audio_path)
                except Exception as e:
                    st.error(f"Error: {e}")

    # Step 4: Generate Lip-Synced Video
    if os.path.exists("edited_audio.wav") and os.path.exists(video_path):
        if st.button("Generate Lip-Synced Video"):
            with st.spinner('Generating lip-synced video...'):
                try:
                    SIEVE_API_KEY = "YOUR_API_KEY"
                    headers = {"Authorization": f"Bearer {SIEVE_API_KEY}", "Content-Type": "application/json"}
                    
                    # Encode files as base64
                    with open(video_path, "rb") as video_file:
                        video_content = base64.b64encode(video_file.read()).decode('utf-8')
                    with open("edited_audio.wav", "rb") as audio_file:
                        audio_content = base64.b64encode(audio_file.read()).decode('utf-8')

                    # Prepare payload
                    payload = {
                        "video": {"filename": os.path.basename(video_path), "content": video_content},
                        "audio": {"filename": "edited_audio.wav", "content": audio_content}
                    }

                    # Send request
                    response = requests.post(
                        "https://mango.sievedata.com/lipsync",
                        headers=headers,
                        json=payload
                    )

                    if response.status_code == 200:
                        output_url = response.json().get("output_url")
                        if output_url:
                            st.success("Lip-synced video generated successfully!")
                            st.video(output_url)
                        else:
                            st.error("Lip-sync failed: No output URL provided.")
                    else:
                        st.error(f"Error {response.status_code}: {response.text}")

                except Exception as e:
                    st.error(f"Error: {e}")
