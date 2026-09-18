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

## 1. Clone and run tests locally

```bash
git clone https://github.com/sandeepmanocha/custom-mcp-demo.git
cd custom-mcp-demo
uv sync --group dev
uv run pytest -q
```

## 2. Run the MCP server locally

```bash
make local-server
```

In another terminal:

```bash
curl -s http://localhost:8000/health
```

MCP endpoint: `http://localhost:8000/mcp`

## 3. Authenticate to Databricks

```bash
databricks auth login --host https://YOUR_WORKSPACE.cloud.databricks.com --profile YOUR_PROFILE
databricks auth profiles   # confirm the profile is Valid
```

Set the profile when you deploy:

```bash
export DB_PROFILE=YOUR_PROFILE
```

Or pass it on every `make` command: `make all DB_PROFILE=YOUR_PROFILE`.

`databricks.yml` uses `workspace.profile` (no hardcoded workspace host). The CLI profile supplies the host.

## 4. Deploy as a Databricks App

App name must start with `mcp-` so AI Playground can discover it.

```bash
make all DB_PROFILE=YOUR_PROFILE
```

That runs:

1. `pytest`
2. `databricks bundle validate --strict`
3. `databricks bundle deploy` (creates/uploads the app)
4. `databricks bundle run collibra_preflight_app` (starts the app)
5. `databricks apps get` smoke check

Redeploy after code changes with the same command.

If `uv.lock` is generated on a machine that uses an internal PyPI proxy, rewrite package URLs to `files.pythonhosted.org` before deploy. Databricks Apps cannot reach some private indexes.

## 5. Try it in AI Playground

1. Open **AI Playground** in your workspace.
2. Pick a **Tools enabled** model. Do **not** use GPT-5.6 Sol with default reasoning — it rejects function tools on `/v1/chat/completions`. Use Claude Sonnet or set `reasoning_effort` to `none`.
3. **Tools → Add tool** → select `mcp-collibra-preflight-demo`.
4. Prompts:
   - `Perform a pre-flight check on the CLAIMS data product.`
   - `Now check the REVENUE data product.`
   - `List all available data products.`

MCP URL after deploy: `{app.url}/mcp/` (trailing slash).

Logs: `{app.url}/logz` or `databricks apps logs mcp-collibra-preflight-demo -p YOUR_PROFILE`.

## 6. Connect Claude Code (optional)

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

## Makefile

| Target | Action |
| --- | --- |
| `make test` | Run pytest |
| `make local-server` | Serve on port 8000 |
| `make validate` | Bundle validate |
| `make deploy` | Upload via DABs |
| `make app-deploy` | Start the app |
| `make smoke` | Print URL and assert RUNNING |
| `make all` | test + deploy + start + smoke |

## Swap mock Collibra for real Collibra

`get_data_product()` in `server/tools.py` is the only lookup. Replace it with an HTTP call to `https://<instance>.collibra.com/rest/2.0/assets`. Tool signatures and check logic stay the same.

## Layout

```
app.yaml              Databricks Apps command
databricks.yml        DABs bundle
resources/app.yml     App resource
server/app.py         FastAPI + FastMCP (stateless HTTP)
server/tools.py       Mock data + MCP tools
Makefile
```
