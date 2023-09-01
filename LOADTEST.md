# Steps to loadtest

- Set the desired platform, server and other variables in the docker compose file
- Run `docker compose up`
- After verifying that all the migrations have been applied 
- run the command `python add_loadtest.py <platform> <no_of_tests>` to add the loadtests
- In a new shell run the command `bash loadtest.bash`
    the command takes the following arguments
    - -t - number of tenants to run the loadtest against
    - -p - specify the platform against which your are performing loadtest
    - -s - specify the server against which you are performing loadtest

**Note:** Before running the test again make sure to run the `docker compose down` command to make sure that a fresh database is used