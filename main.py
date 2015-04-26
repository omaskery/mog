#!/usr/bin/env python3
"""
mog (My Own Game-Maker-Language) is a little experiment into producing GML code from a made up language
"""


import argparse
import mog
import os


def main():
    args = parse_args()
    args.func(args)


def mog_init(args):
    project_path = os.path.join(args.path, args.name)

    if mog.project.Project.already_exists(project_path):
        print("a mog project already exists at that location")
        return

    project = mog.project.Project.create_new(project_path, args.name, args.gm_proj)


def mog_scan(args):
    if not mog.project.Project.already_exists(args.path):
        print("no mog project found in specified directory")
        return

    project = mog.project.Project(args.path)

    print("scanning '{}'".format(project.project_file.gamemaker_project_path))


def parse_args():
    parser = argparse.ArgumentParser(
        description="""mog (My Own Game-Maker-Language)
        an experiment into producing GML from a made up language"""
    )
    subparsers = parser.add_subparsers(dest="mode", help="the mode of operation")

    parser_init = subparsers.add_parser(
        'init', help='initialises a new mog project'
    )
    parser_init.add_argument(
        'name', help='the name of the project and the folder to create'
    )
    parser_init.add_argument(
        'gm_proj', type=mog.arg_helpers.is_gm_project_folder, metavar="gm-proj",
        help='the path to the associated game maker project'
    )
    parser_init.add_argument(
        '--path', default='.',
        help='the path to create the project in, defaults to current directory'
    )
    parser_init.set_defaults(func=mog_init)

    parser_scan = subparsers.add_parser(
        'scan', help='scans the game maker project for new objects'
    )
    parser_scan.add_argument(
        '--path', default='.',
        help='the path of the directory containing the mog project'
    )
    parser_scan.set_defaults(func=mog_scan)

    return parser.parse_args()


if __name__ == "__main__":
    main()
