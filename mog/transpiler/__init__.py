"""
this package provides the the custom language transpiling within mog
"""


from .. import gamemaker
from ..source import ast as astree
from collections import namedtuple


class TranspilerMessage(namedtuple('TranspilerMessage', 'type contents origin')):

    VERBOSE = 0
    INFO = 1
    WARNING = 2
    ERROR = 3
    FATAL_ERROR = 4

    def __str__(self):
        return "{} [line {}, char {}] {}: {}".format(
            TranspilerMessage.message_type_string(self.type),
            self.origin.line + 1, self.origin.column + 1,
            self.origin.source_name,
            self.contents
        )

    @staticmethod
    def message_type_string(message_type):
        return {
            TranspilerMessage.VERBOSE: 'VERBOSE',
            TranspilerMessage.INFO: 'INFO',
            TranspilerMessage.WARNING: 'WARNING',
            TranspilerMessage.ERROR: 'ERROR',
            TranspilerMessage.FATAL_ERROR: 'FATAL_ERROR'
        }[message_type]


class FatalTranspilerError(Exception):

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


class DeclarationInfo(object):

    def __init__(self, name, ast):
        self._name = name
        self._ast = ast

    @property
    def name(self):
        return self._name

    @property
    def origin(self):
        return self._ast.origin.clone()

    @property
    def ast(self):
        return self._ast


class Type(object):

    def __init__(self, name):
        self._name = name

    @property
    def name(self):
        return self._name

    def __str__(self):
        return "type '{}'".format(self.name)


class RecordType(Type):

    def __init__(self, name, origin):
        super().__init__(name)
        self._origin = origin
        self._members = {}
        self._methods = {}
        self._parent = None

    def set_parent(self, parent):
        self._parent = parent

    @property
    def parent(self):
        return self._parent

    @property
    def origin(self):
        return self._origin.clone()

    @property
    def member_names(self):
        return self._members.keys()

    def member_info(self, field_name):
        return self._members[field_name]

    def add_member(self, field_info):
        self._members[field_info.name] = field_info

    @property
    def method_names(self):
        return self._methods.keys()

    def method_info(self, method_name):
        return self._methods[method_name]

    def add_method(self, method_info):
        self._methods[method_info.name] = method_info

    def __str__(self):
        parent = ""
        fields = ""
        methods = ""
        if self.parent is not None:
            parent = " parent: {}".format(self.parent.name)
        if len(self._members) > 0:
            fields = "fields: {}".format(", ".join(self.member_names))
        if len(self._methods) > 0:
            methods = "methods: {}".format(", ".join(self.method_names))
        details = ""
        if fields != "" or methods != "":
            details = " ({})".format(", ".join([
                text
                for text in [fields, methods]
                if text != ""
            ]))
        return "record type '{}'{}{}".format(
            self.name,
            parent,
            details
        )


class EventDeclarationInfo(DeclarationInfo):

    def __init__(self, name, ast):
        super().__init__(name, ast)


class MethodDeclarationInfo(DeclarationInfo):

    def __init__(self, name, ast):
        super().__init__(name, ast)


class MemberDeclarationInfo(DeclarationInfo):

    def __init__(self, name, ast):
        super().__init__(name, ast)


class ObjectType(RecordType):

    def __init__(self, name, origin):
        super().__init__(name, origin)
        self._events = {}

    @property
    def event_names(self):
        return self._events.keys()

    def event_info(self, event_name):
        return self._events[event_name]

    def add_event(self, event_info):
        self._events[event_info.name] = event_info

    def __str__(self):
        parent = ""
        fields = ""
        methods = ""
        events = ""
        if self.parent is not None:
            parent = " parent: {}".format(self.parent.name)
        if len(self._members) > 0:
            fields = "fields: {}".format(", ".join(self.member_names))
        if len(self._methods) > 0:
            methods = "methods: {}".format(", ".join(self.method_names))
        if len(self._events) > 0:
            events = "events: {}".format(", ".join(self.event_names))
        details = ""
        if fields != "" or methods != "" or events != "":
            details = " ({})".format(", ".join([
                text
                for text in [fields, methods, events]
                if text != ""
            ]))
        return "object type '{}'{}{}".format(
            self.name,
            parent,
            details
        )


class Transpiler(object):

    def __init__(self, project_name):
        self._ast = astree.RootNode("mog project '{}'".format(project_name))
        self._messages = []
        self._types = {}
        self._delayed = {}
        self._stage_order = [
            'object-parenting',
        ]
        for stage in self._stage_order:
            self._delayed[stage] = []

    def _register_delay(self, stage_name, callback):
        if stage_name not in self._delayed:
            self._delayed[stage_name] = []
        self._delayed[stage_name].append(callback)

    def _trigger_delays(self, stage_name, *args):
        for delay in self._delayed[stage_name]:
            delay(*args)

    def _delay_object_parenting(self, callback):
        self._register_delay('object-parenting', callback)

    @property
    def messages(self):
        return self._messages

    def report(self, message_type, contents, origin):
        self._messages.append(TranspilerMessage(message_type, contents, origin.clone()))

    def verbose(self, contents, origin):
        self.report(TranspilerMessage.VERBOSE, contents, origin)

    def info(self, contents, origin):
        self.report(TranspilerMessage.INFO, contents, origin)

    def warn(self, contents, origin):
        self.report(TranspilerMessage.WARNING, contents, origin)

    def error(self, contents, origin):
        self.report(TranspilerMessage.ERROR, contents, origin)

    def fatal_error(self, contents, origin):
        raise FatalTranspilerError(contents, origin)

    def _fatal_error(self, contents, origin):
        self.report(TranspilerMessage.FATAL_ERROR, contents, origin)

    def is_success(self):
        return all([
            message.type not in (TranspilerMessage.ERROR, TranspilerMessage.FATAL_ERROR)
            for message in self.messages
        ])

    def _parent_objects(self, child, parent_name):
        if parent_name in self._types and isinstance(self._types[parent_name], ObjectType):
            child.set_parent(self._types[parent_name])
        else:
            self.error("parent type {} does not exist".format(parent_name), child.origin)

    def ingest_event_definition(self, parent, event_ast):
        if event_ast.event_name in parent.event_names:
            self.error("object {} already has event definition for {} at {}".format(
                parent.name, event_ast.event_name, parent.event_info(event_ast.event_name).origin
            ), event_ast.origin)
        else:
            parent.add_event(EventDeclarationInfo(event_ast.event_name, event_ast))

    def _ingest_method_definition(self, parent, method_ast):
        if method_ast.name in parent.method_names:
            self.error("object {} already has method definition for {} at {}".format(
                parent.name, method_ast.name, parent.method_info(method_ast.name).origin
            ), method_ast.origin)
        else:
            parent.add_method(MethodDeclarationInfo(method_ast.name, method_ast))

    def _ingest_member_definition(self, parent, member_ast):
        if member_ast.name in parent.member_names:
            self.error("object {} already has method definition for {} at {}".format(
                parent.name, member_ast.name, parent.method_info(member_ast.name).origin
            ), member_ast.origin)
        else:
            parent.add_member(MemberDeclarationInfo(member_ast.name, member_ast))

    def _ingest_object_definition(self, object_ast):
        obj = ObjectType(object_ast.name, object_ast.origin)
        if obj.name in self._types:
            existing_definition = self._types[obj.name].origin
            self.error("object with name {} already defined at {}".format(existing_definition), object_ast.origin)
        else:
            self._types[obj.name] = obj
            if object_ast.parent_name is not None:
                self._delay_object_parenting(lambda transpiler: transpiler._parent_objects(obj, object_ast.parent_name))
            for child in object_ast.children:
                if isinstance(child, astree.EventNode):
                    self.ingest_event_definition(obj, child)
                elif isinstance(child, astree.MethodNode):
                    self._ingest_method_definition(obj, child)
                elif isinstance(child, astree.MemberNode):
                    self._ingest_member_definition(obj, child)

    def identify_types_in(self, ast):
        for child in ast.children:
            if isinstance(child, astree.ObjectNode):
                self._ingest_object_definition(child)

    def ingest_ast(self, ast):
        for child in ast.children:
            self._ast.add(child)

    def _compile_expression(self, origin, type_ast, value_ast):
        if type_ast is None:
            self.error("member missing type information", origin)
        else:
            

    def _compile_code(self, this_obj, is_create_event, ast, comment):
        result = "///{}\n".format(comment)
        result += "// automatically generated by mog\n"

        if is_create_event:
            result += "\n// initialising member variables\n"
            for member_name in this_obj.member_names:
                member_info = this_obj.member_info(member_name)
                expression = self._compile_expression(member_info.origin, member_info.ast.type, member_info.ast.value)
                if expression is not None:
                    result += "{} = {}\n".format(
                        member_name, expression
                    )

        return result

    def _compile_object(self, obj, gm_project):
        gm_object = gm_project.create_or_fetch_object(obj.name)
        for event_name in obj.event_names:
            event_decl = obj.event_info(event_name)
            if event_name not in EVENT_NAME_MAPPING:
                self.error("'{}' is not a valid event name".format(event_name), event_decl.origin)
                continue
            event_type, event_number = EVENT_NAME_MAPPING[event_name]
            gm_event = gm_object.create_or_fetch_event(event_type, event_number)
            code = self._compile_code(obj, event_name == "create", event_decl.ast.code_block, event_name)
            gm_event.set_code_action(code)
        gm_object.save()

    def _compile_objects(self, gm_project):
        for obj in self._types.values():
            if not isinstance(obj, ObjectType):
                continue
            self._compile_object(obj, gm_project)

    def compile(self, gm_project):
        try:
            self.identify_types_in(self._ast)
            self._trigger_delays('object-parenting', self)
            self._compile_objects(gm_project)
        except FatalTranspilerError as err:
            self._fatal_error(err.contents, err.origin)

    def debug_types(self):
        print("debug transpiler type information:")
        for info in self._types.values():
            print("  {}".format(info))


EVENT_NAME_MAPPING = {
    'create': (gamemaker.project.EVENT_TYPE_CREATE, 0),
    'destroy': (gamemaker.project.EVENT_TYPE_DESTROY, 0),
    'step': (gamemaker.project.EVENT_TYPE_STEP, 0),
}
