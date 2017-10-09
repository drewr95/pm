import contextlib
import functools
import io
import logging
import os

import attr
import pycparser.c_ast
import pycparser.c_generator
import PyQt5.QtCore
from PyQt5 import QtCore, QtGui, QtWidgets
import PyQt5.uic

import epyqlib.attrsmodel
import epyqlib.utils.qt

import epcpm.parametermodel
import epcpm.parameterstoc
import epcpm.symbolmodel

# See file COPYING in this source tree
__copyright__ = 'Copyright 2017, EPC Power Corp.'
__license__ = 'GPLv2+'


@attr.s
class ModelView:
    view = attr.ib()
    filename = attr.ib()
    droppable_from = attr.ib()
    columns = attr.ib()
    types = attr.ib()
    root_factory = attr.ib()
    model = attr.ib(default=None)
    proxy = attr.ib(default=None)
    selection = attr.ib(default=None)


class Window:
    def __init__(self, ui_file):
        # # TODO: CAMPid 980567566238416124867857834291346779
        # ico_file = os.path.join(QtCore.QFileInfo.absolutePath(QtCore.QFileInfo(__file__)), 'icon.ico')
        # ico = QtGui.QIcon(ico_file)
        # self.setWindowIcon(ico)

        logging.debug('Loading UI from: {}'.format(ui_file))

        ui = ui_file
        # TODO: CAMPid 9549757292917394095482739548437597676742
        if not QtCore.QFileInfo(ui).isAbsolute():
            ui_file = os.path.join(
                QtCore.QFileInfo.absolutePath(QtCore.QFileInfo(__file__)), ui)
        else:
            ui_file = ui
        ui_file = QtCore.QFile(ui_file)
        ui_file.open(QtCore.QFile.ReadOnly | QtCore.QFile.Text)
        ts = QtCore.QTextStream(ui_file)
        sio = io.StringIO(ts.readAll())
        self.ui = PyQt5.uic.loadUi(sio)

        self.ui.action_new.triggered.connect(lambda _: self.open())
        self.ui.action_open.triggered.connect(lambda _: self.open_from_dialog())
        self.ui.action_save.triggered.connect(lambda _: self.save())
        self.ui.action_save_as.triggered.connect(self.save_as)

        self.filters = [
            ('JSON', ['json']),
            ('All Files', ['*'])
        ]

        self.view_models = {}

        self.uuid_notifier = epcpm.symbolmodel.ReferencedUuidNotifier()
        self.uuid_notifier.changed.connect(self.symbol_uuid_changed)

        self.filename = None

    def set_model(self, name, view_model):
        self.view_models[name] = view_model

        view_model.proxy = QtCore.QSortFilterProxyModel()
        view_model.proxy.setSortCaseSensitivity(QtCore.Qt.CaseInsensitive)
        view_model.proxy.setSourceModel(view_model.model)
        view_model.view.setModel(view_model.proxy)

        view_model.selection = view_model.view.selectionModel()

        with contextlib.suppress(TypeError):
            view_model.selection.selectionChanged.disconnect()

        view_model.selection.selectionChanged.connect(
            self.selection_changed)

    def open_from_dialog(self):
        filename = epyqlib.utils.qt.file_dialog(self.filters, parent=self.ui)

        if filename is None:
            return

        self.open(filename=filename)

    def open(self, filename=None):
        view_models = {
            'parameters': ModelView(
                view=self.ui.parameter_view,
                filename=filename,
                droppable_from=('parameters',),
                columns=epcpm.parametermodel.columns,
                types=epcpm.parametermodel.types,
                root_factory=epcpm.parametermodel.Root,
            ),
            'symbols': ModelView(
                view=self.ui.symbol_view,
                filename=(
                    filename.replace('parameters', 'symbols')
                    if filename is not None
                    else None
                ),
                droppable_from=('parameters', 'symbols'),
                columns=epcpm.symbolmodel.columns,
                types=epcpm.symbolmodel.types,
                root_factory=epcpm.symbolmodel.Root,
            ),
        }

        self.uuid_notifier.disconnect_view()

        for name, view_model in view_models.items():
            view = view_model.view

            view.setSelectionBehavior(view.SelectRows)
            view.setSelectionMode(view.SingleSelection)
            view.setDropIndicatorShown(True)
            view.setDragEnabled(True)
            view.setAcceptDrops(True)

            if view_model.filename is None:
                view_model.model = epyqlib.attrsmodel.Model(
                    root=view_model.root_factory(),
                    columns=view_model.columns,
                )
            else:
                with open(view_model.filename) as f:
                    view_model.model = epyqlib.attrsmodel.Model.from_json_string(
                        s=f.read(),
                        columns=view_model.columns,
                        types=view_model.types
                    )

            self.set_model(name=name, view_model=view_model)
            view.expandAll()
            for i in range(view_model.model.columnCount(QtCore.QModelIndex())):
                view.resizeColumnToContents(i)
            self.filename = filename

            view.setContextMenuPolicy(
                QtCore.Qt.CustomContextMenu)
            m = functools.partial(
                self.context_menu,
                view_model=view_model
            )

            with contextlib.suppress(TypeError):
                view.customContextMenuRequested.disconnect()

            view.customContextMenuRequested.connect(m)

        self.uuid_notifier.set_view(self.ui.symbol_view)

        for view_model in view_models.values():
            view_model.model.add_drop_sources(*(
                view_models[d].model.root for d in view_model.droppable_from
            ))

        return

    def save(self):
        for view_model in self.view_models.values():
            s = view_model.model.to_json_string()

            with open(view_model.filename, 'w') as f:
                f.write(s)

                if not s.endswith('\n'):
                    f.write('\n')

    def save_as(self):
        filenames = {}

        for name, view_model in self.view_models.items():
            filename = epyqlib.utils.qt.file_dialog(
                filters=self.filters,
                parent=self.ui,
                save=True,
                caption='Save {} As'.format(name.title()),
            )

            if filename is None:
                return

            filenames[name] = filename

        for name, view_model in self.view_models.items():
            view_model.filename = filenames[name]

        if filename is not None:
            self.save()

    def context_menu(self, position, view_model):
        index = view_model.view.indexAt(position)
        index = view_model.view.model().mapToSource(index)

        model = view_model.model
        node = model.node_from_index(index)

        menu = QtWidgets.QMenu(parent=view_model.view)

        delete = None
        addable_types = node.addable_types()
        actions = {
            menu.addAction('Add {}'.format(name)): t
            for name, t in addable_types.items()
        }

        if node is not model.root:
            delete = menu.addAction('Delete')

        menu.addSeparator()
        generate_code = menu.addAction('Generate code...')

        action = menu.exec(
            view_model.view.viewport().mapToGlobal(position)
        )

        if action is not None:
            if action is delete:
                node.tree_parent.remove_child(child=node)
            elif action is generate_code:
                builder = epcpm.parameterstoc.builders.wrap(node)

                ast = pycparser.c_ast.FileAST(builder.definition())
                generator = pycparser.c_generator.CGenerator()
                s = generator.visit(ast)
                epyqlib.utils.qt.dialog(
                    parent=self.ui,
                    message=s,
                )
            else:
                node.append_child(actions[action]())

    def selection_changed(self, selected, deselected):
        pass

    def symbol_uuid_changed(self, uuid):
        view_model = self.view_models['parameters']
        model = view_model.model
        view = view_model.view

        node = model.node_from_uuid(uuid)
        index = model.index_from_node(node)
        index = epyqlib.utils.qt.resolve_index_from_model(
            model=model,
            view=view,
            index=index,
        )

        view.setCurrentIndex(index)
        view.selectionModel().select(
            index,
            QtCore.QItemSelectionModel.ClearAndSelect,
        )
