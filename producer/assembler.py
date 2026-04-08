"""
Video-Assembler: kombiniert Audio (MP3) + Visuals (PNG) zu einem MP4.

Kompatibel mit MoviePy 1.x und 2.x.
- Je Sektion: ImageClip (PNG, Dauer = Audio-Länge) + AudioFileClip (MP3)
- Output: 1920×1080, 24fps, H.264/AAC
"""
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

W, H = 1920, 1080
FPS  = 24

# ── MoviePy Version-kompatible Imports ───────────────────────────────────────
MOVIEPY_V2 = False

try:
    # MoviePy 2.x: direkte Imports aus moviepy-Paket
    from moviepy import ImageClip, AudioFileClip, CompositeVideoClip  # type: ignore
    try:
        from moviepy import concatenate_videoclips  # type: ignore
    except ImportError:
        from moviepy.video.compositing.concatenate import concatenate_videoclips  # type: ignore
    MOVIEPY_V2 = True
    logger.info("MoviePy 2.x erkannt")
except ImportError:
    try:
        # MoviePy 1.x: Imports aus moviepy.editor
        from moviepy.editor import (  # type: ignore
            ImageClip, AudioFileClip, CompositeVideoClip, concatenate_videoclips
        )
        logger.info("MoviePy 1.x erkannt")
    except ImportError as e:
        raise ImportError(
            f"MoviePy nicht installiert oder fehlerhaft: {e}\n"
            "Installiere mit: pip install 'moviepy>=1.0.3'"
        ) from e


def _resize_clip(clip, width: int, height: int):
    """Resize-Wrapper für MoviePy 1.x und 2.x."""
    if MOVIEPY_V2:
        return clip.resized((width, height))
    else:
        return clip.resize((width, height))


def _set_audio(clip, audio):
    """Audio-Wrapper für MoviePy 1.x und 2.x."""
    if MOVIEPY_V2:
        return clip.with_audio(audio)
    else:
        return clip.set_audio(audio)


def _make_subtitle_clip(text: str, duration: float):
    """Erstellt einen Untertitel-Clip — mit Fallback wenn TextClip nicht verfügbar."""
    try:
        if MOVIEPY_V2:
            from moviepy import TextClip  # type: ignore
            txt = TextClip(
                text=text[:60],
                font_size=36,
                color="white",
                font="Liberation-Sans-Bold",
                duration=duration,
            )
        else:
            from moviepy.editor import TextClip  # type: ignore
            txt = TextClip(
                txt=text[:60],
                fontsize=36,
                color="white",
                font="Liberation-Sans-Bold",
            ).set_duration(duration)

        if MOVIEPY_V2:
            return txt.with_position(("left", "bottom"))
        else:
            return txt.set_position(("left", "bottom"))

    except Exception:
        # Fallback ohne Font-Spezifikation
        try:
            if MOVIEPY_V2:
                from moviepy import TextClip  # type: ignore
                txt = TextClip(
                    text=text[:60],
                    font_size=36,
                    color="white",
                    duration=duration,
                )
                return txt.with_position(("left", "bottom"))
            else:
                from moviepy.editor import TextClip  # type: ignore
                txt = TextClip(
                    txt=text[:60],
                    fontsize=36,
                    color="white",
                ).set_duration(duration)
                return txt.set_position(("left", "bottom"))
        except Exception as e:
            logger.warning(f"Subtitle-Clip fehlgeschlagen: {e}")
            return None


def build_video(
    sections_data: list,
    output_path: Path,
    fps: int = FPS,
    fade: float = 0.5,
) -> Path:
    """
    Assemblt alle Sektionen zu einem finalen MP4.

    sections_data: Liste von dicts:
        {
          "audio":   Path  (MP3),
          "visual":  Path  (PNG),
          "title":   str,
        }
    output_path: Zielpfad für das MP4

    Returns: output_path
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    clips = []
    total = len(sections_data)

    for i, sd in enumerate(sections_data):
        audio_p  = Path(sd["audio"])
        visual_p = Path(sd["visual"])
        title    = sd.get("title", "")

        if not audio_p.exists():
            logger.warning(f"Audio fehlt: {audio_p} — überspringe Sektion")
            continue
        if not visual_p.exists():
            logger.warning(f"Visual fehlt: {visual_p} — überspringe Sektion")
            continue

        logger.info(f"Clip {i+1}/{total}: {title}")

        audio    = AudioFileClip(str(audio_p))
        duration = audio.duration

        img_clip = _resize_clip(
            ImageClip(str(visual_p), duration=duration),
            W, H
        )

        sub = _make_subtitle_clip(title, duration)
        if sub:
            video_clip = CompositeVideoClip([img_clip, sub])
        else:
            video_clip = img_clip

        video_clip = _set_audio(video_clip, audio)
        clips.append(video_clip)

    if not clips:
        raise ValueError("Keine gültigen Clips zum Zusammenstellen gefunden.")

    logger.info(f"Zusammenstellen von {len(clips)} Clips → {output_path.name}")

    if len(clips) == 1:
        final = clips[0]
    else:
        final = concatenate_videoclips(clips, method="compose")

    final.write_videofile(
        str(output_path),
        fps=fps,
        codec="libx264",
        audio_codec="aac",
        temp_audiofile=str(output_path.parent / "temp_audio.m4a"),
        remove_temp=True,
        logger="bar",
    )
    logger.info(f"Video fertig: {output_path}")
    return output_path
