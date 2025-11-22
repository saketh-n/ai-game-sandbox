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

            return {
                'images': result.get('images', []),
                'timings': result.get('timings', {}),
                'seed': result.get('seed'),
                'has_nsfw_concepts': result.get('has_nsfw_concepts', []),
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
            if update.get('status') == 'IN_PROGRESS':
                logs = update.get('logs', [])
                if logs:
                    print(f"Progress: {logs[-1].get('message', '')}")

        callback = on_queue_update or default_callback

        try:
            result = fal_client.subscribe(
                config.model_name,
                arguments=config.to_dict(),
                with_logs=True,
                on_queue_update=callback
            )

            return {
                'images': result.get('images', []),
                'timings': result.get('timings', {}),
                'seed': result.get('seed'),
                'has_nsfw_concepts': result.get('has_nsfw_concepts', []),
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
