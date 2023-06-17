from django.db import router, connection
from django.conf import settings
from django.template import Origin, TemplateDoesNotExist
from django.template.loaders.base import Loader as BaseLoader

from django.apps import apps


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
        print(template_name)
        try:
            app_dir = settings.BASE_DIR / "zelthy_apps" / connection.tenant.name
            pages_dir = app_dir / "pages"
            for path in pages_dir.rglob('*'):
                if path.is_file() and path.name == template_name:
                    print(path)
                    with path.open('r') as f:
                        content = f.read()
                    print(content)
                    print(type(content))
                    return content
            # model = apps.get_model('customization', 'zelthyapptemplate')
            # template = model.objects.get(
            #                 name__exact=template_name)
            # return (template.get_code(connection.request_object, interface="app"), template_name)

        except Exception as e:
            try:
                return self._load_and_store_template(template_name, cache_key,
                                                    site, sites__isnull=True)
            except:
                pass
        raise TemplateDoesNotExist(template_name)