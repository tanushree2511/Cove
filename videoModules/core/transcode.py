"""Make every stored video playable in the app's browser engine (Chrome / Edge WebView2).

Browsers only decode H.264 / VP8 / VP9 / AV1 (8-bit 4:2:0) in an MP4 or WebM container. Anything else - AVI/Xvid,
MPEG-4 Part 2, HEVC, MKV, WMV ... - shows thumbnails fine (OpenCV can decode it) but will not play in the player.
`ensure_playable` re-encodes such files to H.264/AAC MP4 and `transcode_to_mp4` does the same into another path.
"""
import logging
import os
import re
import shutil
import subprocess
import sys
import tempfile
from typing import Optional

logger = logging.getLogger(__name__)

PLAYABLE_CONTAINERS = ('.mp4', '.m4v', '.webm')
PLAYABLE_VIDEO_CODECS = {'h264', 'vp8', 'vp9', 'av1'}
PLAYABLE_PIX_FMTS = {'yuv420p', 'yuvj420p'}
PLAYABLE_AUDIO_CODECS = {'aac', 'mp3', 'opus', 'vorbis', 'flac'}

# Don't flash a console window for every ffmpeg call in the packaged Windows app.
_NO_WINDOW = getattr(subprocess, 'CREATE_NO_WINDOW', 0) if sys.platform == 'win32' else 0


def ffmpeg_exe() -> Optional[str]:
    """The bundled imageio-ffmpeg binary, else an ffmpeg on PATH, else None."""
    try:
        import imageio_ffmpeg
        exe = imageio_ffmpeg.get_ffmpeg_exe()
        if exe and os.path.exists(exe):
            return exe
    except Exception:
        pass
    return shutil.which('ffmpeg')


def probe(path: str) -> dict:
    """{'video': codec|None, 'pix_fmt': str|None, 'audio': codec|None} read from `ffmpeg -i` (no ffprobe needed)."""
    empty = {'video': None, 'pix_fmt': None, 'audio': None}
    exe = ffmpeg_exe()
    if not exe:
        return empty
    try:
        text = subprocess.run([exe, '-hide_banner', '-i', path], capture_output=True, text=True,
                              errors='ignore', creationflags=_NO_WINDOW, timeout=60).stderr
    except Exception as exc:
        logger.warning('ffmpeg probe failed for %s: %s', path, exc)
        return empty
    video = re.search(r'Video: (\w+)(.*)', text)
    audio = re.search(r'Audio: (\w+)', text)
    pix_fmt = None
    if video:
        for field in video.group(2).split(','):
            token = field.strip().split(' ')[0].split('(')[0]
            if re.match(r'^(yuv|nv\d|gray|rgb|bgr|gbr|pal|p0)\w*$', token):
                pix_fmt = token
                break
    return {'video': video.group(1).lower() if video else None,
            'pix_fmt': pix_fmt,
            'audio': audio.group(1).lower() if audio else None}


def _video_ok(info: dict) -> bool:
    return info['video'] in PLAYABLE_VIDEO_CODECS and info['pix_fmt'] in PLAYABLE_PIX_FMTS


def _audio_ok(info: dict) -> bool:
    return info['audio'] is None or info['audio'] in PLAYABLE_AUDIO_CODECS


def is_browser_playable(path: str) -> bool:
    if not path.lower().endswith(PLAYABLE_CONTAINERS):
        return False
    info = probe(path)
    return _video_ok(info) and _audio_ok(info)


def transcode_to_mp4(src: str, dest: str) -> bool:
    """Write a browser-playable H.264/AAC MP4 of `src` to `dest` (atomically). True on success; `src` is untouched."""
    exe = ffmpeg_exe()
    if not exe:
        logger.error('ffmpeg is not available - cannot convert %s', src)
        return False
    info = probe(src)
    # Re-use streams that are already fine (fast, lossless); re-encode only what a browser can't play.
    vcodec = ['-c:v', 'copy'] if _video_ok(info) else [
        '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '23', '-pix_fmt', 'yuv420p',
        '-vf', 'scale=trunc(iw/2)*2:trunc(ih/2)*2']
    acodec = ['-c:a', 'copy'] if info['audio'] in ('aac', 'mp3') else (
        ['-an'] if info['audio'] is None else ['-c:a', 'aac', '-b:a', '128k'])
    folder = os.path.dirname(os.path.abspath(dest))
    os.makedirs(folder, exist_ok=True)
    fd, tmp = tempfile.mkstemp(suffix='.mp4', prefix='.convert_', dir=folder)
    os.close(fd)
    try:
        result = subprocess.run([exe, '-y', '-hide_banner', '-loglevel', 'error', '-i', src, *vcodec, *acodec,
                                 '-movflags', '+faststart', tmp],
                                capture_output=True, text=True, errors='ignore', creationflags=_NO_WINDOW)
        if result.returncode != 0 or not os.path.exists(tmp) or os.path.getsize(tmp) == 0:
            logger.error('ffmpeg failed converting %s (exit %s): %s', src, result.returncode, result.stderr.strip()[-400:])
            return False
        os.replace(tmp, dest)
        return True
    except Exception as exc:
        logger.error('Converting %s failed: %s', src, exc)
        return False
    finally:
        if os.path.exists(tmp):
            try:
                os.remove(tmp)
            except OSError:
                pass


def ensure_playable(path: str) -> str:
    """Return a path to a browser-playable version of `path`, converting in place (source removed) when needed.

    On failure the original path is returned unchanged, so callers never lose the file.
    """
    if is_browser_playable(path):
        return path
    stem = os.path.splitext(path)[0]
    dest = stem + '.mp4'
    if os.path.exists(dest) and os.path.abspath(dest) != os.path.abspath(path):
        dest = stem + '_converted.mp4'   # don't clobber an unrelated clip that shares the base name
    logger.info('Converting %s to browser-playable MP4...', os.path.basename(path))
    if not transcode_to_mp4(path, dest):
        return path
    if os.path.abspath(dest) != os.path.abspath(path):
        try:
            os.remove(path)
        except OSError as exc:
            logger.warning('Converted %s but could not remove the original: %s', path, exc)
    return dest
