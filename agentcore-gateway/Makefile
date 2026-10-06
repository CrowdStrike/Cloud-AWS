IMAGE  ?= aidr-agentcore-interceptor
TAG    ?= latest
DOCKER ?= podman   # override with DOCKER=docker if needed

.PHONY: setup test build push ecr-login

setup:
	pip install -r requirements-dev.txt

test:
	pytest tests/ -v

build:
	$(DOCKER) build -t $(IMAGE):$(TAG) .

ecr-login:
	aws ecr get-login-password --region $(AWS_REGION) \
	  | $(DOCKER) login --username AWS --password-stdin $(REPO_URI)

push: ecr-login
	$(DOCKER) push $(IMAGE):$(TAG)
