import json
import os
import urllib.parse
import base64
import typing

import httpx

import anthropic
import dotenv

dotenv.load_dotenv()

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

DEFAULT_IMG="https://static.passthru.ai/black-square.png"

SYSTEM_PROMPT="""You are part of a game development project and your goal is to check character image assets as part of the quality assurance process that 3D artists have generated. You will be given PNG or JPEG images of characters from multiple angles or camera views an you need to ensure that the character in the image is consistent with the manner in which the character is displayed in other images from the angle which you are viewing the image.

NOTE: ANY BLACK IMAGES ARE IMAGES THAT FAILED TO LOAD BUT MAINTAIN INDEXES OF THE IMAGE AS THE SAME FOR THE CALLING PROCESS TO BE ABLE TO IDENTIFY WHICH IMAGES HAVE PROBLEMS AND MUST BE REGENERATED. YOU ARE TO EXCLUDE ANY FULLY-BLACK IMAGES FROM THE SET OF IMAGES YOU ARE EVALUATE BUT PRESERVE THE INDICES FOR EACH IMAGE IN THE ORDER YOU REFER TO THE THEM WHEN YOU POINT OUT ERRORS.

--- PROCESS OF IDENTIFYING INCORRECTLY GENERATED IMAGES ---
1. Evaluate the angle from which you are viewing the image and think about what elements of the character you should be able to see from that angle given the details of the character from the other images.
2. Out of all the details you have listed that should be visible from the camera angle you are currently viewing the image from, check the image you are validating for each detail.
3. If there is a missing detail, a detail does not appear as it should be expected to from that angle (such as containing smudges or incorrect positioning or details that do not line up with the other reference images), note that detail missing.

--- EXPECTED OUTPUT GENERATION ---
Return a JSON array that for each image at the index that it is in, there is a list of all errors with that image as follows, for an example. But do not return the following output below as verbatim, but actually return the valid output for the scenario after performing the process detailed above to identify incorrectly generated images. If there are no inconsistencies with an image you may return an empty JSON array at that index such as []. Do not re-evaluate the same inconsistencies across multiple images, as in if image 1 contains something that image 2 does not do not mention it image 1 as having something extra in addition to image 2 not having something.

RETURN JSON as PLAIN TEXT. NO MARKDOWN

--- START EXAMPLE OUTPUT (FROM NEXT LINE ONWARDS) ---
[
  [
    "Character is missing crown on top of the character's head",
    "The colour of different parts of the character skin does not align with the lighting from this angle",
    "Character is missing a leather strap that sits over the character's sword on the right hand side"  ],
  [],
  [
    "Character is missing right-hand",
  ]
]

DO NOT EVALUATE ANY IMAGES THAT ARE EITHER FULLY BLACK BACKGROUND. EXCLUDE SUCH IMAGES FROM THE SET OF IMAGES TO BE EVALUATED AGAINST EACH OTHER TO ENSURE IMAGE CONSISTENCY."""

def critic_image(image_paths: typing.List[str], user_request: str):
    """
    params:
      image_path: local path or image URL
      user_request: the original user request of what characters to generate
    """
    
    # Image path handler
    def handle_image_path(image_path: str) -> str:
        parsed_image_path = urllib.parse(image_path)

        if parsed_image_path.scheme == "http": # image URL on web
            return base64.standard_b64encode(httpx.get(image_path).content).decode("utf-8")
        elif parsed_image_path.scheme == "": # local image
            with open(image_path) as f:
                return base64.standard_b64encode(f.read()).decode("utf-8")
        else:
            return base64.standard_b64encode(httpx.get(DEFAULT_IMG).content).decode("utf-8")
            
    images = [
        { 
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": get_mediatype(image_path),
                "data": handle_image_path(image_path)
            }
        } for image_path in image_paths
    ]

    images.append({"type": "text", "text": SYSTEM_PROMPT})
    
    anthropic_response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": images,
            }
        ],
    )

    return json.loads(anthropic_response.content[0].text)

def get_mediatype(image_path: str):
    filetype_suffix= image_path.spilt(".")[-1]
    if filetype_suffix == "jpg" or "jpeg":
        return "image/jpeg"
    elif filetype_suffix == "png":
        return "image/png"
    else:
        return "image/png"
