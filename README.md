# Vinyl-Style Audio Pitch Corrector

A Python script that performs vinyl-style pitch correction on audio files, where both pitch and speed change together proportionally - just like changing the RPM on a turntable.

## Features

- **Vinyl-style pitch shifting**: Changes both pitch and speed together (higher pitch = faster, lower pitch = slower)
- **Fine pitch control**: Adjust by semitones and cents (e.g., +1.52 = 1 semitone + 52 cents)
- **Universal format support**: Handles WAV, FLAC, MP3, M4A, OGG, OPUS, and more
- **Lossless processing**: Maintains audio quality throughout the process
- **Smart format handling**: MP3 → MP3, FLAC → FLAC, etc.
- **Progress tracking**: Real-time progress bars for all operations
- **Drag & drop support**: Simply drag audio files into the terminal

## Installation

### Prerequisites

1. **Python 3.8+** - [Download Python](https://www.python.org/downloads/)
2. **FFmpeg** (for MP3 support) - Install using:
   - **macOS**: `brew install ffmpeg`
   - **Linux**: `sudo apt install ffmpeg`
   - **Windows**: Download from [ffmpeg.org](https://ffmpeg.org/download.html)

### Quick Setup

1. Download these files:
   - `pitch_corrector.py`
   - `requirements.txt`

2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the script:
   ```bash
   python pitch_corrector.py
   ```

### Manual Installation

If you don't have the requirements.txt file, install packages individually:

```bash
pip install librosa>=0.10.0 soundfile>=0.12.1 numpy>=1.24.0 resampy>=0.4.0 tqdm>=4.64.0
```

## Usage

### Basic Usage

1. Run the script:
   ```bash
   python pitch_corrector.py
   ```

2. **Drag and drop** your audio file into the terminal when prompted, or type the file path

3. Enter your pitch adjustment:
   - `+1` = up 1 semitone (faster)
   - `-0.5` = down 50 cents (slower)
   - `+1.52` = up 1 semitone + 52 cents (much faster)
   - `0` = no change

4. Wait for processing to complete!

### Examples

- **Tune up a recording**: `+0.37` (37 cents higher, slightly faster)
- **Slow down fast speech**: `-2` (2 semitones lower, much slower)
- **Speed up a song**: `+1` (1 semitone higher, noticeably faster)

## Output Formats

The script intelligently handles output formats:

| Input Format | Output Format | Notes |
|--------------|---------------|-------|
| MP3 | MP3 | Uses FFmpeg for conversion |
| WAV | WAV | Direct lossless processing |
| FLAC | FLAC | Direct lossless processing |
| M4A | FLAC | Converted for compatibility |
| Other | FLAC/WAV | Best available format |

## Troubleshooting

### Dependencies Missing
The script will check for missing dependencies and show exactly what to install:
```
❌ Missing required Python packages:
  - librosa>=0.10.0
  - soundfile>=0.12.1

To install missing packages, run:
  pip install librosa>=0.10.0 soundfile>=0.12.1
```

### FFmpeg Not Found
If FFmpeg is missing, MP3 files will be converted to WAV instead:
```
⚠ ffmpeg not found - MP3 output will fallback to WAV
  Install with: brew install ffmpeg (macOS) or apt install ffmpeg (Linux)
```

### File Not Found Error
If drag-and-drop doesn't work, try:
1. Type the full file path manually
2. Move your audio file to the same folder as the script
3. Check that the file extension is supported

### Large Files Taking Too Long
For very large files (>1 hour), consider:
- Using smaller pitch adjustments
- Converting to a lower bitrate first
- Processing in chunks if needed

## Technical Details

### How It Works
1. **Audio Loading**: Uses librosa to load audio in original quality
2. **Pitch Shifting**: Resamples audio at different rate, then saves at original rate
3. **Format Handling**: Preserves original format when possible
4. **Progress Tracking**: Real-time feedback for all operations

### Supported Formats
- **Input**: WAV, FLAC, MP3, M4A, OGG, OPUS, AIFF, AU, SND
- **Output**: Same as input (when possible), or FLAC/WAV for compatibility

### Quality Settings
- **FLAC**: 24-bit lossless compression
- **WAV**: 16-bit or 24-bit uncompressed
- **MP3**: 320kbps high quality

## License

This script is provided as-is for educational and personal use. Feel free to modify and share!

## Credits

Built with:
- [librosa](https://librosa.org/) - Audio processing
- [soundfile](https://pysoundfile.readthedocs.io/) - Audio I/O
- [FFmpeg](https://ffmpeg.org/) - Format conversion
- [tqdm](https://tqdm.github.io/) - Progress bars