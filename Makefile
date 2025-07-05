REGISTRY=127.0.0.1:5000
IMAGE_NAME=otsun_notebook
TAG=$(shell git rev-parse --short HEAD)
FULL_IMAGE=$(REGISTRY)/$(IMAGE_NAME):$(TAG)

.PHONY: build push up deploy

build:
	docker build -t $(FULL_IMAGE) .

push: build
	docker push $(FULL_IMAGE)

generate-swarm:
	sed 's|__TAG__|$(TAG)|g' docker-compose.swarm.yml > docker-compose.generated.yml

up:
	docker compose -f docker-compose.base.yml up

deploy: push generate-swarm
	docker stack deploy -c docker-compose.base.yml -c docker-compose.generated.yml otsun
