# Development Guides

## prerequisites

- Docker for Desktop 4.1.1
- docker-compose v2.0.0
- Python 3.9 or later

## Steps (only first)

Move to the project root directory

```shell
$ pwd
/path/to/doktor-v2
```

Create a docker network

```shell
docker network create frontend
```

Install task runner: [Runner](https://github.com/stylemistake/runner#installation)

```
npm install -g bash-task-runner
```

## Getting started

Move to the project root directory

```shell
$ pwd
/path/to/doktor-v2
```

Start containers:

```shell
runner up
```

Access web ui

- Web UI(front) http://localhost:4000/
- Admin UI(front-admin) http://localhost:4300/

Stop containers:

```shell
runner down
```
