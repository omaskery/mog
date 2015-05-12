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
    """handles the `mog init` command"""

    project_path = os.path.join(args.path, args.name)

    if mog.project.Project.already_exists(project_path):
        print("a mog project already exists at that location")
        return

    project = mog.project.Project.create_new(project_path, args.name, args.gm_proj)

    # nothing else needs doing atm?
    _ = project


def mog_scan(args):
    """handles the `mog scan` command"""

    base_path = args.path

    if not mog.project.Project.already_exists(base_path):
        print("no mog project found in specified directory")
        return

    project = mog.project.Project(base_path)

    print("scanning game maker project {}...".format(project.project_file.gamemaker_project_path))
    gm_project = mog.gamemaker.project.Project(project.project_file.gamemaker_project_path)
    for object in gm_project.objects:
        object_path = mog.source.generator.generate_object_path(base_path, object)
        if not os.path.exists(object_path):
            print("  generating mog file for game maker object {}".format(object.name))
            mog.source.generator.generate_object_file(base_path, object)
        else:
            parse_result = mog.source.parser.parse(open(object_path, 'r'), object_path)
            print("  existing mog file:\n    ast:\n{}".format(parse_result.ast.pretty_print(3, 2)))
            if len(parse_result.messages) > 0:
                print("    parser output:")
                for message in parse_result.messages:
                    print("      {}".format(message))


def mog_build(args):
    """handles the `mog build` command"""

    base_path = args.path

    if not mog.project.Project.already_exists(base_path):
        print("no mog project found in specified directory")
        return

    project = mog.project.Project(base_path)
    project_name = project.project_file.project_name
    parser_success = True

    transpiler = mog.transpiler.Transpiler(project_name)
    for filename in filter(lambda x: x.endswith(".mog"), os.listdir(base_path)):
        filepath = os.path.join(base_path, filename)
        parse_result = mog.source.parser.parse(open(filepath, 'r'), filename)
        print("  ast:")
        print(parse_result.ast.pretty_print(4, 1))
        for message in parse_result.messages:
            print("  parser - {}".format(message))
        if parse_result.is_success():
            transpiler.ingest_ast(parse_result.ast)
        else:
            parser_success = False

    transpiler.compile()
    for message in transpiler.messages:
        print("  compiler - {}".format(message))

    transpiler.debug_types()

    if parser_success and transpiler.is_success():
        # print("build success")
        pass
    else:
        print("build unsuccessful")


def parse_args():
    """configures the argument parser and parses the command line arguments"""

    parser = argparse.ArgumentParser(
        description="""mog (My Own Game-Maker-Language)
        an experiment into producing GML from a made up language"""
    )
    subparsers = parser.add_subparsers(dest="mode", help="the mode of operation")

    # mog init
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

    # mog scan
    parser_scan = subparsers.add_parser(
        'scan', help='scans the game maker project for new objects'
    )
    parser_scan.add_argument(
        '--path', default='.',
        help='the path of the directory containing the mog project'
    )
    parser_scan.set_defaults(func=mog_scan)

    # mog build
    parser_build = subparsers.add_parser(
        'build', help='builds the mog project'
    )
    parser_build.add_argument(
        '--path', default='.',
        help='the path of the directory containing the mog project'
    )
    parser_build.set_defaults(func=mog_build)

    # go go go
    return parser.parse_args()


if __name__ == "__main__":
    main()
