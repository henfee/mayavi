"""
 Code related to traits UI menu items for the tree view of mayavi.
"""
# Author: Prabhu Ramachandran <prabhu@aero.iitb.ac.in>
# Copyright (c) 2008, Prabhu Ramachandran Enthought, Inc.
# License: BSD Style.

# Standard library imports.
from os.path import splitext, isfile

# Enthought library imports.
from enthought.traits.api import HasTraits, Any, List, Instance
from enthought.traits.ui.menu import Action, Menu
from enthought.pyface.api import FileDialog, OK

# Local imports.
from enthought.mayavi.core.registry import registry
from enthought.mayavi.core.common import error


################################################################################
# `MenuHelper` class.
################################################################################ 
class MenuHelper(HasTraits):
   
    # The object this menu generates the menus for.
    object = Any

    # The actions this helper generates.
    actions = List()

    ######################################################################
    # Public interface.
    ######################################################################
    def check_active(self, metadata):
        """Check if the `metadata` passed can be added to `self.object`.
        """
        # FIXME: This should also have logic for checking the attributes
        # and attribute_types.
        output_info = self.object.output_info
        input_info = metadata.input_info
        if output_info is None:
            return True
        elif input_info is None:
            return True
        output_datasets = output_info.datasets
        input_datasets = input_info.datasets
        if 'none' in output_datasets:
            return False
        if 'any' in input_datasets:
            return True
        for d in input_datasets:
            if d in output_datasets:
                return True
        return False

    def open_file_action(self):
        wildcard = 'All files (*.*)|*.*'
        for src in registry.sources:
            if len(src.extensions) > 0:
                wildcard += '|' + src.wildcard

        dialog = FileDialog(parent=None,
                            title='Open supported data file',
                            action='open', wildcard=wildcard
                            )
        if dialog.open() == OK:
            if not isfile(dialog.path):
                error("File '%s' does not exist!"%dialog.path, parent)
                return
            # FIXME: Ask for user input if a filetype is unknown and
            # choose appropriate reader.
            # FIXME: This is repeated in the engine and here and should
            # be fixed.
            filename = dialog.path
            base, ext = splitext(filename)
            readers = registry.get_file_reader(ext)
            if len(readers) == 0:
                msg = 'No readers found for the extension %s'%ext
                error(msg)
            else:
                object = self.object
                try:
                    object.scene.busy = True
                    reader = readers[-1]
                    callable = reader.get_callable()
                    if reader.factory is None:
                        src = callable()
                        src.initialize(filename)
                    else:
                        src = callable(filename)
                    object.add_child(src)
                finally:
                    object.scene.busy = False

    ######################################################################
    # Non-public interface.
    ######################################################################
    def _create_source(self, metadata):
        callable = metadata.get_callable()
        obj = callable()
        self.object.add_child(obj)

    def _create_object(self, metadata):
        callable = metadata.get_callable()
        obj = callable()
        self.object.add_child(obj)

    def _build_source_actions(self):
        actions = []
        a = Action(name='Open File ...',
                   action='object._menu_helper.open_file_action',
                   tooltip='Open a supported data file')
        actions.append(a)

        for src in registry.sources:
            if len(src.extensions) == 0:
                # The method that creates the source.
                setattr(self, src.id, 
                        lambda self=self, md=src: self._create_source(md))
                a = Action(name=src.menu_name,
                           action='object._menu_helper.'+src.id,
                           tooltip=src.tooltip)
                actions.append(a)
        return actions

    def _build_filter_actions(self):
        actions = []
        for fil in registry.filters:
            # The method that creates the object.
            setattr(self, fil.id, 
                    lambda self=self, md=fil: self._create_object(md))
            # The method that checks if the menu can be activated or
            # not.
            setattr(self, 'check_' + fil.id, 
                    lambda self=self, md=fil: self.check_active(md))
            a = Action(name=fil.menu_name,
                       action='object._menu_helper.' + fil.id,
                       enabled_when='object._menu_helper.check_%s()'%fil.id,
                       tooltip=fil.tooltip)
            actions.append(a)
        return actions

    def _build_module_actions(self):
        actions = []
        for mod in registry.modules:
            # The method that creates the module.
            setattr(self, mod.id, 
                    lambda self=self, md=mod: self._create_object(md))
            # The method that checks if the menu can be activated or
            # not.
            setattr(self, 'check_' + mod.id, 
                    lambda self=self, md=mod: self.check_active(md))
            a = Action(name=mod.menu_name,
                       action='object._menu_helper.' + mod.id,
                       enabled_when='object._menu_helper.check_%s()'%mod.id,
                       tooltip=mod.tooltip)
            actions.append(a)
        return actions


################################################################################
# `SourceMenuHelper` class.
################################################################################ 
class SourceMenuHelper(MenuHelper):
  
    def _actions_default(self):
        actions = self._build_source_actions()
        return [Menu(name='Add Source', *actions)]


################################################################################
# `FilterMenuHelper` class.
################################################################################ 
class FilterMenuHelper(MenuHelper):
   
    def _actions_default(self):
        filter_actions = self._build_filter_actions()
        module_actions = self._build_module_actions()
        return [Menu(name='Add Filter', *filter_actions),
                Menu(name='Add Module', *module_actions)]

################################################################################
# `ModuleMenuHelper` class.
################################################################################ 
class ModuleMenuHelper(MenuHelper):
   
    def _actions_default(self):
        module_actions = self._build_module_actions()
        return [Menu(name='Add Module', *module_actions)]