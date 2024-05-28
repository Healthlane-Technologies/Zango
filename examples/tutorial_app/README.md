# Zango Tutorial App

## Introduction
This folder contains the source code of the Zango Tutorial App, an app for managing patients.

## Application Walk-through

### Creating a Patient

https://github.com/Healthlane-Technologies/Zango/assets/22682748/79ec5e2c-f322-4738-8cf3-e66ebf7e05ee

### Editing Patient Details

https://github.com/Healthlane-Technologies/Zango/assets/22682748/5ba497ab-ad72-4d30-9674-876a1c106b7e

### Patient Workflow

https://github.com/Healthlane-Technologies/Zango/assets/22682748/90549722-df9f-4fdf-bb15-79eed5a480de


## Steps for setting up the app

### 1. Setup Zango framework
Setup the Zango Framework locally or through the GitPod option given in the [Zango repository](https://github.com/Healthlane-Technologies/Zango)

### 2. Create an app
Create an app named "MyFirstApp" in Zango through the app panel.

### 3. Install Packages

Install the below required packages from the App Panel. For more information, refer to the [Installing a Package](https://www.zango.dev/docs/core/packages/installing-a-package).

1. login
2. frame
3. crud
4. workflow

### 4. Transfering the code
Copy all the contents from inside the "MyFirstApp" folder in this repository to the "MyFirstApp" folder present in you Zango installation.

### 5. Create user roles
Create the below user roles from the App Panel.

1. PatientSupportExecutive
2. PatientSupportManager

### 6. Migrate models

To migrate the patient model, execute the following command:

```python
python manage.py ws_migrate MyFirstApp
```

### 7. Sync Static Files
To sync static files, run the commands below:

```python
python manage.py sync_static MyFirstApp
```

```python
python manage.py collectstatic
```

### 8. Setup Login Config

Configure the Login package to have the configs mentioned in the image below

<img width="1439" alt="image" src="https://github.com/Healthlane-Technologies/Zango/assets/22682748/072b6166-4633-4cbe-889c-c30b883a2d43">

### 9. Setup Frame
Configure the Frames package to have the configs mentioned in the image below

![frame_config](https://github.com/Healthlane-Technologies/Zango/assets/22682748/41b30cf1-786a-4ba6-8035-b97adaf476de)

### 10. Sync and Assign Policies
Sync the policies and assign the required policies to the user role. For more information, refer to the [Syncing Policies](https://www.zango.dev/docs/core/permission-framework/policies/syncing-policy) and [Assigning Policies](https://www.zango.dev/docs/core/permission-framework/policies/assigning-policies)


Now you can create a user and login through ``/login`` route to access the application
