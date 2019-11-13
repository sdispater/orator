# Contributing
All kind of contribution is welcome: reporting new issues, pull requests or tweeting about this project.


## Installation
In this section we will focus to setup the project to run the tests in our local environment. 

Orator supports many python versions and also multiple databases so the setup can be a little difficult. To make it as easy as possible we will use docker and docker-compose.

But before beginning there are some prerequisites to setup the environment.

### Prerequisites
  * [docker](https://docs.docker.com/install/)
  * [docker-compose](https://docs.docker.com/compose/install/)

### Instructions
We already prepared all the images to permit to start the test environment with one command:

```cmd
make start-containers
```

This will start the databases::
  * postgres 9.6
  * mysql 5.6


### Run tests
Now you can try to execute the tests:

```cmd
make test
```

