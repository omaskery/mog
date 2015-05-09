"""
this module provides the parsing for mog's custom language
"""


from collections import namedtuple
from . import source
from . import ast


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


class Parser(object):

    def __init__(self, src):
        self._result = ParserResult(src.source_name)
        self._src = src

    def verbose(self, contents, origin=None):
        if origin is None:
            origin = self._src.position
        self._result.verbose(contents, origin)

    def info(self, contents, origin=None):
        if origin is None:
            origin = self._src.position
        self._result.info(contents, origin)

    def warning(self, contents, origin=None):
        if origin is None:
            origin = self._src.position
        self._result.warn(contents, origin)

    def error(self, contents, origin=None):
        if origin is None:
            origin = self._src.position
        self._result.error(contents, origin)

    def fatal_error(self, contents, origin=None):
        if origin is None:
            origin = self._src.position
        self._result.fatal_error(contents, origin)

    def parse(self):
        self.fatal_error('parser unimplemented')
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
        self._messages.append(ParserMessage(message_type, contents, origin))

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


def parse(file, filename):
    src = source.FileSource(file, filename)
    parser = Parser(src)
    return parser.parse()
