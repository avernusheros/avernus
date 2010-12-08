# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-

import imp
import os
import types
from configobj import ConfigObj

from avernus import config
from avernus.logger import Log

class Plugin(object):
    instance = None
    enabled = False
    error = False
    icon = 'plugin'
    _active = False
    missing_modules = []
    
    def __init__(self, info, module_path):
        """Initialize the Plugin using a ConfigObj."""
        info_fields = {
          'module_name': 'Module',
          'name': 'Name',
          'version': 'Version',
          'authors': 'Authors',
          'description': 'Description',
          'module_depends': 'Dependencies'
        }
        for attr, field in info_fields.iteritems():
            try:
                setattr(self, attr, info[field])
            except KeyError:
                setattr(self, attr, [])
        self._load_module(module_path)
    
    @property
    def configurable(self):
        if self.instance is None:
            return False
        else: return self.instance.configurable

    def _get_active(self):
        return self._active
    
    def _set_active(self, value):
        if value:
            self.instance = self.plugin_class()
            self.instance.api = self.api
            self.instance.activate()
        else:
            self.instance.deactivate()
            self.instance = None
        self._active = value
    
    active = property(_get_active, _set_active)
       
    def _check_module_depends(self):
        self.missing_modules = []
        for mod_name in self.module_depends:
            try:
                __import__(mod_name)
            except:
                self.missing_modules.append(mod_name)
                self.error = True
    
    
    def _load_module(self, module_path):
        """Load the module containing this plugin."""
        try:
            # import the module containing the plugin
            f, pathname, desc = imp.find_module(self.module_name, module_path)
            module = imp.load_module(self.module_name, f, pathname, desc)
            # find the class object for the actual plugin
            for key, item in module.__dict__.iteritems():
                if isinstance(item, types.ClassType):
                    self.plugin_class = item
                    try:
                        self.class_name = item.__dict__['__module__'].split('.')[1]
                    except:
                        #plugins that are not in a directory
                        self.class_name = item.__name__
                    break
        except ImportError, e:
            Log.debug(self.module_name+str(e))
            # load_module() failed, probably because of a module dependency
            if len(self.module_depends) > 0:
                self._check_module_depends()
            else:
                # no dependencies in info file; use the ImportError instead
                self.missing_modules.append(str(e).split(" ")[3])
            self.error = True
        except Exception, e:
            # load_module() failed for some other reason
            Log.debug(self.module_name+"load_module() failed for some other reason")
            self.error = True


class PluginEngine():
    def __init__(self, plugin_path, api):
        self.plugins = {}
        self.api = api
        self.plugin_path = plugin_path
        self.initialized_plugins = []
        self.config = config.avernusConfig()
    
    def load_plugins(self):       
        plugin_info_files = []
        for path in self.plugin_path:
            if os.path.exists(path):
                for f in os.listdir(path):
                    info_file = os.path.join(path, f)
                    if os.path.isfile(info_file) and f.endswith('.avernus-plugin'):
                        plugin_info_files.append(info_file)
        for info_file in plugin_info_files:
            info = ConfigObj(info_file)
            p = Plugin(info["avernus Plugin"], self.plugin_path)
            self.plugins[p.module_name] = p
    
    @property 
    def enabled_plugins(self):
        plugins = filter(lambda (name,p): p.enabled, self.plugins.iteritems())
        return dict(plugins)
    
    def activate_plugins(self, plugins, save=True):
        for plugin in plugins:
            if plugin.enabled and not plugin.error:
                plugin.api = self.api
                plugin.active = True
        if save:
            self.save_to_config()
                
    def deactivate_plugins(self, plugins, save=True):
        for plugin in plugins:
            if not plugin.enabled:
                plugin.active = False
        if save:
            self.save_to_config()
    
    def save_to_config(self):
        self.config.set_option('enabled', self.enabled_plugins.keys(), section = 'Plugins')

    def enable_from_config(self):
        if len(self.plugins) > 0:
            enabled = self.config.get_option('enabled', section='Plugins')
            if enabled is not None:
                enabled = eval(enabled)
                for name, plugin in self.plugins.iteritems():
                    if name in enabled and not plugin.error:
                        plugin.enabled = True
                    else:
                        plugin.enabled = False
                self.activate_plugins(self.enabled_plugins.values(), False)
