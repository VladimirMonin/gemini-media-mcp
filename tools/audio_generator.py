import os
import yaml
import wave
from typing import List, Dict, Any, Tuple
from google import genai
from google.genai import types
from config import GEMINI_API_KEY, GEMINI_VOICES_DATA, DEFAULT_VOICE, OUTPUT_AUDIO_DIR
from utils.logger import get_logger

logger = get_logger(__name__)

DEFAULT_TTS_MODEL = "gemini-2.5-flash-preview-tts"


def save_wave_file(
    filename: str,
    pcm_data: bytes,
    channels: int = 1,
    rate: int = 24000,
    sample_width: int = 2,
) -> None:
    """Saves PCM data to a WAV file."""
    with wave.open(filename, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sample_width)
        wf.setframerate(rate)
        wf.writeframes(pcm_data)


def _load_yaml_script(yaml_path: str) -> Dict[str, Any]:
    """Loads and validates the YAML script file."""
    if not os.path.exists(yaml_path):
        raise FileNotFoundError(f"File not found at {yaml_path}")

    with open(yaml_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if not data.get("cast"):
        raise ValueError("YAML must contain a 'cast' section.")
    if not data.get("script"):
        raise ValueError("YAML must contain a 'script' section.")

    return data


def _resolve_voice_name(voice_input: str) -> str:
    """Resolves voice name to the capitalized format required by API."""
    voice_key = voice_input.lower()
    if voice_key in GEMINI_VOICES_DATA:
        return voice_key.capitalize()

    # Strict validation: Raise error if voice is not found
    raise ValueError(
        f"Voice '{voice_input}' is not a valid Gemini voice. Please check 'voices.md' for the list of available voices."
    )


def _prepare_speaker_config(
    cast: List[Dict[str, str]],
) -> Tuple[Dict[str, str], List[types.SpeakerVoiceConfig]]:
    """Prepares speaker mapping and configuration objects."""
    speaker_map = {}
    speaker_configs = []

    for actor in cast:
        name = actor.get("name")
        voice_input = actor.get("voice", DEFAULT_VOICE)
        voice_name = _resolve_voice_name(voice_input)

        speaker_map[name] = voice_name

        speaker_configs.append(
            types.SpeakerVoiceConfig(
                speaker=name,
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name=voice_name
                    )
                ),
            )
        )

    return speaker_map, speaker_configs


def _generate_content_request(
    client: genai.Client,
    model: str,
    prompt: str,
    speaker_configs: List[types.SpeakerVoiceConfig],
    is_multi_speaker: bool,
) -> Any:
    """Sends the generation request to Gemini API."""

    speech_config = (
        types.SpeechConfig(
            multi_speaker_voice_config=types.MultiSpeakerVoiceConfig(
                speaker_voice_configs=speaker_configs
            )
        )
        if is_multi_speaker
        else types.SpeechConfig(voice_config=speaker_configs[0].voice_config)
    )

    return client.models.generate_content(
        model=model,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=speech_config,
        ),
    )


def get_audio_generation_guide() -> str:
    """
    Returns the comprehensive guide for using the audio generation tool.
    Reads the full voice catalog and the example YAML structure from documentation files.
    """
    # Define paths relative to the project root
    # Get the directory containing this file (tools/)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Go up one level to get project root
    base_dir = os.path.dirname(current_dir)

    voices_file_path = os.path.join(base_dir, "docs", "gem", "voices.md")
    example_file_path = os.path.join(
        base_dir, "docs", "examples", "audio_script_example.yaml"
    )

    guide_content = ["# Audio Generation Guide\n"]

    # 1. Read Voices Catalog
    if os.path.exists(voices_file_path):
        try:
            with open(voices_file_path, "r", encoding="utf-8") as f:
                voices_content = f.read()
            guide_content.append("## Voice Catalog\n")
            guide_content.append(voices_content)
            guide_content.append("\n")
        except Exception as e:
            guide_content.append(f"Error reading voices file: {e}\n")
    else:
        guide_content.append(f"Voices file not found at: {voices_file_path}\n")

    # 2. Read YAML Example
    if os.path.exists(example_file_path):
        try:
            with open(example_file_path, "r", encoding="utf-8") as f:
                example_content = f.read()
            guide_content.append("## YAML Script Example\n")
            guide_content.append("Use this structure for your requests:\n")
            guide_content.append("```yaml\n")
            guide_content.append(example_content)
            guide_content.append("\n```\n")
        except Exception as e:
            guide_content.append(f"Error reading example file: {e}\n")
    else:
        guide_content.append(f"Example file not found at: {example_file_path}\n")

    return "\n".join(guide_content)


def generate_audio_from_yaml(yaml_path: str, model: str = DEFAULT_TTS_MODEL) -> str:
    """
    Generates audio from a local YAML script file using Gemini TTS.

    Args:
        yaml_path: Absolute path to the YAML file.
        model: Gemini TTS model to use.
               Default: 'gemini-2.5-flash-preview-tts' (faster, cheaper).
               Alternative: 'gemini-2.5-pro-preview-tts' (higher quality, more expensive).
               You must explicitly specify the Pro model if needed.
    """
    try:
        # 1. Load and Validate
        data = _load_yaml_script(yaml_path)
        cast = data.get("cast", [])
        script = data.get("script", [])

        if len(cast) > 2:
            return "Error: Gemini TTS currently supports a maximum of 2 speakers."

        # 2. Prepare Configuration
        speaker_map, speaker_configs = _prepare_speaker_config(cast)

        # 3. Prepare Prompt
        is_multi_speaker = len(cast) > 1

        if is_multi_speaker:
            prompt_text = ""
            for line in script:
                sp = line.get("speaker")
                txt = line.get("text")
                if sp not in speaker_map:
                    return f"Error: Speaker '{sp}' in script is not defined in 'cast'."
                prompt_text += f"{sp}: {txt}\n"
        else:
            # Single speaker: just the text
            prompt_text = " ".join([line.get("text", "") for line in script])

        logger.info(
            f"Generating audio. Model: {model}, Speakers: {len(cast)}, Script length: {len(prompt_text)}"
        )

        # 4. Call API
        client = genai.Client(api_key=GEMINI_API_KEY)
        response = _generate_content_request(
            client, model, prompt_text, speaker_configs, is_multi_speaker
        )

        # 5. Save Output
        if not response.candidates:
            return "Error: No candidates returned from Gemini API."

        part = response.candidates[0].content.parts[0]
        if not part.inline_data:
            return "Error: No audio data received."

        os.makedirs(OUTPUT_AUDIO_DIR, exist_ok=True)
        base_name = os.path.splitext(os.path.basename(yaml_path))[0]
        output_path = os.path.join(OUTPUT_AUDIO_DIR, f"{base_name}.wav")

        save_wave_file(output_path, part.inline_data.data)

        return f"Audio generated successfully: {os.path.abspath(output_path)}"

    except Exception as e:
        logger.error(f"Generation failed: {e}")
        return f"Critical error: {str(e)}"
