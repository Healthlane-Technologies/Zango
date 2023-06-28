## How to install zelthy3



**Step 1:** Create a new directory and install virtualenv in it

```bash
mkdir dir
cd dir
virtualenv .
```

**Step 2:** Activate the virtualenv

```bash
source bin/activate
```

**Step 3:** Install zelthy3 in the virtualenv

If you are developing zelthy3

```bash
pip install -r /path to zelthy3 lib
```
    
if you are using zelthy3 to develop apps
```bash
pip install /path to zelthy3 tar package
```

**Step 4:** Start your first zelthy3 project
```bash
zelthy3 startproject myfirstproject
```




####Issues:
- zelthy3 is not working fine
- 



## How to develop applications on zelthy3?

On launching an app (from the d-panel), a folder is provisioned for the app by the unique name of the app. The app’s folder will have a few folders and files to begin with:
- An empty folder with the name "templates"
- An empty folder with the name "static"
- An empty folder with the name "media"
- `settings.json` with some boilerplate settings shown below

```json
{
    "version": "1.0.0",
    "modules": [ //this should not be changed manually
    ],
    "routes": [
    ]
}

```

For developing features in the applications, modules need to be added:
- Go to the app’s root directory and execute the command `python manage.py addmodule <module_name>`

Modules can also be created inside any folder structure inside the app's root directory.
   - Create any folder structure in the app’s root directory.
   - Navigate to the desired path and execute the command `python manage.py addmodule <module_name>`

On executing the `addmodule` command, the following will happen:
- A directory by the name `<module_name>` is created in the path where the `addmodule` command is executed.
- The module’s directory will have the following folders and files:
   - `templates`
     - `hello_world.html` a sample html file
   - `views` 
     - `pages` 
        - `hello_world.py` a sample page
    - `apis`
        - `my_first_api.py` a sample API
   - `datamodels`
        - `my_first_model.py` boilerplate code for data model 
   - `tests`
   - `module_settings.json`

When a module is created, it is automatically registered in settings.json. 

The module_settings.json will have the below boilerplate entry consistent with the pages, apis, datamodels, etc. created in the newly created module

```json

{
 "pages": [
    {
        "name": "page1",
        "path": "views/pages/hello_world.py",
        "template": "",
        "meta_title": "My First Page",
        "perm": {
            "is_public": false,
            "allowed_roles": []
        }        
    }
 ],
 "apis": [
    {
        "name": "api1",
        "path": "views/page1",
        "perm": {
            "is_public": false,
            "allowed_roles": []
        }        
    }
 ],
 "datamodels": [
    {
        "name": "MyFirstModel",
        "path": "datamodels/my_first_model.py"
    }
 ],    
 "routes": 
    [
        {
            "re_path": "^hello_world/$",
            "view_path": "views/pages/hello_world.py"
        },
        {
            "re_path": "^my_first_api/$",
            "view_path": "views/my_first_api.py"
        }
    ]
}


```
It is not necessary to follow the same folder strucure or folder naming for views, pages, apis or datamodels. The only requirement is to include the items in the module_settings.json with the relevant path. 


## How packages work in Zelthy3?

Packages represent a collection of features built on zelthy3, generally reusable components or features that can be directly used to represent certain use cases. When installed packages are populated as one or more modules in the app.  

Package - Migration, Collectstatic.

- Install package zelthy3 install pkgname
- Register the package in settings.json and update the package's settings
- Once a package is registered as a module it becomes a 
- Run app_migrate

- Zelthy packages are dynamically executed.
- Pages, APIs, Tasks etc. exposed by the installed packages have to be called seperately
- 


# Examples of packages:
 - Email Module: Email module can be a package that includes the following:
    - datamodels to store Email Objects
    - pages to host the email's inbox, outbox etc. with email sending functionality
    - pages to configure email - e.g. smtp, imap configurations

Usage of email module:
-   

    <!-- roles are not known when module is developed -->

How to modify module's code?
- Ideally module's code should not be altered directly to keep it upgradable
- 

- SMS Module: 

Pages need to be compatible with Frames


How to install Frames?
 - Frames have the following aspects that need to be considered:
    - Support of Menu 
    - Select

    
