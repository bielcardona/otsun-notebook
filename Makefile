# 🧩 Variables configurables amb valors per defecte

# Nom del registre on pushes la imatge
REGISTRY ?= 127.0.0.1:5000

# Nom de la imatge sense tag
IMAGE_NAME ?= otsun_notebook

# Hash curt del commit Git actual (usat com a tag únic)
TAG ?= $(shell git rev-parse --short HEAD)

# Nom complet de la imatge amb tag
IMAGE ?= $(REGISTRY)/$(IMAGE_NAME):$(TAG)

# Nom de l'stack de Swarm
STACK ?= otsun-notebook

# Fitxers de configuració
BASE ?= docker-compose.base.yml
OVERRIDE ?= docker-compose.override.yml
SWARM ?= docker-compose.swarm.yml
GENERATED ?= docker-compose.generated.yml

# Mode d'execució per docker compose (p. ex. -d)
MODE ?=

# Arguments addicionals per docker stack deploy
ARGS ?=

.PHONY: build push generate up deploy clean

# 🏗️ Construcció de la imatge
build:
	docker build -t $(IMAGE) .

# 🚀 Enviament al registre
push: build
	docker push $(IMAGE)

# 🧾 Generació del fitxer docker-compose per Swarm (amb el tag substituït)
generate:
	sed "s|__TAG__|$(TAG)|g" $(SWARM) > $(GENERATED)

# 🖥️ Execució local amb docker compose
up:
	docker compose -f $(BASE) -f $(OVERRIDE) up $(MODE)

# 📦 Desplegament a Swarm
deploy: push generate
	docker stack deploy -c $(BASE) -c $(GENERATED) --with-registry-auth $(ARGS) $(STACK)

#  Eliminar fitxer temporal generat
clean:
	rm -f $(GENERATED)
	