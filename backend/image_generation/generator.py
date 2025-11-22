"""
Image generator using FAL AI API
"""

import os
from typing import List, Dict, Any, Optional
import fal_client
from .config import ImageGenerationConfig


class ImageGenerator:
    """Generate images using FAL AI API"""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the image generator

        Args:
            api_key: FAL API key. If not provided, will use FAL_KEY environment variable
        """
        self.api_key = api_key or os.getenv('FAL_KEY')
        if not self.api_key:
            raise ValueError(
                "FAL API key is required. Pass it as argument or set FAL_KEY environment variable"
            )

        os.environ['FAL_KEY'] = self.api_key

    def generate(self, config: ImageGenerationConfig) -> Dict[str, Any]:
        """
        Generate images based on configuration

        Args:
            config: ImageGenerationConfig object with generation parameters

        Returns:
            Dictionary containing generated images and metadata
        """
        try:
            # Submit the request
            handler = fal_client.submit(
                config.model_name,
                arguments=config.to_dict()
            )

            # Poll for results with status updates
            result = handler.get()

            # Handle both dict and object result types
            if isinstance(result, dict):
                images = result.get('images', [])
                timings = result.get('timings', {})
                seed = result.get('seed')
                has_nsfw = result.get('has_nsfw_concepts', [])
            else:
                images = getattr(result, 'images', [])
                timings = getattr(result, 'timings', {})
                seed = getattr(result, 'seed', None)
                has_nsfw = getattr(result, 'has_nsfw_concepts', [])

            return {
                'images': images,
                'timings': timings,
                'seed': seed,
                'has_nsfw_concepts': has_nsfw,
                'prompt': config.prompt,
                'model': config.model_name
            }

        except Exception as e:
            raise RuntimeError(f"Image generation failed: {str(e)}") from e

    def generate_with_progress(
        self,
        config: ImageGenerationConfig,
        on_queue_update: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        Generate images with progress callbacks

        Args:
            config: ImageGenerationConfig object with generation parameters
            on_queue_update: Callback function for queue updates

        Returns:
            Dictionary containing generated images and metadata
        """
        def default_callback(update):
            # Handle both dict and object types from fal_client
            if isinstance(update, dict):
                status = update.get('status')
            else:
                status = getattr(update, 'status', None)

            if status == 'IN_PROGRESS':
                if isinstance(update, dict):
                    logs = update.get('logs', [])
                else:
                    logs = getattr(update, 'logs', [])

                if logs:
                    last_log = logs[-1] if isinstance(logs, list) else logs
                    if isinstance(last_log, dict):
                        message = last_log.get('message', '')
                    else:
                        message = getattr(last_log, 'message', '')
                    if message:
                        print(f"Progress: {message}")

        callback = on_queue_update or default_callback

        try:
            result = fal_client.subscribe(
                config.model_name,
                arguments=config.to_dict(),
                with_logs=True,
                on_queue_update=callback
            )

            # Handle both dict and object result types
            if isinstance(result, dict):
                images = result.get('images', [])
                timings = result.get('timings', {})
                seed = result.get('seed')
                has_nsfw = result.get('has_nsfw_concepts', [])
            else:
                images = getattr(result, 'images', [])
                timings = getattr(result, 'timings', {})
                seed = getattr(result, 'seed', None)
                has_nsfw = getattr(result, 'has_nsfw_concepts', [])

            return {
                'images': images,
                'timings': timings,
                'seed': seed,
                'has_nsfw_concepts': has_nsfw,
                'prompt': config.prompt,
                'model': config.model_name
            }

        except Exception as e:
            raise RuntimeError(f"Image generation failed: {str(e)}") from e

    def download_images(
        self,
        result: Dict[str, Any],
        output_dir: str = './output'
    ) -> List[str]:
        """
        Download generated images to local directory

        Args:
            result: Result dictionary from generate() or generate_with_progress()
            output_dir: Directory to save images

        Returns:
            List of saved file paths
        """
        import requests
        from pathlib import Path

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        saved_files = []
        images = result.get('images', [])

        for idx, image_data in enumerate(images):
            url = image_data.get('url')
            if not url:
                continue

            # Download image
            response = requests.get(url)
            response.raise_for_status()

            # Save image
            file_path = output_path / f"generated_{idx+1}.png"
            file_path.write_bytes(response.content)
            saved_files.append(str(file_path))

            print(f"Saved: {file_path}")

        return saved_files

    @staticmethod
    def get_available_models() -> List[str]:
        """
        Get a list of commonly used FAL AI models for image generation

        Returns:
            List of model names
        """
        return [
            'fal-ai/flux/dev',
            'fal-ai/flux/schnell',
            'fal-ai/flux-pro',
            'fal-ai/stable-diffusion-v3-medium',
            'fal-ai/fast-sdxl',
            'fal-ai/aura-flow',
        ]
