"""
this module provides the abstract syntax tree for mog's custom language
"""


from . import source


class Node(object):

    def __init__(self, origin):
        self._origin = origin
        self._children = []

    @property
    def origin(self):
        return self._origin

    @property
    def children(self):
        return self._children

    def add(self, child):
        self._children.append(child)

    def pretty_print(self, indent=4, depth=0):
        result = ""
        result += "{}{}".format(indent * depth * " ", str(self))
        for child in self.children:
            result += "\n" + child.pretty_print(indent, depth + 1)
        return result


class RootNode(Node):

    def __init__(self, source_name):
        super().__init__(source.SourcePoint(source_name, 0, 0))

    @property
    def source_name(self):
        return self.origin.source_name

    def __str__(self):
        return "root node of source {}".format(self.source_name)
