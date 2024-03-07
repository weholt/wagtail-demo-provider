import os

import djclick as click
from django.apps import apps
from django.db import DatabaseError, transaction


@click.command()
def run_demo_providers():
    with transaction.atomic():
        try:
            for app in [app for app in apps.get_app_configs()]:
                app_folder = os.path.split(app.module.__file__)[0]
                if os.path.exists(os.path.join(app_folder, "demo.py")):
                    try:
                        getattr(__import__("%s.%s" % (app.name, "demo")).demo, "run")()
                    except ImportError as ex:
                        print(f"Skipping demo from {app.name}: {ex}")
        except DatabaseError as ex:
            print(f"Demo process aborted: {ex}")
