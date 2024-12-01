import streamlit as st
import requests
import tempfile
import os
import subprocess
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
                # Check if ffmpeg is available
                subprocess.run(['ffmpeg', '-version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

                # Extract audio using FFmpeg
                subprocess.run(['ffmpeg', '-i', video_path, '-q:a', '0', '-map', 'a', audio_path], check=True)

                # Transcribe audio using Whisper
                model = whisper.load_model("base")
                result = model.transcribe(audio_path)

                # Save transcription to a file
                transcription = result["text"]
                with open(transcription_file_path, "w") as file:
                    file.write(transcription)

                st.success("Audio extracted and transcribed successfully!")
                st.session_state["transcription"] = transcription

            except Exception as e:
                st.error(f"Error during audio extraction or transcription: {e}")

    # Step 3: Edit Transcript and Generate Edited Audio
    if "transcription" in st.session_state:
        transcription = st.session_state["transcription"]
        edited_transcript = st.text_area("Edit the Transcript Here", transcription, key="unique_edit_transcript")

        if st.button("Generate Edited Audio"):
            with st.spinner('Generating new audio...'):
                try:
                    # Generate audio from edited transcript using gTTS
                    tts = gTTS(text=edited_transcript, lang='en')
                    raw_audio_path = "raw_edited_audio.mp3"
                    tts.save(raw_audio_path)

                    # Convert to WAV format
                    edited_audio_path = "edited_audio.wav"
                    subprocess.run(['ffmpeg', '-y', '-i', raw_audio_path, '-ar', '16000', '-ac', '1', edited_audio_path], check=True)

                    st.success("Edited audio generated successfully!")
                    st.audio(edited_audio_path)

                except Exception as e:
                    st.error(f"Failed to generate or convert audio: {e}")

    # Step 4: Generate Lip-Synced Video
    if os.path.exists("edited_audio.wav") and os.path.exists(video_path):
        if st.button("Generate Lip-Synced Video"):
            with st.spinner('Generating lip-synced video...'):
                try:
                    # Replace with your Sieve API key
                    SIEVE_API_KEY = "cfYLVK8HOLOAS-riACFSa37EAdXFBlstd7CA_I3SYSw"
                    headers = {"Authorization": f"Bearer {SIEVE_API_KEY}"}

                    # Upload files to Sieve API
                    video_upload = requests.post(
                        "https://mango.sievedata.com/upload",
                        headers=headers,
                        files={"file": open(video_path, "rb")}
                    )

                    audio_upload = requests.post(
                        "https://mango.sievedata.com/upload",
                        headers=headers,
                        files={"file": open("edited_audio.wav", "rb")}
                    )

                    # Debugging: Log response status codes and errors
                    if video_upload.status_code != 200:
                        st.error(f"Video upload failed: {video_upload.text}")
                        return
                    if audio_upload.status_code != 200:
                        st.error(f"Audio upload failed: {audio_upload.text}")
                        return

                    video_url = video_upload.json().get("url")
                    audio_url = audio_upload.json().get("url")

                    if not video_url or not audio_url:
                        st.error("Failed to retrieve uploaded file URLs.")
                        return

                    # Trigger lip-sync processing
                    response = requests.post(
                        "https://mango.sievedata.com/lipsync",
                        headers=headers,
                        json={"video_url": video_url, "audio_url": audio_url}
                    )

                    if response.status_code == 200:
                        output_url = response.json().get("output_url")
                        if output_url:
                            st.success("Lip-synced video generated successfully!")
                            st.video(output_url)
                        else:
                            st.error("Lip-sync processing failed: No output URL provided.")
                    else:
                        st.error(f"Failed to generate lip-synced video: {response.text}")

                except requests.exceptions.RequestException as e:
                    st.error(f"Network error: {e}")
                except Exception as e:
                    st.error(f"Error during lip-syncing: {e}")


