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
        if child is not None:
            self._children.append(child)

    def pretty_print(self, indent=4, depth=0):
        result = ""
        result += "{}[{}:{}] {}".format(
            indent * depth * " ",
            self.origin.line, self.origin.column,
            str(self)
        )
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


class CommentNode(Node):

    def __init__(self, origin, comment):
        super().__init__(origin)
        self._comment = comment

    @property
    def comment(self):
        return self._comment

    def __str__(self):
        return "comment node: '{}'".format(self._comment)


class ObjectNode(Node):

    def __init__(self, origin, name, parent_name):
        super().__init__(origin)
        self._name = name
        self._parent_name = parent_name

    @property
    def name(self):
        return self._name

    @property
    def parent_name(self):
        return self._parent_name

    def __str__(self):
        if self.parent_name is None:
            parent_name = ""
        else:
            parent_name = " inherits from '{}'".format(self.parent_name)
        return "object '{}'{}".format(self.name, parent_name)


class EventNode(Node):

    def __init__(self, origin, event_name):
        super().__init__(origin)
        self._event_name = event_name

    @property
    def event_name(self):
        return self._event_name

    def __str__(self):
        return "event handler '{}'".format(self.event_name)
