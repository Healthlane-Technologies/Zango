



class ZPreprocessor:
    """
    Handles zfrom and zimport
    """

    def __init__(self, file_obj, **kwargs):
        request = kwargs.get('request')
        # code_string = file_obj.get_code(request, interface="app")
        code_string = file_obj
        # self.folder = file_obj.parentFolder
        lines = code_string.split("\n")
        zfroms = []
        _lines = []
        for l in lines:
            if "zfrom" in l:
                zfroms.append(l.strip())
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
        # self.folder = None
        self.zcode = None
        self.elements = [] #stores zfrom import statements
        self._globals = None
        self._processed = []
        self.zcode = zcode
        # self.folder = zcode.folder
        # self._globals = globals()
        self.load_globals()
        self.add_safe_functions()
        self._imported_objects = {}
        for z in zcode.zfroms:
            _split = z.strip().split(" ") 
            self.elements.append(
                    {
                    'zpath': _split[1], 'obj': [o.replace(",","") for o in _split[3:-1]]
                    })

    def load_globals(self):
        self._globals = globals()
        all_keys = self._globals.keys()
        _new = ['__builtins__', '__file__', 'ZimportStack', '__package__', 'unicode_literals', '__name__', '__doc__', 'ZPreprocessor']
        keys_to_delete = [i for i in all_keys if i not in _new]
        for k in keys_to_delete:
            del self._globals[k]
        return 

    def add_safe_functions(self):
        pass
    
    def get_top(self):
        if len(self.elements) > 0:
            return self.elements[-1]
        else:
            return None
    
    def get_zfileobj(self, path):
        if "." not in path:
            filemodel = self.folder.filemodel_set.all().filter(
                                            fileName=path
                                            ).first()
            return filemodel
        else:
            _split = path.split(".")
            from django.apps import apps
            file_model = apps.get_model('customization', 'FileModel')
            filemodel = file_model.objects.filter(fileName=_split[-1])
            for f in filemodel:
                folders = []
                folder = f.parentFolder
                while folder:
                    folders.append(folder.folderName)
                    folder = folder.parentFolder
                folders.reverse()
                _path = ".".join(folders)+"."+_split[-1]
                if _path == path:
                    return f
            return None
    
    def process_import_and_execute(self):
        top = self.get_top()        
        if top:
            file_obj = self.get_zfileobj(top['zpath'])
            zcode = ZPreprocessor(file_obj, request=self.request)
            if zcode.has_zimport():
                all_imports_available = True
                for z in zcode.zfroms:
                    _split = z.strip().split(" ")
                    if {'zpath': _split[1], 'obj': _split[3:-1]} not in \
                        self._processed:            
                        self.elements.append(
                            {
                            'zpath': _split[1], 'obj': _split[3:-1]
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
                    self._imported_objects[o] = self._globals[o]
            self.process_import_and_execute()
        else:
            #Final Execution
            self._globals = globals()
            for k,v in self._imported_objects.items():
                self._globals[k] = v
            exec("\n".join(self.zcode.lines), self._globals, self._globals)