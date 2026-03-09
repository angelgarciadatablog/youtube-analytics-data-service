# youtube-analytics-data-service

Capa de servicio que exporta datos de BigQuery a Cloud Storage como archivos JSON públicos,
alimentando una web personal y un dashboard de Power BI.

---

## Arquitectura

```
youtube-v3-data-pipeline (ETL)
    │
    ▼
BigQuery (dataset: angelgarciadatablog)
    │
    ▼
Cloud Functions (youtube-analytics-daily + youtube-analytics-weekly)
    │
    ▼
Cloud Storage: angelgarciadatablog-analytics (bucket público)
    │
    ├──▶ youtube-insights-dashboard (dashboard web estático en GitHub Pages)
    └──▶ Power BI (consume JSON desde Cloud Storage)
```

---

## Estructura del proyecto

```
youtube-analytics-data-service/
├── main.py                      # Entry points de Cloud Functions (daily, weekly)
├── requirements.txt             # Dependencias
├── .env                         # Variables de entorno (no commitear)
├── .gitignore
├── .gcloudignore
└── scripts/
    ├── __init__.py
    ├── bigquery_repository.py   # Queries SQL a BigQuery
    ├── storage_repository.py    # Subida de JSON a Cloud Storage
    └── server.py                # Lógica de daily_server() y weekly_server()
```

---

## Variables de entorno (.env)

```
GCP_PROJECT=youtube-datasets-360
BIGQUERY_DATASET=angelgarciadatablog
GCS_BUCKET=angelgarciadatablog-analytics
```

---

## Archivos JSON que genera

### Daily (corre a las 3:00 AM UTC)

| Archivo en Cloud Storage | Fuente en BigQuery |
|---|---|
| `daily/view-channel-growth-daily.json` | vista `view-channel-growth-daily` |
| `daily/latest_videos_current.json` | tabla `latest_videos_current` |

### Weekly (corre a las 3:30 AM UTC los lunes)

| Archivo en Cloud Storage | Fuente en BigQuery |
|---|---|
| `weekly/view-playlist-growth-weekly.json` | vista `view-playlist-growth-weekly` |
| `weekly/view-video-growth-weekly.json` | vista `view-video-growth-weekly` |
| `weekly/view-video-weekly-evolution-relevant.json` | vista `view-video-weekly-evolution-relevant` |
| `weekly/view-playlist-weekly-evolution.json` | vista `view-playlist-weekly-evolution` |
| `weekly/view-all-playlist-videos-weekly.json` | vista `view-all-playlist-videos-weekly` |

---

## Infraestructura en GCP

### Cloud Functions

| Función | Entry point | URL |
|---------|-------------|-----|
| `youtube-analytics-daily` | `daily` | https://youtube-analytics-daily-1052480639778.us-central1.run.app |
| `youtube-analytics-weekly` | `weekly` | https://youtube-analytics-weekly-1052480639778.us-central1.run.app |

> **Nota:** Las URLs de las Cloud Functions **no son accesibles públicamente**. El ingress está configurado como Internal, por lo que solo pueden ser invocadas por los Cloud Schedulers mediante autenticación OIDC. Los datos públicos se consumen directamente desde Cloud Storage (ver sección siguiente).

**Configuración de cada función:**
- Runtime: Python 3.11
- Trigger: HTTP
- Ingress: Internal (solo accesible desde Cloud Scheduler con OIDC)
- Instancias mínimas: 0 / máximas: 1
- Timeout: 300s
- Service account: `youtube-analytics-sa`

### URLs públicas de Cloud Storage

Los JSON generados son accesibles públicamente desde el bucket de Cloud Storage:

**Daily**
- https://storage.googleapis.com/angelgarciadatablog-analytics/daily/view-channel-growth-daily.json
- https://storage.googleapis.com/angelgarciadatablog-analytics/daily/latest_videos_current.json

**Weekly**
- https://storage.googleapis.com/angelgarciadatablog-analytics/weekly/view-playlist-growth-weekly.json
- https://storage.googleapis.com/angelgarciadatablog-analytics/weekly/view-video-growth-weekly.json
- https://storage.googleapis.com/angelgarciadatablog-analytics/weekly/view-video-weekly-evolution-relevant.json
- https://storage.googleapis.com/angelgarciadatablog-analytics/weekly/view-playlist-weekly-evolution.json
- https://storage.googleapis.com/angelgarciadatablog-analytics/weekly/view-all-playlist-videos-weekly.json

### Cloud Schedulers

| Scheduler | Cron | Hora UTC | Servicio que invoca |
|-----------|------|----------|---------------------|
| `youtube-daily-analytics` | `0 3 * * *` | 3:00 AM diario | `youtube-analytics-daily` |
| `youtube-weekly-analytics` | `30 3 * * 1` | 3:30 AM lunes | `youtube-analytics-weekly` |

**Configuración de reintentos:**
- Máx. reintentos: 3
- Duración mín. de retirada: 5s
- Duración máx. de retirada: 1h
- Duplicaciones máximas: 5

---

## Posición en la arquitectura

Este servicio ocupa la capa intermedia de un pipeline de tres repositorios:

| Capa | Repo | Rol |
|------|------|-----|
| 1 | `youtube-v3-data-pipeline` | ETL: extrae de la API de YouTube y carga en BigQuery |
| 2 | `youtube-analytics-data-service` | **Este repo:** exporta BigQuery → JSON en Cloud Storage |
| 3 | `youtube-insights-dashboard` | Dashboard web estático que visualiza los JSON |

Este servicio depende del pipeline ETL (`youtube-v3-data-pipeline`) que escribe los datos en BigQuery.
Los schedulers están definidos para correr **1 hora después** de que el ETL termina, garantizando que los datos ya estén disponibles.

| Evento | Repo / Scheduler | Hora UTC |
|--------|------------------|----------|
| ETL escribe en BigQuery | `youtube-v3-data-pipeline` (daily) | 2:00 AM |
| **Este repo exporta a Cloud Storage** | `youtube-daily-analytics` | **3:00 AM** |
| ETL escribe en BigQuery | `youtube-v3-data-pipeline` (weekly, lunes) | 2:30 AM |
| **Este repo exporta a Cloud Storage** | `youtube-weekly-analytics` | **3:30 AM** |
| `youtube-insights-dashboard` consume los JSON | GitHub Pages (estático) | en tiempo real |

---

## Cache-Control en Cloud Storage

Los archivos JSON se sirven con `Cache-Control: public, max-age=N` para reducir peticiones
innecesarias a Cloud Storage. El valor varía según la frecuencia de actualización de cada grupo.

| Tipo | max_age | Equivale a | Razonamiento |
|------|---------|------------|--------------|
| Daily | `14400` | 4 horas | Un usuario que cachea a las 11 PM verá los datos nuevos (3:00 AM) antes de las 7 AM |
| Weekly | `43200` | 12 horas | Los domingos hay lives con tráfico alto — los viewers verán la actualización del lunes por la mañana |

El `max_age` es el valor por defecto en `upload_dataframe_as_json()`. Las llamadas weekly
lo sobreescriben explícitamente pasando `max_age=43200`.

### Control manual desde el frontend

A pesar del caché automático, la web puede ofrecer un botón para forzar datos frescos.
Al añadir un timestamp a la URL, el navegador ignora su caché y consulta Cloud Storage directamente:

```javascript
// El navegador trata esta URL como nueva → bypasea el caché local
const url = `https://storage.googleapis.com/.../daily/latest_videos_current.json?t=${Date.now()}`;
const response = await fetch(url);
```

Esto no afecta a otros usuarios ni invalida nada en Cloud Storage — solo fuerza una petición fresca para ese cliente.

---

## Cómo probar localmente

```bash
# Activar entorno virtual
source .venv/bin/activate

# Autenticarse con GCP
gcloud auth application-default login

# Ejecutar
python test.py
```
