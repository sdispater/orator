# Contributing
All kind of contribution is welcome: reporting new issues, pull requests or tweeting about this project.


## Installation
In this section we will focus to setup the project to run the tests in our local environment. 

Orator supports many python versions and also multiple databases so the setup can be a little difficult. To make it 
as easy as possible we will use docker.

But before beginning there are some prerequisites to setup the environment.

### Prerequisites
  * [docker](https://docs.docker.com/install/)
  * [pyenv](https://github.com/pyenv/pyenv)
  * [poetry](https://github.com/sdispater/poetry)

### Instructions

#### Python 3.7
First we will install python 3.7 using pyenv. But before installing this version of python you will need some
packages installed to compile python correctly. You can install them using apt.

  * libsqlite3-dev
  * libbz2-dev

Now you can install python 3.7 (this will take a while)
```cmd
pyenv install 3.7.2
```

Change to use the new python
```cmd
pyenv local 3.7.2
```

And finally install the dependencies
```
poetry install --extras mysql-python --extras pgsql
```

#### Databases
First thing is to start our databases with the following command:

```cmd
docker run --rm --name postgres -e POSTGRES_PASSWORD=orator -e POSTGRES_USER=orator -d -p 5432:5432 postgres:9.6
docker run --rm --name mysql -e MYSQL_ROOT_PASSWORD=orator  -d -p 3306:3306 mysql:5.7
```

This will create a new docker with the Postgres 9.6 version and Mysql 5.7.

Next we create our test databases:
```cmd
docker exec postgres psql -c 'create database orator_test;' -U orator
docker exec mysql mysql -e 'create database orator_test;' --password=orator
```


And finally create a new user to connect to this databases. 
```cmd
docker exec mysql mysql -u root -porator -e "CREATE USER 'orator'@'%' IDENTIFIED BY 'orator';"
docker exec mysql mysql -u root -porator -e "USE orator_test; GRANT ALL PRIVILEGES ON orator_test.* TO 'orator'@'%';"
```

#### Tests
Now you can try to execute the tests:
```cmd
poetry run pytest tests -sq
```
