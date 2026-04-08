"""
Video-Assembler: kombiniert Audio (MP3) + Visuals (PNG) zu einem MP4.

Verwendet MoviePy für die Zusammenstellung:
- Je Sektion: ImageClip (PNG, Dauer = Audio-Länge) + AudioFileClip (MP3)
- Fade-Übergänge zwischen Sektionen
- Untertitel-Overlay (Sektion-Titel unten links)
- Output: 1920×1080, 24fps, H.264/AAC
"""
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

W, H = 1920, 1080
FPS  = 24


def _make_subtitle_clip(text: str, duration: float):
    """Erstellt einen halbtransparenten Untertitel-Clip."""
    from moviepy import TextClip, ColorClip, CompositeVideoClip

    try:
        txt = TextClip(
            text=text[:60],
            font_size=36,
            color="white",
            font="Liberation-Sans-Bold",
            duration=duration,
        ).with_position(("left", "bottom")).with_margin(left=60, bottom=40)
        return txt
    except Exception:
        # Fallback ohne Schriftart-Spezifikation
        try:
            return TextClip(
                text=text[:60],
                font_size=36,
                color="white",
                duration=duration,
            ).with_position(("left", "bottom")).with_margin(left=60, bottom=40)
        except Exception as e:
            logger.warning(f"Subtitle-Clip fehlgeschlagen: {e}")
            return None


def build_section_clip(visual_path: Path, audio_path: Path,
                       section_title: str, fade: float = 0.5):
    """
    Erstellt einen VideoClip für eine einzelne Sektion.

    visual_path: PNG-Datei (Titelkarte, Screenshot, Grafik)
    audio_path:  MP3-Datei (Voiceover)
    section_title: Text für Untertitel-Overlay
    fade: Fade-In/Out Dauer in Sekunden
    """
    from moviepy import ImageClip, AudioFileClip, CompositeVideoClip

    audio = AudioFileClip(str(audio_path))
    duration = audio.duration

    # Bild auf Audio-Länge strecken
    img_clip = (
        ImageClip(str(visual_path), duration=duration)
        .resized((W, H))
    )

    # Untertitel
    sub = _make_subtitle_clip(section_title, duration)
    if sub:
        clip = CompositeVideoClip([img_clip, sub])
    else:
        clip = img_clip

    # Audio hinzufügen + Fade
    clip = (
        clip
        .with_audio(audio)
        .with_effects([
            __import__("moviepy.video.fx", fromlist=["CrossFadeIn"]).CrossFadeIn(fade),
        ])
    )
    return clip


def build_video(
    sections_data: list[dict],
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
    from moviepy import concatenate_videoclips, ImageClip, AudioFileClip, CompositeVideoClip

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    clips = []
    total = len(sections_data)

    for i, sd in enumerate(sections_data):
        audio_p   = Path(sd["audio"])
        visual_p  = Path(sd["visual"])
        title     = sd.get("title", "")

        if not audio_p.exists():
            logger.warning(f"Audio fehlt: {audio_p} — überspringe Sektion")
            continue
        if not visual_p.exists():
            logger.warning(f"Visual fehlt: {visual_p} — überspringe Sektion")
            continue

        logger.info(f"Clip {i+1}/{total}: {title}")

        audio = AudioFileClip(str(audio_p))
        duration = audio.duration

        img_clip = (
            ImageClip(str(visual_p), duration=duration)
            .resized((W, H))
        )

        sub = _make_subtitle_clip(title, duration)
        if sub:
            video_clip = CompositeVideoClip([img_clip, sub])
        else:
            video_clip = img_clip

        video_clip = video_clip.with_audio(audio)
        clips.append(video_clip)

    if not clips:
        raise ValueError("Keine gültigen Clips zum Zusammenstellen gefunden.")

    logger.info(f"Zusammenstellen von {len(clips)} Clips → {output_path.name}")
    final = concatenate_videoclips(clips, method="compose", padding=-fade)

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
