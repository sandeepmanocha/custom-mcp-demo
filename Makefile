# Mock Collibra Pre-Flight MCP — Databricks App
#
# Override profile/target at deploy time:
#   make all DB_TARGET=dev DB_PROFILE=YOUR_PROFILE

DB_PROFILE ?= DEFAULT
DB_TARGET  ?= dev
APP_NAME   ?= mcp-collibra-preflight-demo
APP_RESOURCE ?= collibra_preflight_app

GREEN  := \033[32m
DIM    := \033[2m
RED    := \033[31m
RESET  := \033[0m

.PHONY: local-server test validate deploy app-deploy deploy-full smoke all help

local-server: ## Start MCP server on DATABRICKS_APP_PORT or 8000
	@printf "$(GREEN)>>> starting local MCP server$(RESET)\n"
	uv run collibra-preflight-server

test: ## Run unit tests
	@printf "$(GREEN)>>> pytest$(RESET)\n"
	uv run pytest -q

validate: ## Strictly validate the Databricks bundle
	@printf "$(GREEN)>>> validating Databricks bundle$(RESET)\n"
	databricks bundle validate --strict -t $(DB_TARGET) -p $(DB_PROFILE) --var databricks_profile=$(DB_PROFILE)

deploy: validate ## Bundle deploy (uploads code)
	@printf "$(GREEN)>>> databricks bundle deploy -t $(DB_TARGET)$(RESET)\n"
	databricks bundle deploy -t $(DB_TARGET) -p $(DB_PROFILE) --var databricks_profile=$(DB_PROFILE)

app-deploy: ## Apply app config and start it through the bundle
	@printf "$(GREEN)>>> databricks bundle run $(APP_RESOURCE) -t $(DB_TARGET)$(RESET)\n"
	databricks bundle run $(APP_RESOURCE) -t $(DB_TARGET) -p $(DB_PROFILE) --var databricks_profile=$(DB_PROFILE)

deploy-full: deploy app-deploy ## Validate, upload, and start app through DABs

smoke: ## Verify deployed app is running
	@APP_JSON=$$(databricks apps get $(APP_NAME) --profile $(DB_PROFILE) --output json 2>/dev/null); \
	APP_URL=$$(echo "$$APP_JSON" | python3 -c "import sys,json;print(json.load(sys.stdin).get('url',''))"); \
	STATUS=$$(echo "$$APP_JSON" | python3 -c "import sys,json;d=json.load(sys.stdin);s=d.get('app_status',d.get('status',{}));print(s.get('state',s.get('status','UNKNOWN')) if isinstance(s, dict) else s)"); \
	if [ -z "$$APP_URL" ]; then printf "$(RED)ERROR: could not get app URL$(RESET)\n"; exit 1; fi; \
	printf "App URL:    $$APP_URL\n"; \
	printf "MCP URL:    $$APP_URL/mcp\n"; \
	printf "App status: $$STATUS\n"; \
	if [ "$$STATUS" = "RUNNING" ]; then \
		printf "$(GREEN)PASS: app is running$(RESET)\n"; \
	else \
		printf "$(RED)WARN: app status is $$STATUS$(RESET)\n"; \
		exit 1; \
	fi

all: test deploy-full smoke ## Full pipeline: test + deploy + smoke

.DEFAULT_GOAL := help

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-16s %s\n", $$1, $$2}'
