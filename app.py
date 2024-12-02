import streamlit as st
import requests
import tempfile
import os
import subprocess
from gtts import gTTS
import whisper
import base64
import sieve  # Import the sieve library

# Step 1: Title and Video Upload
st.title("Text-Based Video Editing Tool")

# Upload a video file
uploaded_video = st.file_uploader("Upload a Video File", type=["mp4", "mov", "avi"], key="unique_video_upload")

if uploaded_video is not None:
    try:
        # Save the uploaded video to a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_video:
            temp_video.write(uploaded_video.read())
            video_path = temp_video.name
        st.success("Video uploaded successfully!")
        st.video(uploaded_video)
    except Exception as e:
        st.error(f"Error saving video file: {e}")
        st.stop()

    # Step 2: Extract Audio and Transcribe
    audio_path = "extracted_audio.wav"
    processed_audio_path = "processed_audio.wav"
    transcription_file_path = "transcription.txt"

    if st.button("Extract and Transcribe Audio"):
        with st.spinner('Processing audio...'):
            try:
                st.info("Extracting audio from video...")
                subprocess.run(['ffmpeg', '-i', video_path, '-q:a', '0', '-map', 'a', audio_path], check=True)
                st.info("Audio extracted successfully.")

                st.info("Converting audio to required format...")
                subprocess.run(['ffmpeg', '-i', audio_path, '-ar', '16000', '-ac', '1', processed_audio_path], check=True)
                st.info("Audio conversion completed.")

                st.info("Transcribing audio with Whisper...")
                model = whisper.load_model("base")
                result = model.transcribe(processed_audio_path)
                transcription = result["text"]

                with open(transcription_file_path, "w") as file:
                    file.write(transcription)
                st.success("Audio extracted, processed, and transcribed successfully!")
                st.session_state["transcription"] = transcription
            except Exception as e:
                st.error(f"Error during audio processing or transcription: {e}")

    # Step 3: Edit Transcript and Generate Edited Audio
    if "transcription" in st.session_state:
        transcription = st.session_state["transcription"]
        edited_transcript = st.text_area("Edit the Transcript Here", transcription, key="unique_edit_transcript")

        if st.button("Generate Edited Audio"):
            with st.spinner('Generating new audio...'):
                try:
                    st.info("Generating audio with gTTS...")
                    tts = gTTS(text=edited_transcript, lang='en')
                    raw_audio_path = "raw_edited_audio.mp3"
                    tts.save(raw_audio_path)

                    st.info("Converting generated audio to WAV format...")
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
                    # Set your Sieve API key
                    sieve.api_key = "cfYLVK8HOLOAS-riACFSa37EAdXFBlstd7CA_I3SYSw"  # Replace with your actual API key

                    # Provide paths to the video and audio files
                    video_file = sieve.File(path=video_path)
                    audio_file = sieve.File(path="edited_audio.wav")

                    # Lip-sync job configuration
                    enhance = "default"
                    backend = "sievesync"
                    downsample = False
                    cut_by = "audio"

                    st.info("Processing lip-sync using Sieve API...")

                    # Get the lip-sync function
                    lipsync = sieve.function.get("sieve/lipsync")

                    # Run the lip-sync function
                    output = lipsync.run(video_file, audio_file, enhance, backend, downsample, cut_by)

                    # Get the output video URL
                    output_url = output.get("path")

                    if output_url:
                        st.success("Lip-synced video generated successfully!")
                        st.video(output_url)
                    else:
                        st.error("Lip-sync processing failed: Output video URL not found.")
                except Exception as e:
                    st.error(f"Error during lip-syncing: {e}")

