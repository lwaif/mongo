# Copyright (C) 2018-present MongoDB, Inc.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the Server Side Public License, version 1,
# as published by MongoDB, Inc.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# Server Side Public License for more details.
#
# You should have received a copy of the Server Side Public License
# along with this program. If not, see
# <http://www.mongodb.com/licensing/server-side-public-license>.
#
# As a special exception, the copyright holders give permission to link the
# code of portions of this program with the OpenSSL library under certain
# conditions as described in each individual source file and distribute
# linked combinations including the program with the OpenSSL library. You
# must comply with the Server Side Public License in all respects for
# all of the code used other than as permitted herein. If you modify file(s)
# with this exception, you may extend this exception to your version of the
# file(s), but you are not obligated to do so. If you do not wish to do so,
# delete this exception statement from your version. If you delete this
# exception statement from all source files in the program, then also delete
# it in the license file.
#
"""
IDL AST classes.

Represents the derived IDL specification after type resolution in the binding pass has occurred.

This is a lossy translation from the IDL Syntax tree as the IDL AST only contains information about
the enums and structs that need code generated for them, and just enough information to do that.
"""

from __future__ import absolute_import, print_function, unicode_literals

from typing import List, Union, Any, Optional, Tuple

from . import common
from . import errors


class IDLBoundSpec(object):
    """A bound IDL document or a set of errors if parsing failed."""

    def __init__(self, spec, error_collection):
        # type: (IDLAST, errors.ParserErrorCollection) -> None
        """Must specify either an IDL document or errors, not both."""
        assert (spec is None and error_collection is not None) or (spec is not None
                                                                   and error_collection is None)
        self.spec = spec
        self.errors = error_collection


class IDLAST(object):
    """The in-memory representation of an IDL file."""

    def __init__(self):
        # type: () -> None
        """Construct an IDLAST."""
        self.globals = None  # type: Global

        self.commands = []  # type: List[Command]
        self.enums = []  # type: List[Enum]
        self.structs = []  # type: List[Struct]

        self.server_parameters = []  # type: List[ServerParameter]
        self.configs = []  # type: List[ConfigOption]


class Global(common.SourceLocation):
    """
    IDL global object container.

    cpp_namespace and cpp_includes are only populated if the IDL document contains these YAML nodes.
    """

    def __init__(self, file_name, line, column):
        # type: (unicode, int, int) -> None
        """Construct a Global."""
        self.cpp_namespace = None  # type: unicode
        self.cpp_includes = []  # type: List[unicode]
        self.configs = None  # type: ConfigGlobal

        super(Global, self).__init__(file_name, line, column)


class Struct(common.SourceLocation):
    """
    IDL struct information.

    All fields are either required or have a non-None default.
    """

    # pylint: disable=too-many-instance-attributes

    def __init__(self, file_name, line, column):
        # type: (unicode, int, int) -> None
        """Construct a struct."""
        self.name = None  # type: unicode
        self.cpp_name = None  # type: unicode
        self.description = None  # type: unicode
        self.strict = True  # type: bool
        self.immutable = False  # type: bool
        self.inline_chained_structs = False  # type: bool
        self.generate_comparison_operators = False  # type: bool
        self.fields = []  # type: List[Field]
        super(Struct, self).__init__(file_name, line, column)


class Validator(common.SourceLocation):
    """
    An instance of a validator for a field.

    The validator must include at least one of the defined validation predicates.
    If more than one is included, they must ALL evaluate to true.
    """

    # pylint: disable=too-many-instance-attributes

    def __init__(self, file_name, line, column):
        # type: (unicode, int, int) -> None
        """Construct a Validator."""
        # Don't lint gt/lt as bad attribute names.
        # pylint: disable=C0103
        self.gt = None  # type: Optional[Union[int, float]]
        self.lt = None  # type: Optional[Union[int, float]]
        self.gte = None  # type: Optional[Union[int, float]]
        self.lte = None  # type: Optional[Union[int, float]]
        self.callback = None  # type: Optional[unicode]

        super(Validator, self).__init__(file_name, line, column)


class Field(common.SourceLocation):
    """
    An instance of a field in a struct.

    Name is always populated.
    A field will either have a struct_type or a cpp_type, but not both.
    Not all fields are set, it depends on the input document.
    """

    # pylint: disable=too-many-instance-attributes

    def __init__(self, file_name, line, column):
        # type: (unicode, int, int) -> None
        """Construct a Field."""
        self.name = None  # type: unicode
        self.description = None  # type: unicode
        self.cpp_name = None  # type: unicode
        self.optional = False  # type: bool
        self.ignore = False  # type: bool
        self.chained = False  # type: bool
        self.comparison_order = -1  # type: int

        # Properties specific to fields which are types.
        self.cpp_type = None  # type: unicode
        self.bson_serialization_type = None  # type: List[unicode]
        self.serializer = None  # type: unicode
        self.deserializer = None  # type: unicode
        self.bindata_subtype = None  # type: unicode
        self.default = None  # type: unicode

        # Properties specific to fields which are structs.
        self.struct_type = None  # type: unicode

        # Properties specific to fields which are arrays.
        self.array = False  # type: bool
        self.supports_doc_sequence = False  # type: bool

        # Properties specific to fields which are enums.
        self.enum_type = False  # type: bool

        # Properties specific to fields inlined from chained_structs
        self.chained_struct_field = None  # type: Field

        # Internal fields - not generated by parser
        self.serialize_op_msg_request_only = False  # type: bool
        self.constructed = False  # type: bool

        # Validation rules.
        self.validator = None  # type: Optional[Validator]

        super(Field, self).__init__(file_name, line, column)


class Command(Struct):
    """
    IDL commmand information.

    All fields are either required or have a non-None default.
    """

    def __init__(self, file_name, line, column):
        # type: (unicode, int, int) -> None
        """Construct a command."""
        self.namespace = None  # type: unicode
        self.command_field = None  # type: Field
        super(Command, self).__init__(file_name, line, column)


class EnumValue(common.SourceLocation):
    """
    IDL Enum Value information.

    All fields are either required or have a non-None default.
    """

    def __init__(self, file_name, line, column):
        # type: (unicode, int, int) -> None
        """Construct an Enum."""
        self.name = None  # type: unicode
        self.value = None  # type: unicode

        super(EnumValue, self).__init__(file_name, line, column)


class Enum(common.SourceLocation):
    """
    IDL Enum information.

    All fields are either required or have a non-None default.
    """

    def __init__(self, file_name, line, column):
        # type: (unicode, int, int) -> None
        """Construct an Enum."""
        self.name = None  # type: unicode
        self.description = None  # type: unicode
        self.cpp_namespace = None  # type: unicode
        self.type = None  # type: unicode
        self.values = []  # type: List[EnumValue]

        super(Enum, self).__init__(file_name, line, column)


class Condition(common.SourceLocation):
    """Condition(s) for a ServerParameter or ConfigOption."""

    def __init__(self, file_name, line, column):
        # type: (unicode, int, int) -> None
        """Construct a Condition."""
        self.expr = None  # type: unicode
        self.constexpr = None  # type: unicode
        self.preprocessor = None  # type: unicode

        super(Condition, self).__init__(file_name, line, column)


class ServerParameter(common.SourceLocation):
    """IDL ServerParameter setting."""

    # pylint: disable=too-many-instance-attributes

    def __init__(self, file_name, line, column):
        # type: (unicode, int, int) -> None
        """Construct a ServerParameter."""
        self.name = None  # type: unicode
        self.set_at = None  # type: unicode
        self.description = None  # type: unicode
        self.cpp_vartype = None  # type: unicode
        self.cpp_varname = None  # type: unicode
        self.condition = None  # type: Condition
        self.redact = False  # type: bool
        self.deprecated_name = []  # type: List[unicode]

        # Only valid if cpp_varname is specified.
        self.default = None  # type: unicode
        self.validator = None  # type: Validator
        self.on_update = None  # type: unicode

        # Required if cpp_varname is NOT specified.
        self.from_bson = None  # type: unicode
        self.append_bson = None  # type: unicode
        self.from_string = None  # type: unicode

        super(ServerParameter, self).__init__(file_name, line, column)


class ConfigGlobal(common.SourceLocation):
    """IDL ConfigOption Globals."""

    def __init__(self, file_name, line, column):
        # type: (unicode, int, int) -> None
        """Construct a ConfigGlobal."""

        # Other config globals are consumed in bind phase.
        self.initializer_name = None  # type: unicode

        super(ConfigGlobal, self).__init__(file_name, line, column)


class ConfigOption(common.SourceLocation):
    """IDL ConfigOption setting."""

    # pylint: disable=too-many-instance-attributes

    def __init__(self, file_name, line, column):
        # type: (unicode, int, int) -> None
        """Construct a ConfigOption."""
        self.name = None  # type: unicode
        self.short_name = None  # type: unicode
        self.deprecated_name = []  # type: List[unicode]
        self.deprecated_short_name = []  # type: List[unicode]

        self.description = None  # type: unicode
        self.section = None  # type: unicode
        self.arg_vartype = None  # type: unicode
        self.cpp_vartype = None  # type: unicode
        self.cpp_varname = None  # type: unicode
        self.condition = None  # type: Condition

        self.conflicts = []  # type: List[unicode]
        self.requires = []  # type: List[unicode]
        self.hidden = False  # type: bool
        self.redact = False  # type: bool
        self.default = None  # type: unicode
        self.implicit = None  # type: unicode
        self.source = None  # type: unicode

        self.duplicates_append = False  # type: bool
        self.positional_start = None  # type: int
        self.positional_end = None  # type: int
        self.validator = None  # type: Validator

        super(ConfigOption, self).__init__(file_name, line, column)
