"""
ElevenLabs API — automatische Voiceover-Generierung.

Generiert pro Sektion eine MP3-Datei.
Benötigt: ELEVENLABS_API_KEY als Umgebungsvariable.
"""
import os
import time
import logging
from pathlib import Path

import requests

logger = logging.getLogger(__name__)

ELEVENLABS_API_KEY: str | None = os.getenv("ELEVENLABS_API_KEY")

# Standard deutsche Stimmen (ElevenLabs Voice IDs)
# Diese IDs sind stabile DE-Stimmen — bei Bedarf auf elevenlabs.io anpassen
VOICES = {
    "daniel":  "onwK4e9ZLuTAKqWW03F9",   # Daniel — professionell, männlich
    "luca":    "TX3LPaxmHKxFdv7VOQHJ",   # Luca — natürlich, männlich
    "sarah":   "EXAVITQu4vr4xnSDxMaL",   # Sarah — klar, weiblich
    "default": "onwK4e9ZLuTAKqWW03F9",   # Daniel als Standard
}

ELEVENLABS_TTS_URL = "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"

# Optimale Einstellungen für Voiceover (ruhig, deutlich)
VOICE_SETTINGS = {
    "stability": 0.65,
    "similarity_boost": 0.80,
    "style": 0.10,
    "use_speaker_boost": True,
}


def _call_api(text: str, voice_id: str) -> bytes | None:
    """Ruft die ElevenLabs API auf und gibt die Audio-Bytes zurück."""
    if not ELEVENLABS_API_KEY:
        raise EnvironmentError(
            "ELEVENLABS_API_KEY nicht gesetzt. "
            "Bitte: export ELEVENLABS_API_KEY=dein_key"
        )

    url = ELEVENLABS_TTS_URL.format(voice_id=voice_id)
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json",
        "Accept": "audio/mpeg",
    }
    payload = {
        "text": text,
        "model_id": "eleven_multilingual_v2",   # Beste DE-Qualität
        "voice_settings": VOICE_SETTINGS,
    }

    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=60)
        resp.raise_for_status()
        return resp.content
    except requests.HTTPError as e:
        logger.error(f"ElevenLabs API Fehler {resp.status_code}: {resp.text[:200]}")
        raise
    except Exception as e:
        logger.error(f"ElevenLabs Verbindungsfehler: {e}")
        raise


def generate_voiceover(
    text: str,
    output_path: str | Path,
    voice: str = "daniel",
    retry: int = 3,
) -> Path:
    """
    Generiert eine MP3-Datei aus dem übergebenen Text.

    Args:
        text:        Der zu sprechende Text
        output_path: Pfad der Output-MP3
        voice:       Stimmen-Key aus VOICES dict
        retry:       Anzahl Wiederholungsversuche bei Fehler

    Returns:
        Path zum generierten MP3
    """
    voice_id = VOICES.get(voice, VOICES["default"])
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    for attempt in range(retry):
        try:
            logger.info(f"Generiere Voiceover: {output_path.name} ({len(text)} Zeichen)")
            audio_bytes = _call_api(text, voice_id)
            output_path.write_bytes(audio_bytes)
            logger.info(f"Voiceover gespeichert: {output_path}")
            return output_path
        except Exception as e:
            if attempt < retry - 1:
                wait = 2 ** attempt
                logger.warning(f"Fehler (Versuch {attempt+1}/{retry}): {e} — warte {wait}s")
                time.sleep(wait)
            else:
                raise

    return output_path


def generate_all_voiceovers(
    sections: list,   # list[Section] aus script_parser
    output_dir: str | Path,
    voice: str = "daniel",
) -> list[Path]:
    """
    Generiert Voiceover-MP3s für alle Sektionen.

    Returns:
        Liste der erzeugten MP3-Pfade (in Reihenfolge der Sektionen)
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    mp3_paths: list[Path] = []

    for i, section in enumerate(sections):
        if not section.voiceover.strip():
            continue
        filename = f"{i:02d}_{section.title.lower().replace(' ', '_')[:30]}.mp3"
        path = generate_voiceover(
            text=section.voiceover,
            output_path=output_dir / filename,
            voice=voice,
        )
        mp3_paths.append(path)
        # Rate-Limiting: ElevenLabs erlaubt ~3 Req/Sek auf Free-Plan
        time.sleep(0.5)

    return mp3_paths
