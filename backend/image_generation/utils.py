"""
Utility functions for image processing
"""

import base64
from io import BytesIO
from typing import Union
from pathlib import Path
from PIL import Image


def image_to_data_uri(image: Union[str, Path, Image.Image, bytes]) -> str:
    """
    Convert an image to a base64 data URI that can be used with FAL AI API

    Args:
        image: Can be one of:
            - str/Path: Local file path to an image
            - PIL.Image.Image: PIL Image object
            - bytes: Raw image bytes

    Returns:
        Base64-encoded data URI string (e.g., 'data:image/png;base64,...')

    Raises:
        ValueError: If image format is not supported
        FileNotFoundError: If file path doesn't exist
    """
    try:
        # Handle file path (str or Path)
        if isinstance(image, (str, Path)):
            path = Path(image)
            if not path.exists():
                raise FileNotFoundError(f"Image file not found: {path}")

            with open(path, 'rb') as f:
                image_bytes = f.read()

            # Determine MIME type from file extension
            extension = path.suffix.lower()
            mime_type_map = {
                '.png': 'image/png',
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.webp': 'image/webp',
                '.gif': 'image/gif',
            }
            mime_type = mime_type_map.get(extension, 'image/png')

        # Handle PIL Image
        elif isinstance(image, Image.Image):
            buffer = BytesIO()
            image_format = image.format or 'PNG'
            image.save(buffer, format=image_format)
            image_bytes = buffer.getvalue()

            mime_type_map = {
                'PNG': 'image/png',
                'JPEG': 'image/jpeg',
                'WEBP': 'image/webp',
                'GIF': 'image/gif',
            }
            mime_type = mime_type_map.get(image_format, 'image/png')

        # Handle raw bytes
        elif isinstance(image, bytes):
            image_bytes = image
            # Try to detect format from bytes
            try:
                pil_image = Image.open(BytesIO(image_bytes))
                image_format = pil_image.format or 'PNG'
                mime_type_map = {
                    'PNG': 'image/png',
                    'JPEG': 'image/jpeg',
                    'WEBP': 'image/webp',
                    'GIF': 'image/gif',
                }
                mime_type = mime_type_map.get(image_format, 'image/png')
            except Exception:
                mime_type = 'image/png'

        else:
            raise ValueError(
                f"Unsupported image type: {type(image)}. "
                "Must be file path (str/Path), PIL Image, or bytes."
            )

        # Encode to base64
        base64_encoded = base64.b64encode(image_bytes).decode('utf-8')

        # Return data URI
        return f"data:{mime_type};base64,{base64_encoded}"

    except Exception as e:
        raise ValueError(f"Failed to convert image to data URI: {str(e)}") from e


def is_url(image_source: str) -> bool:
    """
    Check if a string is a URL

    Args:
        image_source: String to check

    Returns:
        True if the string appears to be a URL, False otherwise
    """
    return (
        image_source.startswith('http://') or
        image_source.startswith('https://') or
        image_source.startswith('data:')
    )


def process_inspiration_image(image: Union[str, Path, Image.Image, bytes]) -> str:
    """
    Process an inspiration image into a format suitable for FAL AI API

    Args:
        image: Can be:
            - str: URL (http/https) or local file path
            - Path: Local file path
            - PIL.Image.Image: PIL Image object
            - bytes: Raw image bytes

    Returns:
        Either the original URL string or a base64 data URI
    """
    # If it's a string and already a URL, return as-is
    if isinstance(image, str) and is_url(image):
        return image

    # Otherwise, convert to data URI
    return image_to_data_uri(image)
