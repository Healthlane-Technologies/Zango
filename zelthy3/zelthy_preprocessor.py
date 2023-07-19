from django.apps import apps
class ZPreprocessor:
    """
    Handles import dynamically from within app
    """

    def __init__(self, file_obj, **kwargs):
        request = kwargs.get('request')
        self.parent_path = kwargs.get('parent_path')
        self.app_settings = kwargs.get('app_settings')
        self.app_dir = kwargs.get('app_dir')
        code_string = file_obj
        lines = code_string.split("\n")
        zfroms = []
        _lines = []
        for l in lines:
            if l.startswith('from'):
                try:
                    mod_name = l.split(" ")[1]
                    import importlib.util
                    spec = importlib.util.find_spec(mod_name)
                    if spec:
                        _lines.append(l)
                    else:
                        zfroms.append(l)
                except Exception as e:
                    zfroms.append(l)
            else:
                _lines.append(l)
        self.lines = _lines
        self.zfroms = zfroms
    
    def has_zimport(self):
        if len(self.zfroms) > 0:
            return True
        return False
        

class ZimportStack:
	
    def __init__(self, zcode, **kwargs):
        self.request = kwargs.get('request')    
        self.zcode = None
        self.elements = [] #stores zfrom import statements
        self._globals = None
        self._processed = []
        self.zcode = zcode
        self.load_globals()
        self._imported_objects = {}
        for z in zcode.zfroms:
            _split = z.strip().split(" ")
            self.elements.append(
                    {
                    'zpath': _split[1], 
                    'obj': [_split[-1]],
                    'parent': self.zcode.parent_path
                    })

    def load_globals(self):
        self._globals = globals()
        all_keys = self._globals.keys()
        _new = ['__builtins__', '__file__', 'ZimportStack', '__package__', 'unicode_literals', '__name__', '__doc__', 'ZPreprocessor']
        keys_to_delete = [i for i in all_keys if i not in _new]
        for k in keys_to_delete:
            del self._globals[k]
        return 

    def is_package(self, app_settings, package_name):
        package_list = app_settings['packages']
        for package in package_list:
            if package["name"] == package_name:
                return True
        return False

    
    def get_top(self):
        if len(self.elements) > 0:
            return self.elements[-1]
        else:
            return None
    
    def get_zfileobj(self, path, parent_path):
        if path.startswith('..'):
            module_filepath = parent_path.parent / "/".join(path[2:].split("."))
        elif path.startswith('.'):
            module_filepath = parent_path / "/".join(path[1:].split("."))
        else:
            mod1 = path.split(".")[0]
            if self.is_package(self.zcode.app_settings, mod1):
                module_filepath = self.zcode.app_dir / "zelthy_packages" / "/".join(path.split("."))
            else:
                module_filepath = self.zcode.app_dir /  "/".join(path.split("."))
        module_filepath = module_filepath.with_suffix('.py')
        with module_filepath.open() as f:
            content = f.read()
        return content, module_filepath

    
    def process_import_and_execute(self):
        top = self.get_top()
        if top:
            file_obj, module_filepath = self.get_zfileobj(top['zpath'], top['parent'])
            zcode = ZPreprocessor(
                        file_obj, 
                        request=self.request,
                        parent_path=module_filepath.parent, 
                        app_dir=self.zcode.app_dir,
                        app_settings=self.zcode.app_settings
                        )
            if zcode.has_zimport():
                all_imports_available = True
                for z in zcode.zfroms:
                    _split = z.strip().split(" ")
                    if {
                        'zpath': _split[1], 
                        'obj': [_split[3]], 
                        'parent': module_filepath.parent
                        } not in \
                        self._processed:            
                        self.elements.append(
                            {
                            'zpath': _split[1], 
                            'obj': [_split[3]],
                            'parent': module_filepath.parent
                            })
                        all_imports_available = False
                if all_imports_available:
                    exec("\n".join(zcode.lines), self._globals, self._globals)
                    self._processed.append(self.elements.pop())    
            else:
                exec("\n".join(zcode.lines), self._globals, self._globals)
                processed = self.elements.pop()
                self._processed.append(processed)
                for o in processed['obj']:
                    self._imported_objects[o, str(module_filepath.parent)] = self._globals[o]
            self.process_import_and_execute()
        else:
            #Final Execution
            self._globals = globals()
            for k,v in self._imported_objects.items():
                if k[0] not in ["ModelBase", "SimpleMixim", "DynamicTable"]:
                    self._globals[k[0]] = v
                    if "ModelBase" in str(type(v)):
                        print(k[0])
                        self._globals[k[0]].__module__ = ".".join(k[1][k[1].find("zelthy_apps"):].split("/")) + ".models"
            exec("\n".join(self.zcode.lines), self._globals, self._globals)
            
            # for k,v in self._imported_objects.items():
            #     if k[0] not in ["ModelBase", "SimpleMixim", "DynamicTable"]:
            #         self._globals[k[0]] = v
            #         if "ModelBase" in str(type(v)):
            #             self._globals[k[0]].__module__ = "zelthy3.zelthy_preprocessor"
