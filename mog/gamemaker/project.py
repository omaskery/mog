"""
this module provides functionality for parsing a game maker project file
"""


import xml.etree.ElementTree as etree
import os


class Project(object):
    """Represents a Game Maker project"""

    def __init__(self, basepath):
        self._basepath = basepath
        self._contents = etree.parse(Project.path_from_base(self._basepath))

    @property
    def objects(self):
        return list(map(lambda x: GameObject.from_xml_element(self._basepath, x), self._fetch_assets(".//object")))

    def _fetch_assets(self, asset_type):
        return self._contents.findall(asset_type)

    @staticmethod
    def name_from_path(basepath):
        return os.path.split(basepath)[-1].split(".")[0]

    @staticmethod
    def path_from_base(basepath):
        filename = "{}.project.gmx".format(Project.name_from_path(basepath))
        return os.path.join(basepath, filename)


class GameObject(object):
    """Represents an 'object' from a Game Maker project"""

    def __init__(self, name, path):
        self._name = name
        self._path = path
        self._contents = etree.parse(self._path)

    @staticmethod
    def from_xml_element(basepath, elem):
        path = os.path.join(basepath, elem.text) + ".object.gmx"
        name = os.path.split(elem.text)[-1]
        return GameObject(name, path)

    @property
    def events(self):
        return list(map(lambda elem: GameObjectEvent.from_xml_element(elem, self), self._contents.findall(".//event")))

    @property
    def name(self):
        return self._name

    @property
    def path(self):
        return self._path

    def __str__(self):
        return "GameObject({})".format(self._name)

    def __repr__(self):
        return str(self)


class GameObjectEvent(object):
    """Represents an 'event' from an 'object' in Game Maker"""

    def __init__(self, parent, event_type, event_number, actions):
        self._parent_object = parent
        self._event_type = event_type
        self._event_number = event_number
        self._actions = actions

    @staticmethod
    def from_xml_element(elem, parent):
        event = GameObjectEvent(
            parent,
            int(elem.attrib['eventtype']),
            int(elem.attrib['enumb']),
            elem.findall('.//action')
        )
        return event

    @property
    def code_actions(self):
        def code_only(elem):
            return elem.find('id').text == '603' and elem.find('kind').text == '7'

        def code_map(elem):
            return {
                'whoName': elem.find('whoName').text,
                'code': elem.find('arguments').find('argument').find('string').text,
            }

        return list(map(code_map, filter(code_only, self._actions)))

    @property
    def parent(self):
        return self._parent_object

    @property
    def type(self):
        return self._event_type

    @property
    def type_name(self):
        return event_type_string(self.type)

    @property
    def number(self):
        return self._event_number

    def __str__(self):
        return "{}.Event({}, {})".format(self.parent, self.type_name, self.number)

    def __repr__(self):
        return str(self)


# based on manually editing *.object.gml file to have events with these numbers, fun!
EVENT_TYPE_CREATE = 0
EVENT_TYPE_DESTROY = 1
EVENT_TYPE_ALARM = 2
EVENT_TYPE_STEP = 3
EVENT_TYPE_COLLISION = 4
EVENT_TYPE_KEYBOARD = 5
EVENT_TYPE_MOUSE = 6
EVENT_TYPE_OTHER = 7
EVENT_TYPE_DRAW = 8
EVENT_TYPE_KEYPRESS = 9
EVENT_TYPE_KEYRELEASE = 10
EVENT_TYPE_TRIGGER = 11  # deprecated


def event_type_string(event_type):
    """Returns a string describing the event type integer"""
    return {
        EVENT_TYPE_CREATE: 'create',
        EVENT_TYPE_DESTROY: 'destroy',
        EVENT_TYPE_STEP: 'step',
        EVENT_TYPE_ALARM: 'alarm',
        EVENT_TYPE_KEYBOARD: 'keyboard',
        EVENT_TYPE_MOUSE: 'mouse',
        EVENT_TYPE_COLLISION: 'collision',
        EVENT_TYPE_OTHER: 'other',
        EVENT_TYPE_DRAW: 'draw',
        EVENT_TYPE_KEYPRESS: 'keypress',
        EVENT_TYPE_KEYRELEASE: 'keyrelease',
        EVENT_TYPE_TRIGGER: 'trigger',
    }[event_type]
