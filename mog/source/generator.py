"""
this module provides the automatic code generation for mog's custom language
"""


import os.path


def generate_object_path(base_path, gm_object):
    return os.path.join(base_path, gm_object.name + ".mog")


def generate_object_file(base_path, gm_object):
    file = open(generate_object_path(base_path, gm_object), 'w')
    writeln = lambda x: file.write("{}\n".format(x))

    parent = gm_object.parent_name
    if parent is None:
        inherited = ""
    else:
        inherited = ": {} ".format(parent)

    writeln("# file auto generated from GM object {}".format(gm_object.name))
    writeln("")
    writeln("object {} {}{{".format(gm_object.name, inherited))
    for event in gm_object.events:
        writeln("    event {} {{".format(event.type_name))
        writeln("    }")
    writeln("}")
