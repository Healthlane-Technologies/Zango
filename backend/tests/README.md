## Steps to run the tests

1. **Create a Virtual Environment:**

   It's recommended to use a virtual environment to isolate the project's dependencies. If you don't have `virtualenv` installed, you can install it using pip:

   ```bash
   pip install virtualenv
   ```

   Then, create a new virtual environment and activate it:

   ```bash
   virtualenv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Clone the Zelthy3 Repository:**

   Clone the Zelthy3 repository from the designated source using Git:

   ```bash
   git clone https://github.com/Healthlane-Technologies/zelthy3.git
   ```

3. **Install Zelthy:**

   Navigate to the `backend` folder of the cloned repository and install the required dependencies using pip:

   ```bash
   cd zelthy3/backend
   pip install .
   ```

4. **Configure Connection Details:**

   Open the `tests/settings.py` file in the `backend/src/tests` folder. Ensure that the connection details for the PostgreSQL instance are correctly configured. Make sure you have a PostgreSQL instance up and running with the same connection details as provided in the `settings.py` file.

5. **Running Tests:**

   Once everything is set up, navigate to the `backend/src/tests` folder and execute the following command to run the tests:

   ```bash
   python manage.py test <test_name>
   ```

   Example:
   ```bash
   python manage.py test orm_tests.queries.test_related
   ```

   Replace `<test_name>` with the name of the specific test you want to run. This command will initiate the testing suite and provide feedback on the results.
