#!/usr/bin/env python3
"""Render the procedural Earth template. No network calls or paid services."""
import argparse
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

SUPPORTED_TOPICS = {"earth_rotation", "house_assembly", "room_airflow"}


def load_project(path):
    project = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(project, dict):
        raise ValueError("O projeto deve ser um objeto JSON.")
    if project.get("topic") not in SUPPORTED_TOPICS:
        raise ValueError("Templates disponíveis: earth_rotation, house_assembly, room_airflow.")
    title = project.get("title", "Por que existe dia e noite?")
    if not isinstance(title, str) or not title.strip() or len(title) > 160:
        raise ValueError("Título deve ter entre 1 e 160 caracteres.")
    duration = project.get("duration", 8)
    if isinstance(duration, bool) or not isinstance(duration, (int, float)) or not math.isfinite(duration) or not 3 <= duration <= 30:
        raise ValueError("Duração deve ser de 3 a 30 segundos.")
    captions = project.get("captions", [{"start": 0, "end": duration, "text": title}])
    if not isinstance(captions, list) or len(captions) > 30:
        raise ValueError("Use até 30 legendas.")
    for caption in captions:
        if not isinstance(caption, dict):
            raise ValueError("Cada legenda deve ser um objeto.")
        start, end = caption.get("start"), caption.get("end")
        if any(isinstance(v, bool) or not isinstance(v, (float, int)) or not math.isfinite(v) for v in (start, end)) or not 0 <= start < end <= duration:
            raise ValueError("Tempos de legenda devem estar dentro da duração.")
        if not isinstance(caption.get("text"), str) or len(caption["text"]) > 240:
            raise ValueError("Legenda deve ter até 240 caracteres.")
    return {**project, "title": title, "duration": duration, "captions": captions}


def ass_time(value):
    centiseconds = round(value * 100)
    hours, rest = divmod(centiseconds, 360000)
    minutes, rest = divmod(rest, 6000)
    seconds, cents = divmod(rest, 100)
    return f"{hours}:{minutes:02}:{seconds:02}.{cents:02}"


def subtitle_text(text):
    # Strip ASS override syntax so project text cannot change drawing commands.
    return text.replace("\\", "／").replace("{", "(").replace("}", ")").replace("\r", "").replace("\n", r"\N")


def write_subtitles(project, path, silent):
    head = """[Script Info]
ScriptType: v4.00+
PlayResX: 360
PlayResY: 640
WrapStyle: 0
[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Caption,DejaVu Sans,25,&H00FFFFFF,&H00FFFFFF,&H00111726,&H80111726,-1,0,0,0,100,100,0,0,1,2,0,8,20,20,70,1
Style: Note,DejaVu Sans,10,&H00FFFFFF,&H00FFFFFF,&H00111726,&H80111726,0,0,0,0,100,100,0,0,1,1,0,2,18,18,34,1
Style: Brand,DejaVu Sans,12,&H007CFFDA,&H00FFFFFF,&H00111726,&H80111726,-1,0,0,0,100,100,1,0,1,1,0,8,18,18,24,1
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    lines = [head]
    end = ass_time(project["duration"])
    lines.append(f"Dialogue: 0,0:00:00.00,{end},Brand,,0,0,0,,CURIOLAB 3D · ESTÚDIO\n")
    note = "DEMONSTRAÇÃO SEM NARRAÇÃO · modelo 3D esquemático" if silent else "Modelo 3D esquemático · revisão editorial necessária"
    lines.append(f"Dialogue: 0,0:00:00.00,{end},Note,,0,0,0,,{note}\n")
    for c in project["captions"]:
        lines.append(f"Dialogue: 1,{ass_time(c['start'])},{ass_time(c['end'])},Caption,,0,0,0,,{subtitle_text(c['text'])}\n")
    path.write_text("".join(lines), encoding="utf-8")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--preview", action="store_true")
    parser.add_argument("--full-hd", action="store_true", help="Renderiza 1080x1920, 30fps; não é upscaling de preview.")
    parser.add_argument("--narration", type=Path)
    args = parser.parse_args(argv)
    try:
        project = load_project(args.project)
        for tool in ("blender", "ffmpeg", "ffprobe"):
            if not shutil.which(tool):
                raise ValueError(f"Dependência ausente: {tool}")
        if args.output.suffix.lower() != ".mp4":
            raise ValueError("O arquivo de saída deve terminar em .mp4.")
        if args.narration:
            if not args.narration.is_file():
                raise ValueError("Arquivo de narração não encontrado.")
            probe = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a:0", "-show_entries", "stream=codec_type", "-of", "csv=p=0", str(args.narration.resolve())], check=True, capture_output=True, text=True)
            if "audio" not in probe.stdout:
                raise ValueError("O arquivo de narração não tem faixa de áudio.")
            audio_duration=float(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",str(args.narration.resolve())],text=True))
            if audio_duration > project["duration"]+.25:
                raise ValueError("A narração é maior que o vídeo. Ajuste a duração para não cortar a fala.")
        output = args.output.resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        width, height, fps = (1080, 1920, 30) if args.full_hd else ((360, 640, 8) if args.preview else (720, 1280, 24))
        # Same filesystem as destination: final atomic replacement also works
        # when /tmp and /workspace are separate cloud mounts.
        with tempfile.TemporaryDirectory(prefix=".curiolab-", dir=output.parent) as tmp:
            temp = Path(tmp)
            config = temp / "project.json"
            config.write_text(json.dumps({**project, "width": width, "height": height, "fps": fps}), encoding="utf-8")
            print("Renderizando cenas 3D no Blender…", flush=True)
            render_env = os.environ.copy()
            render_env["XDG_CACHE_HOME"] = str(temp / "cache")
            subprocess.run(["blender", "-b", "-noaudio", "--factory-startup", "-t", "4", "--python", str(Path(__file__).with_name({"house_assembly":"scene_house.py","room_airflow":"scene_room.py"}.get(project["topic"],"scene.py"))), "--", str(config), str(temp)], check=True, env=render_env)
            subs = temp / "captions.ass"
            write_subtitles(project, subs, not bool(args.narration))
            command = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-framerate", str(fps), "-i", str(temp / "frame_%04d.png")]
            if args.narration:
                command += ["-i", str(args.narration.resolve())]
            command += ["-vf", f"ass={subs},fps={30 if args.full_hd else 24}", "-c:v", "libx264", "-preset", "fast", "-crf", "18" if args.full_hd else "23", "-pix_fmt", "yuv420p", "-movflags", "+faststart"]
            if args.narration:
                command += ["-map", "0:v:0", "-map", "1:a:0", "-af", "apad", "-c:a", "aac", "-b:a", "128k"]
            command += ["-t", str(project["duration"]), str(temp / "complete.mp4")]
            subprocess.run(command, check=True, env=render_env)
            os.replace(temp / "complete.mp4", output)
        print(json.dumps({"status": "complete", "output": str(output), "width": width, "height": height, "duration": project["duration"], "silent": not bool(args.narration)}, ensure_ascii=False))
        return 0
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        print(f"Falha na renderização: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
