from ..MiddlewareBase import MiddlewareBase
from modules.processing import StableDiffusionProcessing, Processed


# be sure to add to __init__.py

class ExampleMiddleware(MiddlewareBase):
    # name can be anything, but uid must be unique
    name = "Example Middleware"
    uid = "example_middleware"

    def __init__(self, config):
        super().__init__(config)
        self.config = config

    def run(self, p: StableDiffusionProcessing) -> Processed:
        pass
