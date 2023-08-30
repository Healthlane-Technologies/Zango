# Steps to loadtest

- Run the `init.sh` script to create the postgres docker container and initialize the project
- The script takes the arguments
    - -t -- number of tenants
    - -nm -- number of models in each tenant
    - -nmod -- number of modules in each tenant (in case of zelthy)
    - -p -- the platform to use (zelthy or django)
    - -s -- the server to use (gunicorn, daphne, etc)
- Run the `loadtest.sh` script to loadtest and obtain the results
- The script takes the arguments
    - -t -- number of tenants
    - -p -- the platform to use (zelthy or django)
    - -s -- the server to use