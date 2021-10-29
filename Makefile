SHELL=/bin/bash

up:
	docker-compose -f front/docker-compose.yml       up -d
	docker-compose -f front-admin/docker-compose.yml up -d
	docker-compose -f paper/docker-compose.yml       up -d
	docker-compose -f author/docker-compose.yml      up -d

down:
	docker-compose -f front/docker-compose.yml       down
	docker-compose -f front-admin/docker-compose.yml down
	docker-compose -f paper/docker-compose.yml       down
	docker-compose -f author/docker-compose.yml      down
