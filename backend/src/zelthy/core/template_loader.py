import os
from django.db import connection
from django.conf import settings
from django.template import Origin, TemplateDoesNotExist
from django.template.loaders.base import Loader as BaseLoader


class AppTemplateLoader(BaseLoader):

    is_usable = True

    def get_template_sources(self, template_name, template_dirs=None):
        yield Origin(name=template_name, template_name=template_name, loader=self)

    def get_contents(self, origin):
        content = self._load_template_source(origin.template_name)
        return content

    def _load_template_source(self, template_name, template_dirs=None):
        """
        Attempts to load the content of a specified template file from a tenant-specific directory.

        This function searches for the template file within the "workspaces" directory.
        It iterates through all "templates" subdirectories within the tenant's workspace to find and read the specified template file.

        Args:
            template_name: The name of the template to load.
            template_dirs: Optional list of template directories to search in.

        Returns:
            The content of the specified template.

        Raises:
            TemplateDoesNotExist: If the specified template does not exist.
        """
        try:
            app_dir = settings.BASE_DIR / "workspaces" / connection.tenant.name
            template_folders = list(app_dir.glob("**/templates"))
            for folder in template_folders:
                _file = str(folder) + "/" + template_name
                if os.path.exists(_file):
                    with open(_file) as f:
                        content = f.read()
                    return content

        except Exception as e:
            print(e)
        raise TemplateDoesNotExist(template_name)
