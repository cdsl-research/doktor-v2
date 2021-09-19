import glob
import json
import importlib

from fastapi.openapi.utils import get_openapi


def main():
    import os
    import sys
    parent_dir = os.path.join(os.path.dirname(__file__), '..')
    sys.path.append(parent_dir)
    dir_list_mainpy = glob.glob(parent_dir + "/*/main.py")
    dir_names = set(map(lambda x: x.split("/")[-2], dir_list_mainpy))

    for mod_name in dir_names:
        full_mod_name = f"{mod_name}.main"
        mod_main = importlib.import_module(full_mod_name)
        app = mod_main.app

        with open(f"openapi_{mod_name}.json", 'w') as f:
            json.dump(get_openapi(
                title=app.title,
                version=app.version,
                openapi_version=app.openapi_version,
                description=app.description,
                routes=app.routes,
            ), f)


if __name__ == "__main__":
    main()
