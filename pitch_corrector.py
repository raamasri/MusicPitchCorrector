#!/usr/bin/env python3
"""
Vinyl-Style Audio Pitch Corrector
A lossless pitch correction tool that changes both pitch and speed proportionally,
just like changing RPM on a vinyl record player.
"""

import os
import sys
import subprocess
import re
from pathlib import Path

def check_dependencies():
    """Check if all required dependencies are installed."""
    missing_deps = []
    
    # Check Python packages
    try:
        import librosa
        print("✓ librosa found")
    except ImportError:
        missing_deps.append("librosa>=0.10.0")
    
    try:
        import soundfile as sf
        print("✓ soundfile found")
    except ImportError:
        missing_deps.append("soundfile>=0.12.1")
    
    try:
        import numpy as np
        print("✓ numpy found")
    except ImportError:
        missing_deps.append("numpy>=1.24.0")
    
    try:
        import resampy
        print("✓ resampy found")
    except ImportError:
        missing_deps.append("resampy>=0.4.0")
    
    try:
        from tqdm import tqdm
        print("✓ tqdm found")
    except ImportError:
        missing_deps.append("tqdm>=4.64.0")
    
    # Check ffmpeg
    try:
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✓ ffmpeg found")
        else:
            print("⚠ ffmpeg not working properly")
    except FileNotFoundError:
        print("⚠ ffmpeg not found - MP3 output will fallback to WAV")
        print("  Install with: brew install ffmpeg (macOS) or apt install ffmpeg (Linux)")
    
    if missing_deps:
        print("\n❌ Missing required Python packages:")
        for dep in missing_deps:
            print(f"  - {dep}")
        print("\nTo install missing packages, run:")
        print(f"  pip install {' '.join(missing_deps)}")
        print("\nOr install from requirements.txt:")
        print("  pip install -r requirements.txt")
        return False
    
    print("\n✅ All dependencies are installed!")
    return True

# Import the packages after checking
try:
    import librosa
    import soundfile as sf
    import numpy as np
    from tqdm import tqdm
    import threading
    import time
except ImportError as e:
    print(f"Import error: {e}")
    print("Please install required packages first.")
    sys.exit(1)


def get_supported_formats():
    """Return supported audio file extensions."""
    return {
        '.wav', '.flac', '.aiff', '.aif', '.aifc', '.au', '.snd', 
        '.mp3', '.m4a', '.ogg', '.opus'
    }


def validate_audio_file(file_path):
    """Validate if the file exists and is a supported audio format."""
    if not os.path.exists(file_path):
        return False, "File does not exist."
    
    ext = Path(file_path).suffix.lower()
    if ext not in get_supported_formats():
        return False, f"Unsupported format: {ext}"
    
    return True, "Valid audio file."


def semitones_to_ratio(semitones):
    """Convert semitones to pitch ratio (2^(semitones/12))."""
    return 2.0 ** (semitones / 12.0)


def vinyl_pitch_shift(audio_data, sr, semitones):
    """
    Pitch shift audio like a vinyl record - both pitch AND speed change together.
    This is achieved by resampling the audio at a different rate then playing at original rate.
    """
    if semitones == 0:
        return audio_data
    
    # Calculate the speed ratio (how much faster/slower the vinyl spins)
    speed_ratio = semitones_to_ratio(semitones)
    
    # For true vinyl behavior: we need to resample the audio
    # If we want higher pitch, we slow down recording then play at normal speed
    # If we want lower pitch, we speed up recording then play at normal speed
    
    # Calculate target sample rate for resampling
    target_sr = int(sr / speed_ratio)
    
    # Resample to the target rate (this changes the data length)
    resampled_audio = librosa.resample(
        audio_data,
        orig_sr=sr,
        target_sr=target_sr,
        res_type='kaiser_best'
    )
    
    # Now when this resampled audio is played back at the original sample rate,
    # it will have the pitch shift we want
    return resampled_audio


def get_output_filename(input_path, semitones):
    """Generate output filename with vinyl-style adjustment info."""
    input_path = Path(input_path)
    name = input_path.stem
    ext = input_path.suffix
    
    # Format semitone value for filename
    if semitones >= 0:
        semitone_str = f"+{semitones:.2f}"
    else:
        semitone_str = f"{semitones:.2f}"
    
    output_name = f"{name}_vinyl{semitone_str}{ext}"
    return input_path.parent / output_name


def process_audio_file(input_path, semitones):
    """Process the audio file with vinyl-style pitch and speed adjustment."""
    print(f"Loading audio file: {input_path}")
    
    try:
        # Load audio with original sample rate
        audio_data, sample_rate = librosa.load(input_path, sr=None, mono=False)
        
        original_duration = len(audio_data) / sample_rate if len(audio_data.shape) == 1 else audio_data.shape[1] / sample_rate
        pitch_ratio = semitones_to_ratio(semitones)
        new_duration = original_duration / pitch_ratio
        
        print(f"Sample rate: {sample_rate} Hz")
        print(f"Shape: {audio_data.shape}")
        print(f"Original duration: {original_duration:.2f} seconds")
        print(f"Vinyl adjustment: {semitones:+.2f} semitones (pitch ratio: {pitch_ratio:.3f}x)")
        print(f"New duration: {new_duration:.2f} seconds ({new_duration/original_duration:.1%} of original)")
        
        # Handle mono and stereo files with progress bar
        print("Processing audio channels...")
        if len(audio_data.shape) == 1:
            # Mono file
            with tqdm(total=1, desc="Pitch shifting", unit="channel") as pbar:
                shifted_audio = vinyl_pitch_shift(audio_data, sample_rate, semitones)
                pbar.update(1)
        else:
            # Stereo/multi-channel file - process each channel
            shifted_channels = []
            with tqdm(total=audio_data.shape[0], desc="Pitch shifting", unit="channel") as pbar:
                for channel in range(audio_data.shape[0]):
                    shifted_channel = vinyl_pitch_shift(
                        audio_data[channel], sample_rate, semitones
                    )
                    shifted_channels.append(shifted_channel)
                    pbar.update(1)
            
            # Stack channels back together
            shifted_audio = np.stack(shifted_channels, axis=0)
        
        # Generate output filename and handle format compatibility
        input_ext = Path(input_path).suffix.lower()
        
        # Check if soundfile can handle the original format for writing
        try:
            with sf.SoundFile(input_path, 'r') as f:
                original_subtype = f.subtype
                original_format = f.format
                can_preserve_format = True
        except Exception:
            # If we can't read format info, fall back to WAV
            can_preserve_format = False
            original_subtype = 'PCM_24'
            original_format = 'WAV'
            
        # Handle different output formats
        if input_ext == '.mp3':
            # Keep MP3 format for universal compatibility
            output_path = get_output_filename(input_path, semitones)
            output_format = 'WAV'  # Temporary format for conversion
            output_subtype = 'PCM_16'  # 16-bit for smaller temp files
            will_convert_to_mp3 = True
            print(f"Note: Will convert to MP3 to match input format (may take time for large files)")
        elif input_ext in {'.m4a', '.opus'} or not can_preserve_format:
            # Use FLAC for other compressed formats
            output_path = get_output_filename(input_path, semitones)
            output_path = output_path.with_suffix('.flac')
            output_format = 'FLAC'
            output_subtype = 'PCM_24'
            will_convert_to_mp3 = False
            print(f"Note: Converting {input_ext} to FLAC for lossless compressed output")
        else:
            # Preserve original format for uncompressed formats
            output_path = get_output_filename(input_path, semitones)
            output_format = original_format
            output_subtype = original_subtype
            will_convert_to_mp3 = False
        
        print(f"Output sample rate: {sample_rate} Hz (unchanged)")
        print(f"Saving to: {output_path}")
        
        # Save with appropriate format and quality
        if will_convert_to_mp3:
            # First save as temporary WAV
            temp_wav_path = output_path.with_suffix('.wav')
            print("Saving temporary WAV file...")
            with tqdm(total=1, desc="Writing WAV", unit="file") as pbar:
                sf.write(
                    str(temp_wav_path), 
                    shifted_audio.T if len(shifted_audio.shape) > 1 else shifted_audio,
                    sample_rate,
                    subtype=output_subtype,
                    format=output_format
                )
                pbar.update(1)
            
            # Convert WAV to MP3 using ffmpeg with progress tracking
            final_mp3_path = output_path.with_suffix('.mp3')
            print(f"Converting to MP3: {final_mp3_path.name}")
            
            try:
                # Run ffmpeg with progress output
                cmd = [
                    'ffmpeg', '-i', str(temp_wav_path), 
                    '-codec:a', 'libmp3lame',
                    '-b:a', '320k',  # High quality bitrate
                    '-ac', '2',  # Stereo
                    '-threads', '0',  # Use all CPU cores
                    '-progress', 'pipe:1',  # Progress to stdout
                    '-y', str(final_mp3_path)
                ]
                
                # Start ffmpeg process
                process = subprocess.Popen(
                    cmd, 
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.PIPE,
                    universal_newlines=True,
                    bufsize=1
                )
                
                # Track progress
                duration_seconds = len(shifted_audio) / sample_rate if len(shifted_audio.shape) == 1 else shifted_audio.shape[1] / sample_rate
                
                with tqdm(total=100, desc="MP3 encoding", unit="%") as pbar:
                    last_progress = 0
                    for line in process.stdout:
                        if line.startswith('out_time_ms='):
                            # Extract current time in microseconds
                            time_ms = int(line.split('=')[1])
                            current_seconds = time_ms / 1000000.0
                            
                            # Calculate percentage
                            if duration_seconds > 0:
                                progress = min(100, (current_seconds / duration_seconds) * 100)
                                pbar.update(progress - last_progress)
                                last_progress = progress
                
                # Wait for process to complete
                stdout, stderr = process.communicate()
                
                if process.returncode == 0:
                    # Remove temporary WAV file
                    temp_wav_path.unlink()
                    print(f"✓ Processing complete! Saved as: {final_mp3_path.name}")
                else:
                    print(f"✗ FFmpeg conversion failed: {stderr}")
                    print(f"⚠ Keeping WAV file instead: {temp_wav_path.name}")
                    
            except FileNotFoundError:
                print(f"⚠ FFmpeg not found - keeping WAV file: {temp_wav_path.name}")
                print("  Install FFmpeg for MP3 output: brew install ffmpeg")
            except Exception as e:
                print(f"✗ Conversion error: {str(e)}")
                print(f"⚠ Keeping WAV file: {temp_wav_path.name}")
        else:
            print("Saving final audio file...")
            with tqdm(total=1, desc="Writing audio", unit="file") as pbar:
                sf.write(
                    str(output_path), 
                    shifted_audio.T if len(shifted_audio.shape) > 1 else shifted_audio,
                    sample_rate,
                    subtype=output_subtype,
                    format=output_format
                )
                pbar.update(1)
            print(f"✓ Processing complete! Saved as: {output_path.name}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error processing audio: {str(e)}")
        return False


def get_file_input():
    """Get audio file path from user input (supports drag & drop)."""
    while True:
        print("\n" + "="*50)
        print("VINYL-STYLE PITCH CORRECTOR")
        print("="*50)
        print("Supported formats:", ", ".join(sorted(get_supported_formats())))
        print("\nDrag and drop your audio file into this terminal, or enter the file path:")
        
        file_path = input("> ").strip()
        
        # Remove quotes if present (common when dragging files)
        if file_path.startswith('"') and file_path.endswith('"'):
            file_path = file_path[1:-1]
        elif file_path.startswith("'") and file_path.endswith("'"):
            file_path = file_path[1:-1]
        
        # Handle escaped characters from drag and drop
        # Replace escaped spaces and special characters
        file_path = file_path.replace('\\ ', ' ')  # Escaped spaces
        file_path = file_path.replace('\\(', '(')  # Escaped parentheses
        file_path = file_path.replace('\\)', ')')
        file_path = file_path.replace('\\[', '[')  # Escaped brackets
        file_path = file_path.replace('\\]', ']')
        file_path = file_path.replace('\\,', ',')  # Escaped commas
        file_path = file_path.replace('\\&', '&')  # Escaped ampersands
        file_path = file_path.replace('\\;', ';')  # Escaped semicolons
        file_path = file_path.replace('\\"', '"')  # Escaped quotes
        file_path = file_path.replace("\\'", "'")
        file_path = file_path.replace('\\⧸', '⧸')  # Special characters like division slash
        
        # Expand user path
        file_path = os.path.expanduser(file_path)
        
        # Validate file
        is_valid, message = validate_audio_file(file_path)
        if is_valid:
            return file_path
        else:
            print(f"✗ {message}")
            print("Please try again.\n")


def get_pitch_adjustment():
    """Get pitch adjustment value from user."""
    while True:
        print("\nEnter pitch adjustment in semitones (vinyl-style - changes pitch AND speed):")
        print("Examples: +1 (up 1 semitone, faster), -0.5 (down 50 cents, slower), +1.52 (up 1 semitone + 52 cents, much faster)")
        print("Note: Like a vinyl record, higher pitch = faster playback, lower pitch = slower playback")
        
        try:
            adjustment = input("> ").strip()
            
            # Parse the input
            semitones = float(adjustment)
            
            # Reasonable bounds check
            if abs(semitones) > 12:
                print("✗ Pitch adjustment too extreme (max ±12 semitones)")
                continue
            
            # Convert to more readable format
            cents = abs(semitones % 1) * 100
            full_semitones = int(semitones)
            
            speed_change = semitones_to_ratio(semitones)
            speed_description = "faster" if semitones > 0 else "slower"
            
            if cents > 0:
                direction = "up" if semitones >= 0 else "down"
                print(f"Vinyl adjustment: {direction} {abs(full_semitones)} semitone(s) and {cents:.0f} cent(s)")
                print(f"This will make the audio {speed_change:.3f}x {speed_description} (like changing vinyl RPM)")
            else:
                if semitones == 0:
                    print("No adjustment (0 semitones)")
                else:
                    direction = "up" if semitones > 0 else "down"
                    print(f"Vinyl adjustment: {direction} {abs(full_semitones)} semitone(s)")
                    print(f"This will make the audio {speed_change:.3f}x {speed_description} (like changing vinyl RPM)")
            
            return semitones
            
        except ValueError:
            print("✗ Invalid input. Please enter a number (e.g., +1.5, -0.25)")
        except KeyboardInterrupt:
            print("\n\nExiting...")
            sys.exit(0)


def main():
    """Main function to run the pitch corrector."""
    try:
        print("Initializing Vinyl-Style Pitch Corrector...")
        
        # Check dependencies first
        print("Checking dependencies...")
        if not check_dependencies():
            print("\nPlease install missing dependencies before running the script.")
            sys.exit(1)
        
        # Get input file
        input_file = get_file_input()
        
        # Get pitch adjustment
        semitones = get_pitch_adjustment()
        
        if semitones == 0:
            print("\nNo adjustment needed. Exiting.")
            return
        
        # Process the file
        print(f"\nProcessing: {Path(input_file).name}")
        success = process_audio_file(input_file, semitones)
        
        if success:
            print("\n✓ Vinyl-style pitch correction completed successfully!")
        else:
            print("\n✗ Vinyl-style pitch correction failed.")
            
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ Unexpected error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()