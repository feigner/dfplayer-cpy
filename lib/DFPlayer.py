# ----------------------------------------------------------------------------
# CircuitPython driver library for the DFPlayer-Mini.
#
# Forked from: https://github.com/bablokb/circuitpython-dfplayer
# Original Author: Bernhard Bablok
# Modified by: EFF
# License: MIT
# ----------------------------------------------------------------------------

import struct
import time

import board
import busio


class DFPlayer:
    MEDIA_U_DISK = 1
    MEDIA_SD = 2
    MEDIA_AUX = 3
    MEDIA_SLEEP = 4
    MEDIA_FLASH = 5

    EQ_NORMAL = 0
    EQ_POP = 1
    EQ_ROCK = 2
    EQ_JAZZ = 3
    EQ_CLASSIC = 4
    EQ_BASS = 5

    STATUS_STOPPED = 0x0200
    STATUS_BUSY = 0x0201
    STATUS_PAUSED = 0x0202

    MAX_VOLUME = 0x1E  # 30

    def __init__(
        self,
        uart=None,
        media=MEDIA_SD,
        volume_pct=50,
        eq=EQ_NORMAL,
        latency=0.100,
    ):
        """
        Initialize DFPlayer and verify connection by querying status.

        :param uart: Optional UART instance (uses board.TX/RX if None)
        :param media: Default media source (e.g., MEDIA_SD)
        :param volume_pct: Initial volume (0–100, pct of MAX_VOLUME)
        :param eq: Equalizer setting (e.g., EQ_NORMAL)
        :param latency: default command delay (in seconds)
        """
        self._uart = uart or busio.UART(board.TX, board.RX, baudrate=9600)
        self._latency = latency
        self.set_media(media)
        if not self.get_status():
            raise Exception("DFPlayer could not be initialized.")
        self.set_volume(volume_pct)
        self.set_eq(eq)

    def _write_data(self, cmd, dataL=0, dataH=0):
        """Send a command frame to the DFPlayer over UART."""
        frame = bytes(
            [
                0x7E,  # Start
                0xFF,  # Firmware version
                0x06,  # Command length
                cmd,  # Command word
                0x00,  # Feedback flag
                dataH,  # DataH
                dataL,  # DataL
                0xEF,  # Stop
            ]
        )
        self._uart.write(frame)

        # give device some time
        if cmd == 0x09:  # set_media
            time.sleep(0.200)
        elif cmd == 0x0C:  # reset
            time.sleep(1.000)
        elif cmd in {0x47, 0x48, 0x49, 0x4E}:  # query files
            time.sleep(0.500)
        elif cmd in {0x03, 0x0D, 0x0F, 0x12, 0x13} or cmd in {0x16}:  # play + stop commands: no delay
            pass
        else:
            time.sleep(self._latency)  # all other commands

    def _read_data(self):
        """Low-level read of 10-byte response frame, returns (cmd, value)."""
        if not self._uart.in_waiting:
            return None

        buf = self._uart.read(10)
        if not buf or len(buf) != 10:
            return None
        if buf[0] != 0x7E or buf[1] != 0xFF or buf[2] != 0x06 or buf[9] != 0xEF:
            return None

        cmd = buf[3]
        data = struct.unpack(">H", buf[5:7])[0]
        return (cmd, data)

    def _read_response(self):
        """Poll UART until most recent valid response is received."""
        res = None
        while True:
            r = self._read_data()
            if not r:
                return res
            res = r

    #
    # Playback Control
    #

    def play(self, folder=None, track=None):
        """Play a specific file, folder/track combo, or resume last playback."""
        if folder is None and track is None:
            self._write_data(0x0D)
        elif folder is None:
            self._write_data(0x03, int(track % 256), int(track // 256))
        elif track is None:
            self._write_data(0x12, folder)
        else:
            self._write_data(0x0F, track, folder)

    def random(self):
        self._write_data(0x18)

    def play_advert(self, track):
        """Play an advertising track from /ADVERT folder."""
        if not (1 <= track <= 9999):
            raise ValueError("Track must be between 1 and 9999")
        self._write_data(0x13, int(track % 256), int(track // 256))

    def stop_advert(self):
        """Abort advert playback and resume previous track."""
        self._write_data(0x15)

    def pause(self):
        self._write_data(0x0E)

    def stop(self):
        self._write_data(0x16)

    def next(self):
        self._write_data(0x01)

    def previous(self):
        self._write_data(0x02)

    def loop(self, on=True):
        """Loop current track. Call with `on=False` to disable."""
        self._write_data(0x19, 0 if on else 1)

    def loop_all(self, on=True):
        """Loop all files on device continuously."""
        self._write_data(0x11, 1 if on else 0)

    def loop_folder(self, folder):
        """Loop all files inside given folder continuously."""
        self._write_data(0x17, folder)

    #
    # Volume & EQ
    #

    def volume_up(self):
        self._write_data(0x04)

    def volume_down(self):
        self._write_data(0x05)

    def set_volume(self, percent):
        percent = max(0, min(100, percent))
        self._write_data(0x06, int(percent * self.MAX_VOLUME / 100))

    def get_volume(self):
        self._write_data(0x43)
        r = self._read_response()
        return int(r[1] / self.MAX_VOLUME * 100) if r and r[0] == 0x43 else 0

    def set_eq(self, eq):
        if eq < 0 or eq > 5:
            eq = 0
        self._write_data(0x07, eq)

    def get_eq(self):
        self._write_data(0x44)
        r = self._read_response()
        return r[1] if r and r[0] == 0x44 else 0

    #
    # Media & Power Control
    #

    def set_media(self, media):
        self._media = media
        self._write_data(0x09, media)

    def set_standby(self, on=True):
        self._write_data(0x0A if on else 0x0B)

    def reset(self):
        self._write_data(0x0C)

    #
    # Status Queries
    #

    def get_status(self):
        self._write_data(0x42)
        r = self._read_response()
        return r[1] if r and r[0] == 0x42 else None

    def get_mode(self):
        """Get current playback source (SD, USB, Flash)."""
        self._write_data(0x45)
        r = self._read_response()
        return r[1] if r and r[0] == 0x45 else None

    def get_version(self):
        """Get firmware version."""
        self._write_data(0x46)
        r = self._read_response()
        return r[1] if r and r[0] == 0x46 else None

    def current_file(self):
        """Get number of currently playing file on SD."""
        self._write_data(0x4C)
        r = self._read_response()
        return r[1] if r and r[0] == 0x4C else None

    def num_files(self, folder=None, media=None):
        """Get number of files in given folder or in entire media device."""
        if folder is not None:
            self._write_data(0x4E, folder)
            r = self._read_response()
            return r[1] if r and r[0] == 0x4E else 0

        media = media or self._media
        cmd = {
            self.MEDIA_U_DISK: 0x47,
            self.MEDIA_SD: 0x48,
            self.MEDIA_FLASH: 0x49,
        }.get(media)
        if not cmd:
            return 0

        self._write_data(cmd)
        r = self._read_response()
        return r[1] if r and r[0] == cmd else 0
