"""
Utilities for parsing command line arguments in main
"""


import argparse
import os


def is_gm_project_folder(path):
    if os.path.isdir(path):
        absolute = os.path.abspath(path)
        # is this a valid assertion? I hope so.
        if absolute.endswith(".gmx"):
            return absolute
        else:
            raise argparse.ArgumentTypeError("directory not a GML project")
    else:
        raise argparse.ArgumentTypeError("path not a valid directory")
