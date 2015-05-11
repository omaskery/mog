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
        return "{} [line {}, char {}]: {}".format(
            ParserMessage.message_type_string(self.type),
            self.origin.line + 1, self.origin.column + 1,
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
        self.first = True

    def __call__(self, char):
        allowed = string.ascii_letters + "_"
        if not self.first:
            allowed += string.digits
        self.first = False
        return char in allowed


class Parser(object):

    COMMENT_CHARACTER = '#'

    def __init__(self, src):
        self._result = ParserResult(src.source_name)
        self._src = src

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

    def recover_scoped(self, scope_open, scope_close, message, initial_scope = 1):
        scope = initial_scope
        while self.peek() is not None:
            next = self.get()
            if next == scope_open:
                scope += 1
            elif next == scope_close:
                scope -= 1
                if scope <= 0:
                    self.info(message)
                    break

    def parse_method_body(self, parent):
        self.skip_whitespace()
        if self.peek() != '{':
            self.error("expected '{' symbol")
            self.recover_scoped('{', '}', "attempting to resume parsing after bad function body")
        else:
            self.get()
            self.skip_whitespace()
            while self.peek() != '}':
                self.skip_whitespace()
            self.get()

    def parse_method(self, parent, start_position):
        pass

    def parse_member(self, parent, start_position):
        pass

    def parse_event(self, parent, start_position):
        event_name = self.parse_identifier()
        self.skip_whitespace()
        result = ast.EventNode(start_position, event_name)
        self.parse_method_body(result)
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
            self.recover_scoped('{', '}', "attempting to resume parsing after bad object definition")
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
                    self.recover_scoped("{", "}", "attempting to resume parsing after bad method/member/event definition", 0)
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
