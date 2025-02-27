import json
from math import log2
from pathlib import Path

import aubio
import noisereduce as nr
import numpy as np
from moviepy.editor import VideoFileClip
from pydub import AudioSegment
from pydub.generators import Sine

MEDIA_PATH = Path(__file__).parent.parent.parent / "media"
SOUNDS_PATH = MEDIA_PATH / "sounds"

NOTES_FREQ = {
    "A": 440,
    "B": 494,
    "C": 523,
    "D": 587,
    "E": 659,
    "F": 698,
    "G": 784,
    "C0": 16.35,
    "C#0": 17.32,
    "D0": 18.35,
    "D#0": 19.45,
    "E0": 20.60,
    "F0": 21.83,
    "F#0": 23.12,
    "G0": 24.50,
    "G#0": 25.96,
    "A0": 27.50,
    "A#0": 29.14,
    "B0": 30.87,
    "C1": 32.70,
    "C#1": 34.65,
    "D1": 36.71,
    "D#1": 38.89,
    "E1": 41.20,
    "F1": 43.65,
    "F#1": 46.25,
    "G1": 49.00,
    "G#1": 51.91,
    "A1": 55.00,
    "A#1": 58.27,
    "B1": 61.74,
    "C2": 65.41,
    "C#2": 69.30,
    "D2": 73.42,
    "D#2": 77.78,
    "E2": 82.41,
    "F2": 87.31,
    "F#2": 92.50,
    "G2": 98.00,
    "G#2": 103.83,
    "A2": 110.00,
    "A#2": 116.54,
    "B2": 123.47,
    "C3": 130.81,
    "C#3": 138.59,
    "D3": 146.83,
    "D#3": 155.56,
    "E3": 164.81,
    "F3": 174.61,
    "F#3": 185.00,
    "G3": 196.00,
    "G#3": 207.65,
    "A3": 220.00,
    "A#3": 233.08,
    "B3": 246.94,
    "C4": 261.63,
    "C#4": 277.18,
    "D4": 293.66,
    "D#4": 311.13,
    "E4": 329.63,
    "F4": 349.23,
    "F#4": 369.99,
    "G4": 392.00,
    "G#4": 415.30,
    "A4": 440.00,
    "A#4": 466.16,
    "B4": 493.88,
    "C5": 523.25,
    "C#5": 554.37,
    "D5": 587.33,
    "D#5": 622.25,
    "E5": 659.26,
    "F5": 698.46,
    "F#5": 739.99,
    "G5": 783.99,
    "G#5": 830.61,
    "A5": 880.00,
    "A#5": 932.33,
    "B5": 987.77,
    "C6": 1046.50,
    "C#6": 1108.73,
    "D6": 1174.66,
    "D#6": 1244.51,
    "E6": 1318.51,
    "F6": 1396.91,
    "F#6": 1479.98,
    "G6": 1567.98,
    "G#6": 1661.22,
    "A6": 1760.00,
    "A#6": 1864.66,
    "B6": 1975.53,
    "C7": 2093.00,
    "C#7": 2217.46,
    "D7": 2349.32,
    "D#7": 2489.02,
    "E7": 2637.02,
    "F7": 2793.83,
    "F#7": 2959.96,
    "G7": 3135.96,
    "G#7": 3322.44,
    "A7": 3520.00,
    "A#7": 3729.31,
    "B7": 3951.07,
    "C8": 4186.01,
}


def fix_notes(notes: list[str]) -> list[str]:
    fixed_notes = []

    for n in notes:
        while n:
            if n in NOTES_FREQ:
                fixed_notes.append(n)
                break
            n = n[:-1]

    return fixed_notes


def generate_melody(notes_path: str, total_duration: float):
    """
    Generate a simple melody using sine waves.

    Returns
    -------
    pydub.AudioSegment
        The generated melody.
    """
    melody = AudioSegment.silent(0)

    notes = NOTES_FREQ

    # Define a simple sequence
    with open(notes_path, "r") as f:
        background_music_sequence = fix_notes(json.load(f))

    note_duration = round(
        (total_duration / len(background_music_sequence)) * 1000
    )
    # Generate melody
    for note in background_music_sequence:
        tone = Sine(notes[note]).to_audio_segment(duration=note_duration)
        melody += tone

    melody.export(str(SOUNDS_PATH / "melody.mp3"), format="mp3")


def convert_to_8bit_audio(video_path: str, output_path: str) -> None:
    """
    Extract audio from an MP4 file and convert it to a 16-bit.

    The result audio would be similar to the sound used by SNES and
    Sega Genesis.

    Parameters
    ----------
    video_path : str
        Path to the input video file (MP4).
    output_path : str
        Path to save the converted audio (WAV).
    """
    # Load the video file
    video_clip = VideoFileClip(video_path)

    # Get audio as numpy array (stereo)
    audio_array = video_clip.audio.to_soundarray(
        fps=22050
    )  # Downsample to 22050 Hz

    # Convert to mono by averaging the two channels
    audio_mono = audio_array.mean(axis=1)

    # Reduce noise
    audio_denoised = nr.reduce_noise(y=audio_mono, sr=22050)

    # Convert to 8-bit PCM format
    audio_8bit = ((audio_denoised + 1) * 127.5).astype("uint8")

    # Create an AudioSegment from the 8-bit array
    audio_segment = AudioSegment(
        audio_8bit.tobytes(),
        frame_rate=22050,
        sample_width=1,  # 1 byte = 8 bits
        channels=1,
    )

    # Export as WAV file
    audio_segment.export(output_path, format="mp3")

    # Close the video clip
    video_clip.reader.close()

    print(
        "Audio has been extracted and converted to 8-bit format "
        f"with noise reduction. Output saved at '{output_path}'."
    )


def extract_audio(video_path: str, output_path: str) -> None:
    """
    Extract audio from an MP4 file.

    Parameters
    ----------
    video_path : str
        Path to the input video file (MP4).
    output_path : str
        Path to save the extracted audio (WAV).
    """
    video_clip = VideoFileClip(video_path)
    audio_clip = video_clip.audio
    audio_clip.write_audiofile(output_path)
    audio_clip.close()
    video_clip.reader.close()

    print(f"Audio has been extracted. Output saved at '{output_path}'.")


def frequency_to_note(frequency: float) -> str:
    """
    Convert a frequency in Hz to a musical note.

    Parameters
    ----------
    frequency : float
        Frequency in Hz.

    Returns
    -------
    str
        Corresponding musical note (e.g., "A4", "C#5").
    """
    notes = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    octave = int(frequency / 130.81)  # Based on C3 = 130.81 Hz
    n = int(round(12 * log2(frequency / 440.0)) + 49) % 12
    return f"{notes[n]}{octave}"


def extract_notes_from_mp3(mp3_path: str, output_notes: str) -> list:
    win_s = 2048  # Correct FFT size
    hop_s = win_s // 2  # Correct Hop size

    # Convert MP3 to WAV using pydub
    audio = AudioSegment.from_mp3(mp3_path)
    audio = audio.set_channels(1)  # Convert to mono
    samples = np.array(audio.get_array_of_samples())

    # Create pitch detection object
    pitch_o = aubio.pitch("default", win_s, hop_s, 44100)
    pitch_o.set_unit("Hz")

    notes = []
    for start in range(0, len(samples), hop_s):
        chunk = samples[start : start + hop_s]

        # Zero-pad the chunk if necessary
        if len(chunk) < hop_s:
            chunk = np.pad(
                chunk, (0, hop_s - len(chunk)), "constant", constant_values=0
            )

        chunk = chunk.astype("float32")
        frequency = pitch_o(chunk)[0]

        # Convert frequency to musical note and add to the list
        if frequency > 0:  # Ignore zero frequencies (silence)
            note = frequency_to_note(frequency)
            notes.append(note)

    with open(output_notes, "w") as f:
        json.dump(notes, f)

    return notes
