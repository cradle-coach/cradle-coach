"""Generate all static API JSON files for headless demo via Caddy file_server.

Produces:
  static/health.json              — health check
  static/api/presets.json          — preset metadata (from YAML)
  static/api/apps.json             — app list for navigation
  static/api/default_ref_audio.json — default reference audio
"""
import base64
import glob
import json
import os
import sys
import wave

import numpy as np
import yaml


def generate_presets(project_root: str, output_dir: str) -> dict:
    """Convert YAML presets to static JSON."""
    presets_dir = os.path.join(project_root, "assets", "presets")
    output = {}

    for mode_dir in sorted(os.listdir(presets_dir)):
        mode_path = os.path.join(presets_dir, mode_dir)
        if not os.path.isdir(mode_path):
            continue
        mode_presets = []
        for yf in sorted(glob.glob(os.path.join(mode_path, "*.yaml"))):
            with open(yf) as f:
                data = yaml.safe_load(f)
            preset = {
                "id": data.get("id", ""),
                "name": data.get("name", ""),
                "description": data.get("description", ""),
            }
            for key in ("system_prompt", "system_content",
                        "ref_audio_path", "order"):
                if key in data:
                    preset[key] = data[key]
            mode_presets.append(preset)
        mode_presets.sort(key=lambda p: p.get("order", 99))
        output[mode_dir] = mode_presets

    api_dir = os.path.join(output_dir, "api")
    os.makedirs(api_dir, exist_ok=True)
    with open(os.path.join(api_dir, "presets.json"), "w") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    return output


def generate_health(output_dir: str) -> None:
    with open(os.path.join(output_dir, "health.json"), "w") as f:
        json.dump({"status": "ok", "mode": "api_bridge"}, f)


def generate_apps(output_dir: str) -> None:
    api_dir = os.path.join(output_dir, "api")
    os.makedirs(api_dir, exist_ok=True)
    with open(os.path.join(api_dir, "apps.json"), "w") as f:
        json.dump({
            "apps": [
                {"app_id": "turnbased", "name": "Turnbased Chat",
                 "route": "/turnbased.html"},
                {"app_id": "audio_duplex", "name": "Audio Duplex",
                 "route": "/audio-duplex/audio_duplex.html"},
                {"app_id": "omni", "name": "Omni",
                 "route": "/omni/omni.html"},
            ]
        }, f, ensure_ascii=False)


def generate_default_ref_audio(project_root: str, output_dir: str) -> None:
    """Generate default_ref_audio.json in the format expected by ref-audio-init.js:
    {base64, name, duration}. Audio is resampled to 16kHz mono float32."""
    ref_dir = os.path.join(project_root, "assets", "ref_audio")
    wavs = sorted([f for f in os.listdir(ref_dir) if f.endswith(".wav")])
    ref = {"base64": "", "name": "", "duration": 0.0}

    if wavs:
        wav_path = os.path.join(ref_dir, wavs[0])
        with wave.open(wav_path, "rb") as wf:
            channels = wf.getnchannels()
            sr = wf.getframerate()
            sw = wf.getsampwidth()
            frames = wf.readframes(wf.getnframes())

        if sw == 2:
            data = np.frombuffer(frames, dtype="<i2").astype(np.float32) / 32768.0
        elif sw == 1:
            data = (np.frombuffer(frames, dtype=np.uint8).astype(np.float32) - 128.0) / 128.0
        else:
            data = np.frombuffer(frames, dtype="<i4").astype(np.float32) / 2147483648.0

        if channels > 1:
            data = data.reshape(-1, channels).mean(axis=1)

        # Resample to 16kHz
        TARGET_SR = 16000
        if sr != TARGET_SR:
            old_x = np.linspace(0.0, 1.0, num=len(data), endpoint=False)
            new_len = int(round(len(data) * TARGET_SR / sr))
            new_x = np.linspace(0.0, 1.0, num=new_len, endpoint=False)
            data = np.interp(new_x, old_x, data).astype(np.float32)

        data = np.clip(data, -1.0, 1.0).astype(np.float32)
        duration = len(data) / TARGET_SR

        ref = {
            "base64": base64.b64encode(
                data.astype("<f4").tobytes()
            ).decode(),
            "name": wavs[0],
            "duration": round(duration, 1),
        }

    api_dir = os.path.join(output_dir, "api")
    os.makedirs(api_dir, exist_ok=True)
    with open(os.path.join(api_dir, "default_ref_audio.json"), "w") as f:
        json.dump(ref, f)
    print(f"  ref_audio: {ref.get('name', 'none')} ({ref.get('duration', 0)}s @ 16kHz)")


def generate_preset_audio_files(project_root: str, output_dir: str) -> None:
    """Generate per-preset audio JSON files for lazy loading.

    Creates static/api/presets/{mode}/{preset_id}/audio.json
    from the WAV files referenced in preset YAML.
    """
    presets_dir = os.path.join(project_root, "assets", "presets")
    ref_dir = os.path.join(project_root, "assets", "ref_audio")

    # Pre-load all ref audio files
    audio_cache = {}
    for wav_name in os.listdir(ref_dir):
        if not wav_name.endswith(".wav"):
            continue
        wav_path = os.path.join(ref_dir, wav_name)
        with wave.open(wav_path, "rb") as wf:
            channels = wf.getnchannels()
            sr = wf.getframerate()
            sw = wf.getsampwidth()
            frames = wf.readframes(wf.getnframes())

        if sw == 2:
            data = np.frombuffer(frames, dtype="<i2").astype(np.float32) / 32768.0
        elif sw == 1:
            data = (np.frombuffer(frames, dtype=np.uint8).astype(np.float32) - 128.0) / 128.0
        else:
            data = np.frombuffer(frames, dtype="<i4").astype(np.float32) / 2147483648.0

        if channels > 1:
            data = data.reshape(-1, channels).mean(axis=1)
        if sr != 16000:
            old_x = np.linspace(0.0, 1.0, num=len(data), endpoint=False)
            new_len = int(round(len(data) * 16000 / sr))
            new_x = np.linspace(0.0, 1.0, num=new_len, endpoint=False)
            data = np.interp(new_x, old_x, data).astype(np.float32)

        data = np.clip(data, -1.0, 1.0).astype(np.float32)
        audio_cache[wav_name] = {
            "base64": base64.b64encode(data.astype("<f4").tobytes()).decode(),
            "duration": round(len(data) / 16000, 1),
        }

    count = 0
    for mode_dir in sorted(os.listdir(presets_dir)):
        mode_path = os.path.join(presets_dir, mode_dir)
        if not os.path.isdir(mode_path):
            continue
        for yf in sorted(glob.glob(os.path.join(mode_path, "*.yaml"))):
            with open(yf) as f:
                preset = yaml.safe_load(f)
            ref_path = preset.get("ref_audio_path", "")
            wav_name = os.path.basename(ref_path) if ref_path else ""
            if not wav_name or wav_name not in audio_cache:
                continue

            # Create dir: static/api/presets/{mode}/{preset_id}/
            audio_dir = os.path.join(
                output_dir, "api", "presets", mode_dir, preset["id"]
            )
            os.makedirs(audio_dir, exist_ok=True)

            cached = audio_cache[wav_name]
            with open(os.path.join(audio_dir, "audio.json"), "w") as f:
                json.dump({
                    "ref_audio": {
                        "name": wav_name,
                        "data": cached["base64"],
                        "duration": cached["duration"],
                    }
                }, f)
            count += 1

    print(f"  preset_audio: {count} files")


if __name__ == "__main__":
    root = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    static_dir = os.path.join(root, "static")

    print("Generating static API files...")
    generate_health(static_dir)
    print("  health.json")

    result = generate_presets(root, static_dir)
    print(f"  presets.json: {list(result.keys())}")
    for mode, ps in result.items():
        print(f"    {mode}: {len(ps)} presets")

    generate_apps(static_dir)
    print("  apps.json")

    generate_default_ref_audio(root, static_dir)

    generate_preset_audio_files(root, static_dir)

    # Frontend defaults (empty — all values from presets/config)
    api_dir = os.path.join(static_dir, "api")
    with open(os.path.join(api_dir, "frontend_defaults.json"), "w") as f:
        json.dump({}, f)
    print("  frontend_defaults.json")

    print("Done. Ready for Caddy: handle /api/* { try_files {path}.json {path}; file_server }")
