import collections

import attr
import graham
import marshmallow
import PyQt5.QtCore

import epyqlib.attrsmodel
import epyqlib.treenode
import epyqlib.utils.general
import epyqlib.utils.qt

import epcpm.parametermodel

# See file COPYING in this source tree
__copyright__ = 'Copyright 2017, EPC Power Corp.'
__license__ = 'GPLv2+'


@staticmethod
def child_from(node):
    return Signal(name=node.name, parameter_uuid=str(node.uuid))


@graham.schemify(tag='signal')
@epyqlib.utils.qt.pyqtify()
@attr.s(hash=False)
class Signal(epyqlib.treenode.TreeNode):
    name = attr.ib(
        default='New Signal',
        metadata=graham.create_metadata(
            field=marshmallow.fields.String(),
        ),
    )
    bits = attr.ib(
        default=0,
        metadata=graham.create_metadata(
            field=marshmallow.fields.Integer(),
        ),
    )
    signed = attr.ib(
        default=False,
        metadata=graham.create_metadata(
            field=marshmallow.fields.Boolean(),
        ),
    )
    factor = attr.ib(
        default=1,
        metadata=graham.create_metadata(
            field=marshmallow.fields.Decimal(as_string=True),
        ),
    )
    parameter_uuid = epyqlib.attrsmodel.attr_uuid(
        metadata={'human name': 'Parameter UUID'},
        default=None,
        allow_none=True,
    )
    uuid = epyqlib.attrsmodel.attr_uuid()

    def __attrs_post_init__(self):
        super().__init__()

    def can_drop_on(self, node):
        return False

    can_delete = epyqlib.attrsmodel.childless_can_delete


@graham.schemify(tag='message')
@epyqlib.utils.qt.pyqtify()
@attr.s(hash=False)
class Message(epyqlib.treenode.TreeNode):
    name = attr.ib(
        default='New Message',
        metadata=graham.create_metadata(
            field=marshmallow.fields.String(),
        ),
    )
    identifier = attr.ib(
        default=0x1fffffff,
        metadata=graham.create_metadata(
            field=marshmallow.fields.Integer(),
        ),
    )
    extended = attr.ib(
        default=True,
        convert=epyqlib.attrsmodel.two_state_checkbox,
        metadata=graham.create_metadata(
            field=marshmallow.fields.Boolean(),
        ),
    )
    length = attr.ib(
        default=0,
        metadata=graham.create_metadata(
            field=marshmallow.fields.Int(),
        ),
    )
    cycle_time = attr.ib(
        default=None,
        convert=epyqlib.attrsmodel.to_decimal_or_none,
        metadata=graham.create_metadata(
            field=marshmallow.fields.Decimal(allow_none=True, as_string=True),
        ),
    )
    children = attr.ib(
        default=attr.Factory(list),
        metadata=graham.create_metadata(
            field=graham.fields.MixedList(fields=(
                marshmallow.fields.Nested(graham.schema(Signal)),
            )),
        ),
    )
    uuid = epyqlib.attrsmodel.attr_uuid()

    def __attrs_post_init__(self):
        super().__init__()

    child_from = child_from

    @classmethod
    def all_addable_types(cls):
        return epyqlib.attrsmodel.create_addable_types((Signal,))

    def addable_types(self):
        return {}

    def can_drop_on(self, node):
        return isinstance(node, epcpm.parametermodel.Parameter)

    def can_delete(self, node=None):
        if node is None:
            return self.tree_parent.can_delete(node=self)

        return True


@graham.schemify(tag='multiplexer')
@epyqlib.utils.qt.pyqtify()
@attr.s(hash=False)
class Multiplexer(epyqlib.treenode.TreeNode):
    name = attr.ib(
        default='New Multiplexer',
        metadata=graham.create_metadata(
            field=marshmallow.fields.String(),
        ),
    )
    identifier = attr.ib(
        default=None,
        metadata=graham.create_metadata(
            field=marshmallow.fields.Integer(allow_none=True),
        )
    )
    length = attr.ib(
        default=0,
        metadata=graham.create_metadata(
            field=marshmallow.fields.Int(),
        ),
    )
    cycle_time = attr.ib(
        default=None,
        convert=epyqlib.attrsmodel.to_decimal_or_none,
        metadata=graham.create_metadata(
            field=marshmallow.fields.Decimal(allow_none=True, as_string=True),
        ),
    )
    comment = attr.ib(
        default=None,
        convert=epyqlib.attrsmodel.to_str_or_none,
        metadata=graham.create_metadata(
            field=marshmallow.fields.String(allow_none=True),
        ),
    )
    children = attr.ib(
        default=attr.Factory(list),
        metadata=graham.create_metadata(
            field=graham.fields.MixedList(fields=(
                marshmallow.fields.Nested(graham.schema(Signal)),
            )),
        ),
    )
    uuid = epyqlib.attrsmodel.attr_uuid()

    def __attrs_post_init__(self):
        super().__init__()

    child_from = child_from

    @classmethod
    def all_addable_types(cls):
        return epyqlib.attrsmodel.create_addable_types((Signal,))

    def addable_types(self):
        return {}

    def can_drop_on(self, node):
        return isinstance(node, (epcpm.parametermodel.Parameter, Signal))

    def can_delete(self, node=None):
        if node is None:
            return self.tree_parent.can_delete(node=self)

        return True


@graham.schemify(tag='multiplexed_message')
@epyqlib.utils.qt.pyqtify()
@attr.s(hash=False)
class MultiplexedMessage(epyqlib.treenode.TreeNode):
    name = attr.ib(
        default='New Multiplexed Message',
        metadata=graham.create_metadata(
            field=marshmallow.fields.String(),
        ),
    )
    identifier = attr.ib(
        default=0x1fffffff,
        metadata=graham.create_metadata(
            field=marshmallow.fields.Integer(),
        ),
    )
    extended = attr.ib(
        default=True,
        convert=epyqlib.attrsmodel.two_state_checkbox,
        metadata=graham.create_metadata(
            field=marshmallow.fields.Boolean(),
        ),
    )
    children = attr.ib(
        default=attr.Factory(list),
        metadata=graham.create_metadata(
            field=graham.fields.MixedList(fields=(
                marshmallow.fields.Nested(graham.schema(Signal)),
                marshmallow.fields.Nested(graham.schema(Multiplexer)),
            )),
        ),
    )
    uuid = epyqlib.attrsmodel.attr_uuid()

    def __attrs_post_init__(self):
        super().__init__()

    def can_drop_on(self, node):
        return isinstance(node, tuple(self.addable_types().values()))

    def can_delete(self, node=None):
        if node is None:
            return self.tree_parent.can_delete(node=self)

        return True

    @classmethod
    def all_addable_types(cls):
        return epyqlib.attrsmodel.create_addable_types((Signal, Multiplexer))

    def addable_types(self):
        types = (Signal,)

        if len(self.children) > 0:
            types += (Multiplexer,)

        return epyqlib.attrsmodel.create_addable_types(types)


Root = epyqlib.attrsmodel.Root(
    default_name='Symbols',
    valid_types=(Message, MultiplexedMessage)
)

types = epyqlib.attrsmodel.Types(
    types=(Root, Message, Signal, MultiplexedMessage, Multiplexer),
)

columns = epyqlib.attrsmodel.columns(
    tuple((x, 'name') for x in types.types.values()),
    tuple((x, 'identifier') for x in (
        Message,
        MultiplexedMessage,
        Multiplexer,
    )),
    ((Signal, 'bits'),),
    tuple((x, 'length') for x in (Message, Multiplexer)),
    ((Message, 'extended'),),
    ((Message, 'cycle_time'),),
    ((Signal, 'parameter_uuid'),)
)


@attr.s
class ReferencedUuidNotifier(PyQt5.QtCore.QObject):
    changed = PyQt5.QtCore.pyqtSignal('PyQt_PyObject')

    view = attr.ib(default=None)
    selection_model = attr.ib(default=None)

    def __attrs_post_init__(self):
        super().__init__()

        if self.view is not None:
            self.set_view(self.view)

    def set_view(self, view):
        self.disconnect_view()

        self.view = view
        self.selection_model = self.view.selectionModel()
        self.selection_model.currentChanged.connect(
            self.current_changed,
        )

    def disconnect_view(self):
        if self.selection_model is not None:
            self.selection_model.currentChanged.disconnect(
                self.current_changed,
            )
        self.view = None
        self.selection_model = None

    def current_changed(self, current, previous):
        index, model = epyqlib.utils.qt.resolve_index_to_model(
            view=self.view,
            index=current,
        )
        node = model.node_from_index(index)
        if isinstance(node, Signal):
            self.changed.emit(node.parameter_uuid)
