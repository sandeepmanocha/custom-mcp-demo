# Mock Collibra Pre-Flight MCP

A Databricks App that exposes Collibra-style data-product pre-flight tools over [MCP](https://modelcontextprotocol.io). It uses **in-memory mock data** — no Collibra instance is required.

Demo outcomes:

| Data product | Pre-flight result |
| --- | --- |
| `CLAIMS` | Pass |
| `CUSTOMER` | Pass (accuracy warning on the quality tool) |
| `REVENUE` | Fail (uncertified, stale, expired contract, SLA miss) |

## Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/)
- [Databricks CLI](https://docs.databricks.com/aws/en/dev-tools/cli/install) ≥ 0.239
- A Databricks workspace with **Apps** enabled
- Permission to create Databricks Apps

App name must start with `mcp-` so AI Playground can discover it.

Official docs:

- [Create a custom Databricks app](https://docs.databricks.com/aws/en/dev-tools/databricks-apps/create-custom-app) — create the app record; custom apps are **not** deployed automatically.
- [Deploy a Databricks app](https://docs.databricks.com/aws/en/dev-tools/databricks-apps/deploy) — upload source, install dependencies, start the process.
- [Configure execution with `app.yaml`](https://docs.databricks.com/aws/en/dev-tools/databricks-apps/app-runtime)

## Why `app.yaml` (and `resources/app.yml`)

Databricks Apps looks at the **root of the source directory** you deploy. Two YAML files in this repo do different jobs.

**[`app.yaml`](app.yaml)** — Apps **runtime**. Databricks reads this after it installs dependencies. Without it, a Python-only app defaults to `python <first .py file>` ([deployment logic](https://docs.databricks.com/aws/en/dev-tools/databricks-apps/deploy#deployment-logic)), which is wrong for this MCP server. This file tells the runtime:

- `command: [uv, run, collibra-preflight-server]` — entry point from `pyproject.toml` (`server.main:main`), bound in code to `DATABRICKS_APP_PORT` / 8000.
- `env.UV_DEFAULT_INDEX` — install packages from public PyPI.

`requirements.txt` contains only `uv`. The platform `pip install`s that, then the `command` uses `uv run` against `pyproject.toml` + `uv.lock`. That matches the documented Python path: `requirements.txt` **or** `pyproject.toml` + `uv.lock`.

**[`resources/app.yml`](resources/app.yml)** — **DABs only**. It is *not* the Apps runtime file. Bundle deploy uses it to create the app resource (`name`, `description`, `source_code_path`). If you deploy with `databricks apps create` / `sync` / `apps deploy`, you can ignore this file.

The file must sit at the project root and may be `.yaml` or `.yml`. See [app.yaml settings](https://docs.databricks.com/aws/en/dev-tools/databricks-apps/app-runtime).

## 1. Clone and run tests locally

```bash
git clone https://github.com/sandeepmanocha/custom-mcp-demo.git
cd custom-mcp-demo
uv sync --group dev
uv run pytest -q
```

## 2. Run the MCP server locally

```bash
uv run collibra-preflight-server
```

In another terminal:

```bash
curl -s http://localhost:8000/health
```

MCP endpoint: `http://localhost:8000/mcp`

## 3. Authenticate to Databricks

```bash
databricks auth login --host https://YOUR_WORKSPACE.cloud.databricks.com --profile YOUR_PROFILE
databricks auth profiles
```

Use `-p YOUR_PROFILE` on every CLI command below.

## 4. Deploy with Databricks Apps CLI

Matches [create a custom app](https://docs.databricks.com/aws/en/dev-tools/databricks-apps/create-custom-app) then [deploy from a workspace folder](https://docs.databricks.com/aws/en/dev-tools/databricks-apps/deploy#deploy-from-a-workspace-folder): create the app, sync files, deploy. Databricks does not auto-deploy custom code.

```bash
export APP_NAME=mcp-collibra-preflight-demo
export PROFILE=YOUR_PROFILE

databricks apps create $APP_NAME \
  --description "Mock Collibra pre-flight check MCP server" \
  -p $PROFILE

DATABRICKS_USERNAME=$(databricks current-user me -p $PROFILE | jq -r .userName)

databricks workspace mkdirs "/Workspace/Users/$DATABRICKS_USERNAME/$APP_NAME" -p $PROFILE

databricks sync . "/Users/$DATABRICKS_USERNAME/$APP_NAME" -p $PROFILE

databricks apps deploy $APP_NAME \
  --source-code-path "/Workspace/Users/$DATABRICKS_USERNAME/$APP_NAME" \
  -p $PROFILE
```

Check status, URL, and logs:

```bash
databricks apps get $APP_NAME -p $PROFILE
databricks apps logs $APP_NAME -p $PROFILE
```

The MCP endpoint is `{app.url}/mcp/` (trailing slash).

Redeploy after code changes:

```bash
databricks sync . "/Users/$DATABRICKS_USERNAME/$APP_NAME" -p $PROFILE
databricks apps deploy $APP_NAME \
  --source-code-path "/Workspace/Users/$DATABRICKS_USERNAME/$APP_NAME" \
  -p $PROFILE
```

If `uv.lock` was generated against an internal PyPI proxy, rewrite package URLs to `files.pythonhosted.org` before deploy. Databricks Apps cannot reach some private indexes.

## 5. Deploy with Makefile (DABs)

Use this if you want Databricks Asset Bundles to own the app resource. `databricks.yml` uses `workspace.profile` (no hardcoded host).

```bash
make all DB_PROFILE=YOUR_PROFILE
```

That runs tests, `databricks bundle validate`, `databricks bundle deploy`, `databricks bundle run collibra_preflight_app`, then a smoke check.

| Target | Action |
| --- | --- |
| `make test` | Run pytest |
| `make local-server` | `uv run collibra-preflight-server` |
| `make validate` | `databricks bundle validate --strict` |
| `make deploy` | `databricks bundle deploy` |
| `make app-deploy` | `databricks bundle run collibra_preflight_app` |
| `make smoke` | `databricks apps get` and assert RUNNING |
| `make all` | test + deploy + start + smoke |

Equivalent DAB commands without Make:

```bash
databricks bundle validate --strict -t dev -p YOUR_PROFILE --var databricks_profile=YOUR_PROFILE
databricks bundle deploy -t dev -p YOUR_PROFILE --var databricks_profile=YOUR_PROFILE --auto-approve
databricks bundle run collibra_preflight_app -t dev -p YOUR_PROFILE --var databricks_profile=YOUR_PROFILE
databricks apps get mcp-collibra-preflight-demo -p YOUR_PROFILE
```

## 6. Try it in AI Playground

1. Open **AI Playground** in your workspace.
2. Pick a **Tools enabled** model. Do **not** use GPT-5.6 Sol with default reasoning — it rejects function tools on `/v1/chat/completions`. Use Claude Sonnet or set `reasoning_effort` to `none`.
3. **Tools → Add tool** → select `mcp-collibra-preflight-demo`.
4. Prompts:
   - `Perform a pre-flight check on the CLAIMS data product.`
   - `Now check the REVENUE data product.`
   - `List all available data products.`

Logs: `{app.url}/logz` or `databricks apps logs mcp-collibra-preflight-demo -p YOUR_PROFILE`.

## 7. Connect Claude Code (optional)

Databricks Apps MCP servers need **OAuth**, not a PAT. See [Connect MCPs to AI assistants](https://docs.databricks.com/aws/en/agents/mcp-tools/connect-clients).

1. Grant yourself **Can Use** on the app.
2. Have an account admin create a Databricks OAuth app with redirect `http://localhost:8080/callback`.
3. Register the server:

```bash
claude mcp add-json collibra-preflight \
  '{"type":"http","url":"https://YOUR_APP.aws.databricksapps.com/mcp/","oauth":{"clientId":"<oauth-client-id>","callbackPort":8080}}'
```

## Tools

| Tool | Role |
| --- | --- |
| `preflight_check` | Eight governance / quality / compliance checks |
| `list_data_products` | CLAIMS, CUSTOMER, REVENUE |
| `get_data_product_details` | Metadata + quality scores |
| `get_lineage` | Upstream / downstream (mocked) |
| `check_data_quality` | Dimension scores |
| `health` | Server liveness |

## Swap mock Collibra for real Collibra

`get_data_product()` in `server/tools.py` is the only lookup. Replace it with an HTTP call to `https://<instance>.collibra.com/rest/2.0/assets`. Tool signatures and check logic stay the same.

## Layout

```
app.yaml              Apps runtime: command + env (required for this server)
databricks.yml        DABs bundle (Makefile path)
resources/app.yml     DAB app resource (Makefile path only)
server/app.py         FastAPI + FastMCP (stateless HTTP)
server/tools.py       Mock data + MCP tools
requirements.txt      `uv` (Apps pip-installs this first)
pyproject.toml        Package + `collibra-preflight-server` script
Makefile
```
