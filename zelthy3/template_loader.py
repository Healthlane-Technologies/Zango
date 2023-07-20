import os
from django.db import router, connection
from django.conf import settings
from django.template import Origin, TemplateDoesNotExist
from django.template.loaders.base import Loader as BaseLoader

from django.apps import apps

"""
the html must be inside the page folder or in the templates folder

"""


class AppTemplateLoader(BaseLoader):

    is_usable = True

    def get_template_sources(self, template_name, template_dirs=None):
        yield Origin(
            name=template_name,
            template_name=template_name,
            loader=self
        )

    def get_contents(self, origin):
        content = self._load_template_source(origin.template_name)
        return content


    def _load_template_source(self, template_name, template_dirs=None):
        try:
            app_dir = settings.BASE_DIR / "zelthy_apps" / connection.tenant.name  
            ##new
            template_folders = list(app_dir.glob('**/templates'))
            # print(template_folders)
            for folder in template_folders:
                _file =  str(folder) + "/" + template_name
                if os.path.exists(_file):
                    with open(_file) as f:
                        content = f.read()
                    return content
            

            # print(template_folders)
            # end ofnew          
            # for path in app_dir.rglob('*'):
            #     print(template_name )
                
            #     if path.is_file() and path.name == template_name:
            #         with path.open('r') as f:
            #             content = f.read()
            #         return content

        except Exception as e:
            print(e)
            try:
                return self._load_and_store_template(template_name, cache_key,
                                                    site, sites__isnull=True)
            except:
                pass
        raise TemplateDoesNotExist(template_name)