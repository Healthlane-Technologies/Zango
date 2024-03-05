from django.conf import settings

from pluginbase import PluginBase, PluginSource


class CustomPluginSource(PluginSource):
    def load_plugin(self, name):
        with self:
            return __import__(
                self.base.package + "." + name, globals(), {}, ["__name__"]
            )


class CustomPluginBase(PluginBase):
    def make_plugin_source(self, *args, **kwargs):
        """Creates a plugin source for this plugin base and returns it.
        All parameters are forwarded to :class:`PluginSource`.
        """
        return CustomPluginSource(self, *args, **kwargs)


plugin_base = CustomPluginBase(package="_workspaces")


def get_plugin_source(name):
    path = str(settings.BASE_DIR) + "/workspaces/" + name
    return plugin_base.make_plugin_source(searchpath=[path], persist=True)
