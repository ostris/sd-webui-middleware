import importlib
import json
import pkgutil
import re
import os
import typing
from typing import List, Union

import modules.scripts as scripts
import gradio as gr
import sys

from middleware import MiddlewareBase
from modules import errors
from modules.ui_common import create_refresh_button
import copy

EXTENSION_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # extensions/sd-webui-ai-toolkit
MIDDLEWARE_ROOT = os.path.join(EXTENSION_ROOT, "middleware")  # extensions/sd-webui-ai-toolkit/middleware
MIDDLEWARE_DB_PATH = os.path.join(EXTENSION_ROOT, "storage", "middleware.db.json")

# add MIDDLEWARE_ROOT to sys modules
sys.path.append(EXTENSION_ROOT)
sys.path.append(MIDDLEWARE_ROOT)

known_middleware: List['MiddlewareBase'] = []


def update_known_middleware():
    global known_middleware
    middleware_folders = ['middleware']

    # This will hold the classes from all middleware modules
    all_middleware_classes: List['MiddlewareBase'] = []

    # Iterate over all directories (i.e., packages) in the "middlewares" directory
    for sub_dir in middleware_folders:
        middlewares_dir = os.path.join(EXTENSION_ROOT, sub_dir)
        for (_, name, _) in pkgutil.iter_modules([middlewares_dir]):
            try:
                # Import the module
                module = importlib.import_module(f"{sub_dir}.{name}")
                # Get the value of the AI_TOOLKIT_EXTENSIONS variable
                middlewares = getattr(module, "MIDDLEWARE_MODULES", None)
                # Check if the value is a list
                if isinstance(middlewares, list):
                    # Iterate over the list and add the classes to the main list
                    all_middleware_classes.extend(middlewares)
            except ImportError as e:
                print(f"Failed to import the {name} module. Error: {str(e)}")

    # filter out the base class
    all_middleware_classes = [x for x in all_middleware_classes if x.uid != "base_middleware"]
    known_middleware = all_middleware_classes


def get_all_middlewares_process_dict():
    global known_middleware
    update_known_middleware()
    process_dict = {}
    for middleware in known_middleware:
        process_dict[middleware.uid] = middleware
    return process_dict


empty_db = {
    "middleware": {}
}


def get_middleware_list():
    global known_middleware

    def convert(name):
        return int(name) if name.isdigit() else name.lower()

    def alphanumeric_key(key):
        return [convert(c) for c in re.split('([0-9]+)', key)]

    return sorted(
        [f"{x.name} ({x.uid})" for x in known_middleware], key=alphanumeric_key)


def update_middleware_db():
    db = copy.deepcopy(empty_db)
    if os.path.exists(MIDDLEWARE_DB_PATH):
        with open(MIDDLEWARE_DB_PATH, "r") as f:
            db = json.load(f)

    process_dict = get_all_middlewares_process_dict()

    for uid, middleware in process_dict.items():
        db["middleware"][uid] = {
            "name": middleware.name,
            "module": middleware.__module__
        }

    os.makedirs(os.path.dirname(MIDDLEWARE_DB_PATH), exist_ok=True)
    with open(MIDDLEWARE_DB_PATH, "w") as f:
        # utf-8 is the default encoding for json
        json.dump(db, f, indent=2)


# run once on load
update_middleware_db()


def get_middleware_class_from_str(middleware_str) -> Union[None, 'MiddlewareBase']:
    global known_middleware

    if middleware_str == "" or middleware_str is None:
        return None

    # find middleware, selected_middleware is in format "name (uid)", we need to extract uid
    uid = middleware_str.split("(")[1].split(")")[0]

    middleware_class = None
    for middleware in known_middleware:
        if middleware.uid == uid:
            middleware_class = middleware
            break

    if middleware_class is None:
        errors.report(f"Middleware {uid} not found", exc_info=True)
        return

    return middleware_class


def handle_middleware_select_change(middleware_str: Union[str, None]):
    middleware_class: 'MiddlewareBase' = get_middleware_class_from_str(middleware_str)
    if middleware_class is None:
        return None

    # make the config json
    default_config = middleware_class.get_default_config()
    if default_config is None:
        default_config = {}

    config_json = json.dumps(default_config, indent=2)

    # make the markdown info
    markdown_ingo = f"""
    
    # {middleware_class.name}
    
    {middleware_class.description}
    
    """

    return [markdown_ingo, config_json]


class Script(scripts.Script):
    def title(self):
        return "Run Middleware"

    def ui(self, is_img2img):
        with gr.Row():
            selected_middleware = gr.Dropdown(
                get_middleware_list(),
                show_label=True,
                elem_id="middleware_selector",
                label="Middleware",
            )
            create_refresh_button(
                refresh_component=selected_middleware,
                refresh_method=update_middleware_db,
                refreshed_args=lambda: {"choices": get_middleware_list()},
                elem_id="middleware_selector"
            )
        with gr.Row():
            markdown_info = gr.Markdown("""
                select a middleware to see more info
            """)
        with gr.Row():
            config_code = gr.Code(
                value='',
                language='json',
                lines=5,
                label='config',
                interactive=True,
                show_label=True,
            )

        selected_middleware.change(
            fn=handle_middleware_select_change,
            inputs=selected_middleware,
            outputs=[markdown_info, config_code]
        )

        return [
            selected_middleware,
            config_code
        ]

    def run(self, p, selected_middleware=None, config_code=None):
        if selected_middleware is None or selected_middleware == "":
            errors.report(f"Middleware is required", exc_info=True)
            return

        config = {}
        if config_code is not None:
            config = json.loads(config_code)

        middleware_class = get_middleware_class_from_str(selected_middleware)

        # Get the module where the middleware_class is defined
        module_name = middleware_class.__module__

        # Check if the module is in sys.modules, if not, you'll need to import it first (based on your comment)
        if module_name not in sys.modules:
            __import__(module_name)

        # Now, reload the module
        module = sys.modules[module_name]
        importlib.reload(module)

        # Fetch the updated middleware_class from the reloaded module
        middleware_class = getattr(module, middleware_class.__name__)

        # run middleware
        middleware_instance = middleware_class(config)
        return middleware_instance.run(p)
