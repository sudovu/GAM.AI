"""Universal Multimodal Media Generator for GAM.AI.

Supports:
- Text-to-Image (T2I) via Pollinations.ai Flux/Turbo (Zero-Key free tier) & Google Gemini Imagen 3
- Image-to-Video (I2V) Motion Trajectories & Cinematic Canvas WebCodecs synthesis
- Text-to-Video (T2V) Multi-Scene Storyboarding
- Creative AI Director Prompt Engineering Agent
"""

import os
import json
import urllib.parse
import urllib.request
import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

STYLE_PROMPTS = {
    "cinematic": "cinematic film still, 35mm lens, depth of field, blockbuster movie aesthetic, dramatic volumetric lighting, 8k resolution",
    "photorealistic": "hyperrealistic photography, 85mm portrait lens, f/1.8, natural studio lighting, ultra sharp focus, subsurface scattering, raw photo",
    "anime": "masterpiece anime artwork, Makoto Shinkai style, vibrant colors, detailed sky, glowing atmospheric light, sharp cel shading",
    "cyberpunk": "cyberpunk neon atmosphere, wet asphalt reflections, holographic displays, blade runner color grading, moody shadows, teal and magenta glow",
    "3d_render": "octane render, unreal engine 5, raytracing, intricate textures, photorealistic materials, global illumination, 4k",
    "oil_painting": "classic oil painting, rich expressive brush strokes, dramatic chiaroscuro lighting, textured canvas, fine art masterpiece",
    "concept_art": "epic sci-fi concept art, matte painting, sprawling vistas, grand scale, atmospheric haze, trending on artstation"
}

ASPECT_RATIOS = {
    "16:9": (1024, 576),
    "9:16": (576, 1024),
    "1:1": (768, 768),
    "4:3": (800, 600),
    "3:2": (900, 600)
}

MOTION_PROFILES = {
    "push_in": {
        "name": "Cinematic Push-In (Zoom In)",
        "description": "Smooth, dramatic forward camera movement focusing toward center detail",
        "scale_start": 1.0,
        "scale_end": 1.35,
        "pan_x": 0.0,
        "pan_y": 0.0
    },
    "pull_out": {
        "name": "Cinematic Pull-Out (Zoom Out)",
        "description": "Slow reveal pulling back to show the surrounding environment",
        "scale_start": 1.35,
        "scale_end": 1.0,
        "pan_x": 0.0,
        "pan_y": 0.0
    },
    "pan_right": {
        "name": "Dynamic Pan Right",
        "description": "Horizontal tracking camera moving smoothly from left to right",
        "scale_start": 1.15,
        "scale_end": 1.15,
        "pan_x": 40.0,
        "pan_y": 0.0
    },
    "pan_left": {
        "name": "Dynamic Pan Left",
        "description": "Horizontal tracking camera moving smoothly from right to left",
        "scale_start": 1.15,
        "scale_end": 1.15,
        "pan_x": -40.0,
        "pan_y": 0.0
    },
    "parallax_3d": {
        "name": "3D Parallax & Tilt",
        "description": "Subtle multi-axis rotational drift simulating handheld steadicam",
        "scale_start": 1.08,
        "scale_end": 1.22,
        "pan_x": 20.0,
        "pan_y": -15.0
    },
    "drone_orbit": {
        "name": "Drone Orbital Sweep",
        "description": "Wide rotational sweeping motion with gentle elevation change",
        "scale_start": 1.20,
        "scale_end": 1.05,
        "pan_x": -30.0,
        "pan_y": 20.0
    }
}


class MultimodalGenerator:
    """Core generator orchestrating Text-to-Image, Image-to-Video, and Text-to-Video generation."""

    def __init__(self, default_provider: str = "pollinations"):
        self.default_provider = default_provider

    @staticmethod
    def enhance_prompt(prompt: str, media_type: str = "image", style: str = "cinematic") -> Dict[str, Any]:
        """Creative AI Director Agent: Expands a brief concept into a Hollywood-grade prompt."""
        clean_prompt = prompt.strip()
        if not clean_prompt:
            return {"original": "", "enhanced": "", "style": style}

        style_suffix = STYLE_PROMPTS.get(style, STYLE_PROMPTS["cinematic"])

        if media_type == "video":
            enhanced = (
                f"{clean_prompt}, cinematic camera motion, smooth steady tracking shot, "
                f"{style_suffix}, high temporal consistency, 60fps photorealistic motion blur, "
                f"atmospheric environmental movement, masterwork grading"
            )
        elif media_type == "image":
            enhanced = f"{clean_prompt}, {style_suffix}, highly detailed, sharp focus, stunning composition"
        else:
            enhanced = f"{clean_prompt}, {style_suffix}"

        return {
            "original": clean_prompt,
            "enhanced": enhanced,
            "style": style,
            "media_type": media_type
        }

    def generate_image_url(
        self,
        prompt: str,
        aspect_ratio: str = "16:9",
        style: str = "cinematic",
        provider: Optional[str] = None,
        seed: Optional[int] = None,
        api_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate a production-ready image URL or payload.

        - By default, uses Pollinations.ai Flux engine (zero API key needed, instant, high quality).
        - If Gemini/Imagen API key is provided and requested, handles Gemini Imagen format.
        """
        provider = provider or self.default_provider
        width, height = ASPECT_RATIOS.get(aspect_ratio, (1024, 576))

        enhanced_info = self.enhance_prompt(prompt, media_type="image", style=style)
        enhanced_prompt = enhanced_info["enhanced"]

        if provider == "gemini" and api_key:
            # Format Gemini / Imagen 3 API payload structure
            return {
                "status": "success",
                "provider": "gemini",
                "prompt": prompt,
                "enhanced_prompt": enhanced_prompt,
                "aspect_ratio": aspect_ratio,
                "width": width,
                "height": height,
                "model": "imagen-3.0-generate-002",
                "requires_client_fetch": True,
                "api_endpoint": "https://generativelanguage.googleapis.com/v1beta/models/imagen-3.0-generate-002:predict",
                "api_key": api_key,
                "message": "Ready to execute via Gemini Imagen 3"
            }

        # Default: High-performance Pollinations Flux engine
        encoded_prompt = urllib.parse.quote(enhanced_prompt)
        seed_str = f"&seed={seed}" if seed is not None else ""
        image_url = (
            f"https://image.pollinations.ai/prompt/{encoded_prompt}"
            f"?width={width}&height={height}&model=flux&nologo=true&enhance=false{seed_str}"
        )

        return {
            "status": "success",
            "provider": "pollinations_flux",
            "prompt": prompt,
            "enhanced_prompt": enhanced_prompt,
            "aspect_ratio": aspect_ratio,
            "width": width,
            "height": height,
            "image_url": image_url,
            "fallback_url": f"https://image.pollinations.ai/prompt/{urllib.parse.quote(prompt)}?width={width}&height={height}&nologo=true"
        }

    def generate_video_storyboard(
        self,
        prompt: str,
        style: str = "cinematic",
        aspect_ratio: str = "16:9",
        num_scenes: int = 3
    ) -> Dict[str, Any]:
        """Generate a multi-scene cinematic storyboard for full-mode Text-to-Video generation."""
        width, height = ASPECT_RATIOS.get(aspect_ratio, (1024, 576))
        clean_prompt = prompt.strip()

        scenes = []
        motions = ["push_in", "pan_right", "parallax_3d"]
        shot_types = [
            ("Establishing Wide Shot", "Slow cinematic zoom revealing the vast environment"),
            ("Medium Cinematic Shot", "Dynamic tracking shot following key focal elements"),
            ("Dramatic Close-up Shot", "Intense shallow depth-of-field climax shot with volumetric lighting")
        ]

        for i in range(min(num_scenes, len(shot_types))):
            shot_title, shot_desc = shot_types[i]
            motion_key = motions[i % len(motions)]
            motion_meta = MOTION_PROFILES[motion_key]

            scene_prompt = f"{clean_prompt}, {shot_title.lower()}, {shot_desc.lower()}, {STYLE_PROMPTS.get(style, '')}"
            encoded = urllib.parse.quote(scene_prompt)
            keyframe_url = (
                f"https://image.pollinations.ai/prompt/{encoded}"
                f"?width={width}&height={height}&model=flux&nologo=true&seed={1000 + i * 77}"
            )

            scenes.append({
                "scene_index": i + 1,
                "title": shot_title,
                "description": shot_desc,
                "prompt": scene_prompt,
                "motion": motion_key,
                "motion_config": motion_meta,
                "keyframe_url": keyframe_url,
                "duration_seconds": 3.0
            })

        return {
            "status": "success",
            "title": f"Cinematic Storyboard: {clean_prompt[:40]}",
            "aspect_ratio": aspect_ratio,
            "width": width,
            "height": height,
            "style": style,
            "total_duration": sum(s["duration_seconds"] for s in scenes),
            "scenes": scenes
        }

    def get_motion_profiles(self) -> Dict[str, Any]:
        """Return available motion profiles for Image-to-Video animation."""
        return MOTION_PROFILES
