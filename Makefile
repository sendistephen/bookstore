build:
	docker-compose -f local.yml build

up:
	docker-compose -f local.yml up -d

down:
	docker-compose -f local.yml down

down-v:
	docker-compose -f local.yml down -v

show-logs:
	docker-compose -f local.yml logs

show-logs-api:
	docker-compose -f local.yml logs api

show-logs-nginx:
	docker-compose -f local.yml logs nginx

show-logs-postgres:
	docker-compose -f local.yml logs postgres_db

user:
	docker build -t bookstore-api -f ./docker/local/flask/Dockerfile .
	docker run --rm bookstore-api whoami

volume:
	docker volume inspect postgres_data
