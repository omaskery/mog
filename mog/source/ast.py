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

    def pop(self):
        result = self._children[-1]
        self._children = self._children[:-1]
        return result

    def pop_many(self, n):
        result = self._children[-n:]
        self._children = self._children[:-n]
        return result

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


class FunctionCall(Node):

    def __init__(self, origin, function_name):
        super().__init__(origin)
        self._function_name = function_name

    @property
    def function_name(self):
        return self._function_name

    def __str__(self):
        return "function call '{}'".format(self.function_name)


class IdentifierNode(Node):

    def __init__(self, origin, name):
        super().__init__(origin)
        self._name = name

    @property
    def name(self):
        return self._name

    def __str__(self):
        return "identifier '{}'".format(self.name)


class LiteralNode(Node):

    def __init__(self, origin, typename, value):
        super().__init__(origin)
        self._typename = typename
        self._value = value

    @property
    def typename(self):
        return self._typename

    @property
    def value(self):
        return self._value

    def __str__(self):
        return "{} literal '{}'".format(self.typename, self.value)


class NumericLiteralNode(LiteralNode):

    def __init__(self, origin, value):
        super().__init__(origin, "real", value)


class StringLiteralNode(LiteralNode):

    def __init__(self, origin, value):
        super().__init__(origin, "string", value)


class OperatorNode(Node):

    def __init__(self, origin, operator, priority, operand_count=2):
        super().__init__(origin)
        self._operator = operator
        self._priority = priority
        self._operand_count = operand_count

    @property
    def operator(self):
        return self._operator

    @property
    def priority(self):
        return self._priority

    @property
    def operand_count(self):
        return self._operand_count

    def pop_operands(self, output_stack):
        operands = output_stack.pop_many(self.operand_count)
        for operand in operands:
            self.add(operand)

    def __str__(self):
        return "operator {}".format(self.operator)


class ParameterList(Node):

    def __init__(self, origin):
        super().__init__(origin)

    def __str__(self):
        return "parameter list"