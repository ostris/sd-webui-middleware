import os
from typing import TYPE_CHECKING

from modules import processing

EXTENSION_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # extensions/sd-webui-ai-toolkit

if TYPE_CHECKING:
    from modules.processing import StableDiffusionProcessing, Processed


class MiddlewareBase:
    name = "Base Middleware"
    uid = "base_middleware"
    description = "Base Middleware"

    extension_root = EXTENSION_ROOT

    def __init__(self, *args, **kwargs):
        pass

    @classmethod
    def get_default_config(cls) -> dict:
        # override in child class
        return {}

    def run(self, p: 'StableDiffusionProcessing') -> 'Processed':
        # Extend this in child class
        processed = processing.process_images(p)
        return processed
