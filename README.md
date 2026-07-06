# otel-observability

Serviço em **Python + FastAPI** instrumentado com **OpenTelemetry** (traces +
métricas **RED**) e um **stack de observabilidade completo** via docker-compose:
OpenTelemetry Collector → **Tempo** (traces) e **Prometheus** (métricas) →
**Grafana** com dashboard **provisionado**. A telemetria fica atrás de uma
**porta**, então a lógica de negócio roda offline nos testes — com **cobertura
100%**.

```
  FastAPI app ──(OTLP)──▶ OTel Collector ──▶ Tempo      (traces)
                                        └──▶ Prometheus (métricas RED) ──▶ Grafana
```

## Destaques

- **Métricas RED** — **R**ate (req/s), **E**rrors (% de 4xx/5xx) e **D**uration
  (latência p95), coletadas por um middleware e expostas num dashboard pronto.
- **Traces distribuídos** — cada caso de uso (`task.create`, `task.complete`)
  abre um span com atributos, exportado para o Tempo.
- **Observabilidade atrás de uma porta** — a interface `Telemetry` isola o
  domínio. Nos testes usa-se `NoopTelemetry` (sem rede); em produção,
  `OtelTelemetry` exporta via OTLP. Trocar um pelo outro não toca na lógica.
- **Stack provisionado** — sobe com um comando: Collector, Tempo, Prometheus e
  Grafana já conectados, com datasources e dashboard versionados no repo.
- **Arquitetura em camadas** — domínio (tarefa) → aplicação (serviço + portas) →
  infraestrutura (store em memória, telemetria) → API.
- **Cobertura 100%** — verificada na CI. O adapter OTel (rede/collector) fica
  fora da métrica.
- **OpenAPI/Swagger** — documentação interativa em `/docs`.

## Stack

- **Linguagem:** Python 3.12 · **Framework:** FastAPI (Uvicorn)
- **Observabilidade:** OpenTelemetry SDK (OTLP) · Collector · Tempo · Prometheus · Grafana
- **Testes/cobertura:** pytest + pytest-cov (gate de 100%) · **Lint:** ruff

## Arquitetura

```
app/
├── domain/          # Task + validação (Python puro)
├── application/     # TaskService + ports (TaskStore, Telemetry)
├── infrastructure/  # store em memória, NoopTelemetry, OtelTelemetry
├── api/             # FastAPI: rotas, DTOs, middleware de métricas
└── main.py          # composição (bootstrap)
observability/       # config do Collector, Tempo, Prometheus e Grafana
```

## Como rodar

### Só a API (offline, sem telemetria)

```bash
python -m venv .venv && . .venv/Scripts/activate   # (Linux/mac: source .venv/bin/activate)
pip install -r requirements.txt
uvicorn app.main:app --reload      # http://localhost:8080  (Swagger em /docs)
```

### Stack completo (API + Collector + Tempo + Prometheus + Grafana)

```bash
docker compose up --build
# Grafana:     http://localhost:3000  (dashboard "otel-observability — RED")
# Prometheus:  http://localhost:9090
```

Gere carga e veja os gráficos reagirem:

```bash
for i in $(seq 1 50); do
  curl -s -X POST localhost:8080/tasks -H "Content-Type: application/json" -d '{"title":"tarefa"}' >/dev/null
done
curl -s -X POST localhost:8080/tasks -H "Content-Type: application/json" -d '{"title":""}'   # gera um erro 400
```

## Endpoints

| Método | Rota                     | Descrição                    |
| ------ | ------------------------ | ---------------------------- |
| POST   | `/tasks`                 | Cria uma tarefa (`title`)    |
| GET    | `/tasks`                 | Lista as tarefas             |
| POST   | `/tasks/{id}/complete`   | Conclui uma tarefa           |
| GET    | `/health`                | Health check                 |
| GET    | `/docs`                  | Swagger UI                   |

## Métricas expostas

| Métrica                        | Tipo      | Uso no dashboard          |
| ------------------------------ | --------- | ------------------------- |
| `http_requests_total`          | counter   | Rate e Error rate         |
| `http_request_duration_ms`     | histogram | Duration (p95)            |

## Testes e cobertura

```bash
pip install -r requirements-dev.txt
pytest                 # exige 100% (configurado no pyproject.toml)
ruff check . && ruff format --check .
```

## Licença

MIT.
