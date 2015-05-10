"""
this module provides the code source abstraction (for reading source code in)
"""


import copy


class SourcePoint(object):

    def __init__(self, source_name, line=0, column=0):
        self._source_name = source_name
        self._line = line
        self._column = column

    @property
    def source_name(self):
        return self._source_name

    @property
    def line(self):
        return self._line

    @property
    def column(self):
        return self._column

    def clone(self):
        return copy.copy(self)

    def advance_by(self, letter):
        if letter == '\n':
            self._line += 1
            self._column = 0
            result = True
        else:
            self._column += 1
            result = False
        return result

    def rewind_by(self, letter, last_column=0):
        if letter == '\n':
            self._column = last_column
            self._line -= 1
        else:
            self._column -= 1


class AbstractSource(object):

    def __init__(self, source_name):
        self._position = SourcePoint(source_name)
        self._buffered = ""

    def _read(self, amount):
        _ = self, amount
        raise RuntimeError("abstract read not implemented")

    def _fill_buffer(self, capacity=1024):
        missing = capacity - len(self._buffered)
        if missing > 0:
            self._buffered += self._read(missing)

    @property
    def position(self):
        return self._position.clone()

    @property
    def source_name(self):
        return self.position.source_name

    def is_eof(self):
        self._fill_buffer()
        return len(self._buffered) < 1

    def peek(self):
        self._fill_buffer()
        if len(self._buffered) > 0:
            result = self._buffered[0]
        else:
            result = None
        return result

    def get(self):
        result = self.peek()
        if result is not None:
            self._position.advance_by(result)
            self._buffered = self._buffered[1:]
        return result

    def put(self, contents):
        for letter in contents:
            self._position.rewind_by(letter)
        self._buffered = contents + self._buffered


class TextSource(AbstractSource):

    def __init__(self, text, source_name="<text source>"):
        super().__init__(source_name)
        self._text = text.encode()

    def _read(self, amount):
        result = self._text[:amount]
        self._text = self._text[amount:]
        return result


class FileSource(AbstractSource):

    def __init__(self, file, filename):
        super().__init__("file '{}'".format(filename))
        self._file = file

    def _read(self, amount):
        return self._file.read(amount)
