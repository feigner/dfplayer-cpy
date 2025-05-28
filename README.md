# DFPlayer Mini + CircuitPython

A CircuitPython library for interacting with the [DFPlayer Mini](https://wiki.dfrobot.com/DFPlayer_Mini_SKU_DFR0299), a small, low cost MP3/WAV player

This library is based on and updates the original work from: [https://github.com/bablokb/circuitpython-dfplayer/](https://github.com/bablokb/circuitpython-dfplayer/) and [https://github.com/jczic/KT403A-MP3](https://github.com/jczic/KT403A-MP3)

## Features

- UART communication with DFPlayer Mini
- Play, pause, stop, next, previous, random
- Loop single track, folder, or entire media
- Play interrupting "advertisement" tracks
- Query current volume, track, firmware version
- Optional latency control for fast playback

## Installation

Copy `DFPlayer.py` into your board's `/lib/` directory. Import, initialze and go.

## Basic Usage

```python
from DFPlayer import DFPlayer

# Initialize with default UART on TX/RX
player = DFPlayer()

# Play first file on SD card
player.play(track=1)

# Play file 3 in folder 2
player.play(folder=2, track=3)

# Loop current track
player.loop()

# Loop all files in folder 3 (i.e., /03/0001.mp3, /03/0002.mp3, ...)
player.loop_folder(3)

# Loop all files on device
player.loop_all()

# Stop looping current track
player.loop(on=False)

# Stop playback
player.stop()

# Play next or previous track
player.next()
player.previous()

# Play random track
player.random()

# Pause/resume
player.pause()
player.play()
```

## Advertisement Playback

Interrupt current playback with a track from /ADVERT/0001.mp3 to /ADVERT/9999.mp3:

```python
player.play_advert(1)    # plays /ADVERT/0001.mp3
player.stop_advert()     # resumes previous track
```
This feature is useful when you want to briefly override background audio with a temporary message or sound effect.

Note: Only works when a track is currently playing. After the advert finishes, the original track playback resumes automatically.

## Controls

```python
# Set volume to 75%
player.set_volume(75)

# Increase or decrease volume
player.volume_up()
player.volume_down()

# Set equalizer to ROCK
player.set_eq(DFPlayer.EQ_ROCK)
```

## Queries

```python
print("Volume:", player.get_volume())
print("EQ:", player.get_eq())
print("Status:", player.get_status())
print("Current file:", player.current_file())
print("Files in folder 5:", player.num_files(folder=5))
print("Firmware version:", player.get_version())
print("Playback source:", player.get_mode())
```

## Notes

- Files must be named 0001.mp3, 0002.mp3, ..., placed in folders /01, /02, etc.
- Folder names must be exactly 2-digit strings: 01, 02, ... up to 99
- Ad tracks must be placed in a folder named ADVERT
- Do not exceed 99 folders or 255 tracks per folder
- default max volume is *half* of what the device is capable of, this thing can get loud

## License

MIT
