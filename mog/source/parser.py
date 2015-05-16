"""
this module provides the parsing for mog's custom language
"""


from collections import namedtuple
from . import source
from . import ast
import string


class ParserMessage(namedtuple('ParserMessage', 'type contents origin')):

    VERBOSE = 0
    INFO = 1
    WARNING = 2
    ERROR = 3
    FATAL_ERROR = 4

    def __str__(self):
        return "{} [line {}, char {}] {}: {}".format(
            ParserMessage.message_type_string(self.type),
            self.origin.line + 1, self.origin.column + 1,
            self.origin.source_name,
            self.contents
        )

    @staticmethod
    def message_type_string(message_type):
        return {
            ParserMessage.VERBOSE: 'VERBOSE',
            ParserMessage.INFO: 'INFO',
            ParserMessage.WARNING: 'WARNING',
            ParserMessage.ERROR: 'ERROR',
            ParserMessage.FATAL_ERROR: 'FATAL_ERROR'
        }[message_type]


class FatalParserError(Exception):

    def __init__(self, contents, origin):
        super().__init__()
        self._contents = contents
        self._origin = origin

    @property
    def contents(self):
        return self._contents

    @property
    def origin(self):
        return self._origin


class IdentifierPredicate(object):

    def __init__(self):
        self._first = True

    def __call__(self, char):
        allowed = string.ascii_letters + "_"
        if not self._first:
            allowed += string.digits
        self._first = False
        return char in allowed


class StringLiteralPredicate(object):

    def __init__(self):
        self._ignore = False

    def __call__(self, char):
        if not self._ignore:
            if char == '\\':
                self._ignore = True
            result = char != '"'
        else:
            self._ignore = False
            result = True
        return result


class Parser(object):

    COMMENT_CHARACTER = '#'

    def __init__(self, src):
        self._result = ParserResult(src.source_name)
        self._src = src
        self._operators = {
            '&&': 5,
            '||': 5,
            '==': 10,
            '!=': 10,
            '<': 20,
            '>': 20,
            '<=': 20,
            '>=': 20,
            '+': 50,
            '-': 50,
            '*': 100,
            '/': 100,
        }

    @property
    def position(self):
        return self._src.position

    def verbose(self, contents, origin=None):
        if origin is None:
            origin = self.position
        self._result.verbose(contents, origin)

    def info(self, contents, origin=None):
        if origin is None:
            origin = self.position
        self._result.info(contents, origin)

    def warn(self, contents, origin=None):
        if origin is None:
            origin = self.position
        self._result.warn(contents, origin)

    def error(self, contents, origin=None):
        if origin is None:
            origin = self.position
        self._result.error(contents, origin)

    def fatal_error(self, contents, origin=None):
        if origin is None:
            origin = self.position
        raise FatalParserError(contents, origin)

    def skip_while(self, predicate, eof_allowed=False):
        self.consume_while(predicate, eof_allowed)

    def consume_while(self, predicate, eof_allowed=False):
        result = ""
        while self.peek() is not None and predicate(self.peek()):
            result += self._src.get()
        if self.peek() is None and not eof_allowed:
            self.fatal_error("unexpected EOF")
        return result

    def consume_until(self, predicate, eof_allowed=False):
        return self.consume_while(lambda x: not predicate(x), eof_allowed)

    def skip_expected_while(self, predicate, expected, eof_allowed=False):
        consumed = self.consume_while(predicate, eof_allowed)
        return consumed == expected

    def skip_whitespace(self, eof_allowed=False):
        def whitespace_predicate(char):
            return char in string.whitespace
        self.skip_while(whitespace_predicate, eof_allowed)

    def skip_expected_identifier(self, identifier, eof_allowed=False):
        return self.skip_expected_while(IdentifierPredicate(), identifier.encode(), eof_allowed)

    def parse_identifier(self, eof_allowed=False) -> str:
        self.skip_whitespace(eof_allowed)
        return self.consume_while(IdentifierPredicate(), eof_allowed)

    def parse_comment(self) -> ast.CommentNode:
        self.skip_whitespace()
        if self.peek() != Parser.COMMENT_CHARACTER:
            self.info("parse_comment called when no comment character found")
            result = None
        else:
            start_position = self.position
            comment = self.consume_until(lambda x: x == '\n', True)
            if self.peek() == '\n':
                self.get()
            result = ast.CommentNode(start_position, comment)
        return result

    def peek(self) -> str:
        return self._src.peek()

    def get(self) -> str:
        return self._src.get()

    def parse_type(self, parent):
        start_position = self.position
        typename = self.parse_identifier()
        if typename == "":
            self.error("expected an identifier")
        parent.add(ast.TypeNode(start_position, typename))

    def parse_let_statement(self, parent, start_position):
        self.skip_whitespace()
        name = self.parse_identifier()
        self.skip_whitespace()
        let_node = ast.LetNode(start_position, name)
        if self.peek() == ':':
            self.get()
            self.skip_whitespace()
            self.parse_type(let_node)
            self.skip_whitespace()
        if self.peek() != '=':
            self.error("expected '=' sign in let statement")
        else:
            self.get()
        self.parse_expression(let_node)
        parent.add(let_node)

    def parse_if_expression(self, parent, start_position):
        pass

    def parse_while_expression(self, parent, start_position):
        pass

    def parse_for_expression(self, parent, start_position):
        pass

    def parse_numeric_literal(self, parent):
        position = self.position
        result = self.consume_while(lambda x: x in string.digits)
        parent.add(ast.NumericLiteralNode(position, result))

    def parse_string_literal(self, parent):
        position = self.position
        if self.peek() != '"':
            self.error("expected '\"' at start of string literal")
        else:
            self.get()
        result = self.consume_while(StringLiteralPredicate())
        if self.peek() == '"':
            self.get()
        parent.add(ast.StringLiteralNode(position, result))

    def parse_operator(self) -> ast.OperatorNode:
        consumed = ""

        def start_of_operator(x):
            return any([
                operator.startswith(x)
                for operator in self._operators.keys()
            ])

        self.skip_whitespace()
        start_position = self.position
        while start_of_operator(consumed + self.peek()):
            consumed += self.get()

        if consumed not in self._operators.keys():
            result = None
        else:
            result = ast.OperatorNode(start_position, consumed, self._operators[consumed])

        return result

    def parse_expression(self, parent):
        self.skip_whitespace()

        output_stack = ast.Node(self.position)
        operator_stack = []
        expecting_operator = False
        value_expected = True
        finished = False

        while not finished:
            peeked = self.peek()
            if not expecting_operator:
                if peeked in string.digits:
                    self.parse_numeric_literal(output_stack)
                elif peeked == '"':
                    self.parse_string_literal(output_stack)
                elif IdentifierPredicate()(peeked):
                    identifier_start = self.position
                    identifier = self.parse_identifier()
                    self.skip_whitespace()
                    if self.peek() == '(':
                        self.parse_function_call(identifier, output_stack, identifier_start)
                    else:
                        output_stack.add(ast.IdentifierNode(identifier_start, identifier))
                else:
                    if value_expected:
                        self.error("expected another value after last operator")
                    finished = True
            else:
                operator = self.parse_operator()
                if operator is not None:
                    while len(operator_stack) > 0 and operator.priority < operator_stack[-1].priority:
                        popped = operator_stack[-1]
                        operator_stack = operator_stack[:-1]
                        popped.pop_operands(output_stack)
                        output_stack.add(popped)
                    operator_stack.append(operator)
                    value_expected = True
                else:
                    finished = True
            expecting_operator = not expecting_operator
            self.skip_whitespace()

        while len(operator_stack) > 0:
            popped = operator_stack[-1]
            operator_stack = operator_stack[:-1]
            popped.pop_operands(output_stack)
            output_stack.add(popped)

        if len(output_stack.children) != 1:
            self.error("internal error: shunting algorithm parsing expression resulted in non-1-length output stack")
        else:
            parent.add(output_stack.children[-1])

    def parse_function_call(self, identifier, parent, start_position):
        self.skip_whitespace()
        call = ast.FunctionCall(start_position, identifier)
        if self.peek() != '(':
            self.error("expected '(' for parameter list in function call")
        else:
            self.get()
        self.skip_whitespace()
        first = True
        parameter_list = ast.ParameterListNode(self.position)
        while self.peek() != ')':
            if not first:
                if self.peek() != ',':
                    self.error("expected ',' between parameters")
                else:
                    self.get()
            self.skip_whitespace()
            self.parse_expression(parameter_list)
            self.skip_whitespace()
            first = False
        self.get()
        call.add(parameter_list)
        parent.add(call)

    def parse_assignment(self, identifier, parent, start_position):
        if self.peek() != '=':
            self.error("expected '=' after identifier in assignment")
        else:
            self.get()
        self.skip_whitespace()
        assignment = ast.AssignmentNode(start_position, identifier)
        self.parse_expression(assignment)
        parent.add(assignment)

    def parse_statement(self, parent) -> bool:
        self.skip_whitespace()
        start_position = self.position
        identifier = self.parse_identifier()
        self.skip_whitespace()
        if identifier == 'let':
            self.parse_let_statement(parent, start_position)
        elif identifier == 'if':
            self.parse_if_expression(parent, start_position)
        elif identifier == 'while':
            self.parse_while_expression(parent, start_position)
        elif identifier == 'for':
            self.parse_for_expression(parent, start_position)
        elif self.peek() == '(':
            self.parse_function_call(identifier, parent, start_position)
        elif self.peek() == '=':
            self.parse_assignment(identifier, parent, start_position)
        self.skip_whitespace()
        if self.peek() == ';':
            self.get()
            as_expression = False
        else:
            as_expression = True
        return as_expression

    def parse_code_block(self, parent):
        as_expression = False
        self.skip_whitespace()
        code_block = ast.CodeBlock(self.position)
        if self.peek() != '{':
            self.error("expected '{' symbol")
        else:
            self.get()
        self.skip_whitespace()
        while self.peek() != '}':
            as_expression = self.parse_statement(code_block)
            self.skip_whitespace()
            if self.peek() != '}' and as_expression:
                self.error("a statement without a trailing ';' must be last statement in block")
        self.get()
        parent.add(code_block)
        return as_expression

    def parse_method(self, parent, start_position):
        self.skip_whitespace()
        name = self.parse_identifier()
        if name == "":
            self.error("expected identifier after method keyword")
        method = ast.MethodNode(start_position, name)
        self.skip_whitespace()
        parameters = ast.ParameterListNode(self.position)
        if self.peek() != '(':
            self.error("expected '(' after method name")
        else:
            self.get()
        self.skip_whitespace()
        first = True
        while self.peek() != ')':
            if not first:
                if self.peek() != ',':
                    self.error("expected ',' between parameters")
                else:
                    self.get()
            start_position = self.position
            name = self.parse_identifier()
            argument = ast.ParameterNode(start_position, name)
            if name == "":
                self.error("expected identifier to name parameter")
            else:
                self.skip_whitespace()
                if self.peek() != ':':
                    self.error("expected ':' after parameter name")
                else:
                    self.get()
                self.parse_type(argument)
            parameters.add(argument)
            first = False
            self.skip_whitespace()
        self.get()
        method.add(parameters)
        self.skip_whitespace()
        if self.peek() == ':':
            self.get()
            self.parse_type(method)
        self.parse_code_block(method)
        parent.add(method)

    def parse_member(self, parent, start_position):
        self.skip_whitespace()
        name = self.parse_identifier()
        self.skip_whitespace()
        member = ast.MemberNode(start_position, name)
        if self.peek() != ':':
            self.error("expected ':' identifier after member name")
        else:
            self.get()
        self.parse_type(member)
        self.skip_whitespace()
        if self.peek() == '=':
            self.get()
            self.parse_expression(member)
        self.skip_whitespace()
        if self.peek() != ';':
            self.error("expected ';' after member declaration")
        else:
            self.get()
        parent.add(member)

    def parse_event(self, parent, start_position):
        event_name = self.parse_identifier()
        self.skip_whitespace()
        result = ast.EventNode(start_position, event_name)
        self.parse_code_block(result)
        parent.add(result)

    def parse_object(self, parent, start_position):
        object_name = self.parse_identifier()
        self.skip_whitespace()
        if self.peek() == ':':
            self.get()
            parent_name = self.parse_identifier()
            self.skip_whitespace()
        else:
            parent_name = None

        if self.peek() != '{':
            self.error('expected "{" symbol')
        else:
            self.get()
        self.skip_whitespace()
        obj = ast.ObjectNode(start_position, object_name, parent_name)
        while self.peek() != '}':
            position = self.position
            identifier = self.parse_identifier()
            if identifier == 'method':
                self.parse_method(obj, position)
            elif identifier == 'member':
                self.parse_member(obj, position)
            elif identifier == 'event':
                self.parse_event(obj, position)
            else:
                self.error("unexpected identifier '{}'".format(identifier))
            self.skip_whitespace()
        if self.peek() == "}":
            self.get()
        parent.add(obj)

    def parse_global(self, parent):
        self.skip_whitespace(True)
        start_position = self.position.clone()
        peeked = self.peek()
        if peeked is None:
            pass
        elif peeked == '#':
            comment = self.parse_comment()
            parent.add(comment)
        elif IdentifierPredicate()(peeked):
            identifier = self.parse_identifier()
            if identifier == 'object':
                self.parse_object(parent, start_position)
        else:
            self.error("unexpected character '{}'".format(peeked))
            # try to recover on next line?
            self.consume_until(lambda x: x == '\n')
            if self.peek() == '\n':
                self.get()

    def parse(self):
        try:
            while not self._src.is_eof():
                self.parse_global(self._result.ast)
                self.skip_whitespace(True)
        except FatalParserError as err:
            self._result.fatal_error(err.contents, err.origin)
        return self._result


class ParserResult(object):

    def __init__(self, source_name):
        self._messages = []
        self._ast = ast.RootNode(source_name)

    @property
    def messages(self):
        return self._messages

    @property
    def ast(self):
        return self._ast

    def report(self, message_type, contents, origin):
        self._messages.append(ParserMessage(message_type, contents, origin.clone()))

    def verbose(self, contents, origin):
        self.report(ParserMessage.VERBOSE, contents, origin)

    def info(self, contents, origin):
        self.report(ParserMessage.INFO, contents, origin)

    def warn(self, contents, origin):
        self.report(ParserMessage.WARNING, contents, origin)

    def error(self, contents, origin):
        self.report(ParserMessage.ERROR, contents, origin)

    def fatal_error(self, contents, origin):
        self.report(ParserMessage.FATAL_ERROR, contents, origin)

    def is_success(self):
        return all([
            message.type not in (ParserMessage.ERROR, ParserMessage.FATAL_ERROR)
            for message in self.messages
        ])


def parse(file, filename):
    src = source.FileSource(file, filename)
    parser = Parser(src)
    return parser.parse()
