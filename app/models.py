import importlib
import pkgutil

import app

for finder, name, ispkg in pkgutil.walk_packages(app.__path__, app.__name__ + "."):
    if name.endswith(".model"):
        importlib.import_module(name)
