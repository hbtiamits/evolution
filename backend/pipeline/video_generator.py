import os
import json
import uuid
import logging
import subprocess
import math
from pathlib import Path
from typing import Optional, Callable
import numpy as np

import anthropic

logger = logging.getLogger(__name__)

WIDTH, HEIGHT = 1280, 720
FPS = 24

OUTPUT_DIR = Path("uploads/videos")
FRAMES_DIR = Path("uploads/frames")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
FRAMES_DIR.mkdir(parents=True, exist_ok=True)


def hex_to_rgb(hex_color: str) -> tuple:
    h = hex_color.lstrip("#")
    if len(h) != 6:
        return (100, 100, 100)
    return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))


def lerp_color(c1: tuple, c2: tuple, t: float) -> tuple:
    return tuple(int(c1[i] * (1 - t) + c2[i] * t) for i in range(3))


def get_ffmpeg() -> str:
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


class VideoGenerator:
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    # ------------------------------------------------------------------ planning

    def _plan_video(self, prompt: str) -> dict:
        system = """You are a professional video producer. Given a natural language description, create a detailed video production plan.

Return ONLY valid JSON (no markdown, no extra text) with this exact structure:
{
  "title": "Video title",
  "subtitle": "Short tagline",
  "total_duration": 25,
  "style": {
    "theme": "modern",
    "primary_color": "#4F46E5",
    "secondary_color": "#7C3AED",
    "accent_color": "#F59E0B",
    "bg_color": "#0F0F1A"
  },
  "scenes": [
    {
      "id": 1,
      "duration": 5,
      "layout": "title",
      "headline": "Main headline text",
      "body": "Supporting text",
      "emoji": "🚀",
      "stats": []
    }
  ],
  "narration": "Full spoken narration script"
}

Layout options: title | feature | stats | quote | cta | split
Create 4-7 scenes, 4-8 seconds each. Total 15-60 seconds.
Choose colors that match the theme and mood. Make it visually compelling."""

        response = self.client.messages.create(
            model="claude-opus-4-8",
            max_tokens=2000,
            system=system,
            messages=[{"role": "user", "content": f"Create a video for: {prompt}"}],
        )
        raw = response.content[0].text.strip()
        if raw.startswith("```"):
            parts = raw.split("```")
            raw = parts[1]
            if raw.startswith("json"):
                raw = raw[4:]
        return json.loads(raw.strip())

    # ------------------------------------------------------------------ fonts

    def _get_font(self, size: int, bold: bool = True):
        from PIL import ImageFont
        candidates = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        ]
        for path in candidates:
            if os.path.exists(path):
                try:
                    return ImageFont.truetype(path, size)
                except Exception:
                    continue
        return ImageFont.load_default()

    # ------------------------------------------------------------------ drawing helpers

    def _gradient_bg(self, primary: tuple, secondary: tuple, bg: tuple):
        from PIL import Image, ImageDraw
        img = Image.new("RGB", (WIDTH, HEIGHT))
        draw = ImageDraw.Draw(img)
        for y in range(HEIGHT):
            t = y / HEIGHT
            # top-third is primary→bg blend, bottom is bg
            if t < 0.5:
                color = lerp_color(primary, bg, t * 1.5)
            else:
                color = lerp_color(bg, secondary, (t - 0.5) * 0.6)
            draw.line([(0, y), (WIDTH, y)], fill=color)
        return img, draw

    def _draw_text_block(
        self,
        draw,
        img,
        text: str,
        font_size: int,
        color: tuple,
        y: int,
        max_width_ratio: float = 0.85,
        shadow: bool = True,
        align: str = "center",
    ) -> int:
        font = self._get_font(font_size)
        max_w = int(WIDTH * max_width_ratio)

        # Word-wrap
        words = text.split()
        lines, current = [], ""
        for word in words:
            test = f"{current} {word}".strip()
            bb = draw.textbbox((0, 0), test, font=font)
            if bb[2] - bb[0] <= max_w:
                current = test
            else:
                if current:
                    lines.append(current)
                current = word
        if current:
            lines.append(current)

        line_h = font_size + int(font_size * 0.3)
        cur_y = y
        for line in lines:
            bb = draw.textbbox((0, 0), line, font=font)
            tw = bb[2] - bb[0]
            x = (WIDTH - tw) // 2
            if shadow:
                draw.text((x + 3, cur_y + 3), line, font=font, fill=(0, 0, 0))
            draw.text((x, cur_y), line, font=font, fill=color)
            cur_y += line_h
        return cur_y

    def _accent_bar(self, draw, accent: tuple):
        draw.rectangle([(0, 0), (WIDTH, 7)], fill=accent)
        draw.rectangle([(0, HEIGHT - 7), (WIDTH, HEIGHT)], fill=accent)

    def _decorative_circles(self, img, primary: tuple, secondary: tuple):
        from PIL import Image, ImageDraw
        overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
        d = ImageDraw.Draw(overlay)
        r, g, b = primary
        d.ellipse([-140, -140, 320, 320], fill=(r, g, b, 35))
        r2, g2, b2 = secondary
        d.ellipse([WIDTH - 280, HEIGHT - 280, WIDTH + 120, HEIGHT + 120], fill=(r2, g2, b2, 30))
        base = img.convert("RGBA")
        combined = Image.alpha_composite(base, overlay)
        return combined.convert("RGB")

    # ------------------------------------------------------------------ scene layouts

    def _render_scene(self, scene: dict, style: dict) -> np.ndarray:
        primary = hex_to_rgb(style.get("primary_color", "#4F46E5"))
        secondary = hex_to_rgb(style.get("secondary_color", "#7C3AED"))
        accent = hex_to_rgb(style.get("accent_color", "#F59E0B"))
        bg = hex_to_rgb(style.get("bg_color", "#0F0F1A"))
        white = (255, 255, 255)
        silver = (200, 200, 215)

        img, draw = self._gradient_bg(primary, secondary, bg)
        img = self._decorative_circles(img, primary, secondary)
        draw_final = __import__("PIL").ImageDraw.Draw(img)
        self._accent_bar(draw_final, accent)

        layout = scene.get("layout", "feature")
        headline = scene.get("headline", "")
        body = scene.get("body", "")
        emoji = scene.get("emoji", "")
        stats = scene.get("stats", [])
        cta = scene.get("cta", "")

        draw = draw_final  # use the updated draw object

        if layout == "title":
            y = HEIGHT // 5
            if emoji:
                y = self._draw_text_block(draw, img, emoji, 72, white, y) + 10
            else:
                y = HEIGHT // 4
            y = self._draw_text_block(draw, img, headline, 68, white, y) + 12
            if body:
                self._draw_text_block(draw, img, body, 34, accent, y)

        elif layout == "feature":
            y = HEIGHT // 6
            if emoji:
                y = self._draw_text_block(draw, img, emoji, 60, white, y) + 8
            else:
                y = HEIGHT // 5
            y = self._draw_text_block(draw, img, headline, 56, white, y) + 14
            if body:
                self._draw_text_block(draw, img, body, 30, silver, y)

        elif layout == "stats":
            self._draw_text_block(draw, img, headline, 50, white, HEIGHT // 10)
            if stats:
                sw = WIDTH // len(stats)
                sy = int(HEIGHT * 0.38)
                font_stat = self._get_font(28)
                font_label = self._get_font(20)
                for i, stat in enumerate(stats):
                    cx = sw * i + sw // 2
                    parts = stat.split(":", 1)
                    value = parts[0].strip()
                    label = parts[1].strip() if len(parts) > 1 else ""
                    bb = draw.textbbox((0, 0), value, font=font_stat)
                    tw = bb[2] - bb[0]
                    draw.text((cx - tw // 2 + 2, sy + 2), value, font=font_stat, fill=(0, 0, 0))
                    draw.text((cx - tw // 2, sy), value, font=font_stat, fill=accent)
                    if label:
                        bb2 = draw.textbbox((0, 0), label, font=font_label)
                        tw2 = bb2[2] - bb2[0]
                        draw.text((cx - tw2 // 2, sy + 46), label, font=font_label, fill=silver)
                    if i < len(stats) - 1:
                        draw.line([(sw * (i + 1), sy - 10), (sw * (i + 1), sy + 80)], fill=secondary, width=2)

        elif layout == "quote":
            font_q = self._get_font(100)
            draw.text((60, 40), "“", font=font_q, fill=accent)
            y = self._draw_text_block(draw, img, headline, 42, white, int(HEIGHT * 0.30)) + 20
            if body:
                self._draw_text_block(draw, img, f"— {body}", 26, silver, y)

        elif layout == "cta":
            y = HEIGHT // 5
            y = self._draw_text_block(draw, img, headline, 62, white, y) + 16
            if body:
                y = self._draw_text_block(draw, img, body, 30, silver, y) + 24
            btn_text = cta or "Get Started"
            font_btn = self._get_font(28)
            bb = draw.textbbox((0, 0), btn_text, font=font_btn)
            bw, bh = bb[2] - bb[0], bb[3] - bb[1]
            bx = (WIDTH - bw - 60) // 2
            by = y + 10
            from PIL import ImageDraw as ID
            draw.rounded_rectangle([bx, by, bx + bw + 60, by + bh + 28], radius=28, fill=accent)
            draw.text((bx + 30, by + 14), btn_text, font=font_btn, fill=bg)

        elif layout == "split":
            mid = WIDTH // 2
            draw.line([(mid, 60), (mid, HEIGHT - 60)], fill=secondary, width=2)
            # Left side
            y_left = HEIGHT // 4
            y_left = self._draw_text_block(
                draw, img, headline, 44, white, y_left, max_width_ratio=0.42
            )
            # Right side body
            if body:
                words = body.split()
                font_b = self._get_font(26)
                y_right = HEIGHT // 4
                line, lines = "", []
                for w in words:
                    test = f"{line} {w}".strip()
                    bb = draw.textbbox((0, 0), test, font=font_b)
                    if bb[2] - bb[0] <= WIDTH // 2 - 60:
                        line = test
                    else:
                        if line:
                            lines.append(line)
                        line = w
                if line:
                    lines.append(line)
                for ln in lines[:6]:
                    bb = draw.textbbox((0, 0), ln, font=font_b)
                    tw = bb[2] - bb[0]
                    lx = mid + (mid - tw) // 2
                    draw.text((lx, y_right), ln, font=font_b, fill=silver)
                    y_right += 40

        else:
            y = HEIGHT // 3
            y = self._draw_text_block(draw, img, headline, 56, white, y) + 14
            if body:
                self._draw_text_block(draw, img, body, 30, silver, y)

        return np.array(img)

    # ------------------------------------------------------------------ transitions

    def _fade_frames(self, frame_a: np.ndarray, frame_b: np.ndarray, n: int = 12) -> list:
        frames = []
        for i in range(1, n + 1):
            t = i / n
            blended = (frame_a * (1 - t) + frame_b * t).astype(np.uint8)
            frames.append(blended)
        return frames

    # ------------------------------------------------------------------ audio

    def _generate_narration(self, text: str, job_id: str) -> Optional[str]:
        try:
            from gtts import gTTS
            path = OUTPUT_DIR / f"{job_id}_narration.mp3"
            gTTS(text=text, lang="en", slow=False).save(str(path))
            return str(path)
        except Exception as e:
            logger.warning(f"TTS failed: {e}")
            return None

    # ------------------------------------------------------------------ video compilation

    def _write_video(
        self,
        scenes: list,
        style: dict,
        audio_path: Optional[str],
        job_id: str,
        progress_cb: Optional[Callable] = None,
    ) -> str:
        import imageio

        raw_path = OUTPUT_DIR / f"{job_id}_raw.mp4"
        final_path = OUTPUT_DIR / f"{job_id}.mp4"

        writer = imageio.get_writer(
            str(raw_path),
            fps=FPS,
            codec="libx264",
            quality=8,
            ffmpeg_log_level="error",
        )

        prev_frame = None
        total_scenes = len(scenes)

        for idx, scene in enumerate(scenes):
            frame = self._render_scene(scene, style)
            duration = max(3, scene.get("duration", 5))

            # Fade transition from previous scene
            if prev_frame is not None:
                for tf in self._fade_frames(prev_frame, frame, n=int(FPS * 0.4)):
                    writer.append_data(tf)

            # Hold frame for scene duration (minus transition time)
            hold_frames = max(1, int(duration * FPS) - int(FPS * 0.4))
            for _ in range(hold_frames):
                writer.append_data(frame)

            prev_frame = frame

            if progress_cb:
                progress_cb(0.25 + 0.50 * ((idx + 1) / total_scenes), f"Rendered scene {idx+1}/{total_scenes}")

        writer.close()

        if audio_path and os.path.exists(audio_path):
            ffmpeg = get_ffmpeg()
            result = subprocess.run(
                [
                    ffmpeg, "-y",
                    "-i", str(raw_path),
                    "-i", audio_path,
                    "-c:v", "copy",
                    "-c:a", "aac",
                    "-shortest",
                    str(final_path),
                ],
                capture_output=True,
            )
            os.remove(str(raw_path))
            if result.returncode != 0:
                logger.warning(f"Audio merge failed: {result.stderr.decode()}")
                # Fall back to video-only
                import shutil
                shutil.move(str(raw_path.with_suffix("").with_suffix(".mp4")), str(final_path))
        else:
            import shutil
            shutil.move(str(raw_path), str(final_path))

        return str(final_path)

    # ------------------------------------------------------------------ public API

    def generate(self, prompt: str, job_id: str, progress_cb: Optional[Callable] = None) -> dict:
        try:
            if progress_cb:
                progress_cb(0.05, "Planning video with AI...")

            plan = self._plan_video(prompt)
            logger.info(f"Video planned: {plan.get('title')}")

            if progress_cb:
                progress_cb(0.20, "Generating narration...")

            narration_text = plan.get("narration", "")
            audio_path = self._generate_narration(narration_text, job_id) if narration_text else None

            if progress_cb:
                progress_cb(0.25, "Rendering scenes...")

            style = plan.get("style", {})
            scenes = plan.get("scenes", [])
            if not scenes:
                raise ValueError("AI returned no scenes")

            video_path = self._write_video(scenes, style, audio_path, job_id, progress_cb)

            if audio_path and os.path.exists(audio_path):
                os.remove(audio_path)

            if progress_cb:
                progress_cb(1.0, "Done!")

            total_duration = sum(max(3, s.get("duration", 5)) for s in scenes)
            return {
                "status": "done",
                "video_path": video_path,
                "title": plan.get("title", ""),
                "subtitle": plan.get("subtitle", ""),
                "scenes": len(scenes),
                "duration": total_duration,
            }

        except Exception as e:
            logger.error(f"Video generation failed: {e}", exc_info=True)
            return {"status": "error", "error": str(e)}
