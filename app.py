import streamlit as st
import requests
import tempfile
import os
import subprocess
import shutil
import base64
import sieve
from gtts import gTTS
import whisper  # Ensure the whisper library is installed

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
    processed_audio_path = "processed_audio.wav"
    transcription_file_path = "transcription.txt"

    if st.button("Extract and Transcribe Audio"):
        with st.spinner('Processing audio...'):
            try:
                # Extract audio using FFmpeg
                if not os.path.exists(video_path):
                    st.error("Video file not found.")
                    raise FileNotFoundError("Video file missing.")

                subprocess.run(['ffmpeg', '-i', video_path, '-q:a', '0', '-map', 'a', audio_path], check=True)

                # Convert extracted audio to desired format
                subprocess.run(['ffmpeg', '-i', audio_path, '-ar', '16000', '-ac', '1', processed_audio_path], check=True)

                # Transcribe audio using Whisper
                model = whisper.load_model("base")
                result = model.transcribe(processed_audio_path)

                # Save transcription to a file
                transcription = result["text"]
                with open(transcription_file_path, "w") as file:
                    file.write(transcription)

                st.success("Audio extracted, processed, and transcribed successfully!")
                st.session_state["transcription"] = transcription

            except FileNotFoundError as fnf_error:
                st.error(f"File error: {fnf_error}")
            except Exception as e:
                st.error(f"Error during audio processing or transcription: {e}")

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

                except FileNotFoundError as fnf_error:
                    st.error(f"File error: {fnf_error}")
                except Exception as e:
                    st.error(f"Failed to generate or convert audio: {e}")

    # Step 4: Generate Lip-Synced Video
    if os.path.exists("edited_audio.wav") and os.path.exists(video_path):
        if st.button("Generate Lip-Synced Video"):
            with st.spinner('Generating lip-synced video...'):
                try:
                    sieve.api_key = "cfYLVK8HOLOAS-riACFSa37EAdXFBlstd7CA_I3SYSw"

                    # Upload video and audio to Sieve
                    video_file = sieve.File(path=video_path)
                    audio_file = sieve.File(path="edited_audio.wav")

                    # Configure and run lip-sync function
                    lipsync = sieve.function.get("sieve/lipsync")
                    output = lipsync.run(video_file, audio_file, "default", "sievesync", False, "audio")

                    # Verify output and display the result
                    output_path = output.get("path")
                    if output_path:
                        shutil.copy(output_path, "lip_synced_output.mp4")
                        st.success("Lip-synced video generated successfully!")
                        st.video("lip_synced_output.mp4")
                    else:
                        st.error("Lip-sync processing failed. No output file.")

                except requests.exceptions.RequestException as req_error:
                    st.error(f"API request error: {req_error}")
                except Exception as e:
                    st.error(f"Error during lip-syncing: {e}")
