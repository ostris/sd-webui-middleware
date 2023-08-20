from modules import processing
from ..MiddlewareBase import MiddlewareBase
from modules.processing import StableDiffusionProcessing, Processed


# be sure to add to __init__.py

class ExampleMiddleware(MiddlewareBase):
    # name can be anything, but uid must be unique
    name = "Example Middleware"
    uid = "example_middleware"

    # description can be markdown
    description = f"""
    This is the description from example middleware uid: {uid}
    
    It takes markdown so you can get fancy if you want
    
    - yeah
    - markdown
    """

    def __init__(self, config):
        super().__init__(config)
        self.config = config

    @classmethod
    def get_default_config(cls) -> dict:
        # put whatever default config you want to show in the code block
        # a user modified version will be passed to this class in __init__
        return {}

    def run(self, p: StableDiffusionProcessing) -> Processed:
        # You can do whatever you want here. It is same as run on a script, but also
        # has a config dict
        processed = processing.process_images(p)
        return processed
