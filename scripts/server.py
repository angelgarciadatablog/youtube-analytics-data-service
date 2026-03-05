from scripts.bigquery_repository import BigQueryRepository
from scripts.storage_repository import StorageRepository


def daily_server():
    bq = BigQueryRepository()
    storage = StorageRepository()

    # ── BLOQUE DAILY - SELECT*FROM ──────────────────────────────────────────────────────────────
    # Llama al método get_all_table_as_df() (de la clase BigQueryRepository) pasando el nombre de la tabla como parámetro.
    # Asigna el resultado (DataFrame) a la variable latest_videos.
    #1
    channel_growth_daily = bq.get_all_table_as_df("view-channel-growth-daily")
    storage.upload_dataframe_as_json(channel_growth_daily, "daily/view-channel-growth-daily.json")

    #2
    latest_videos_current = bq.get_all_table_as_df("latest_videos_current")
    storage.upload_dataframe_as_json(latest_videos_current, "daily/latest_videos_current.json")

    # ── AQUÍ AÑADES TUS CONSULTAS DAILY ───────────────────────────────────────
    # Patrón A (tabla entera):
    #   df = bq.get_table_as_dataframe("nombre_tabla_en_bigquery")
    #   storage.upload_dataframe_as_json(df, "nombre_archivo_de_salida.json")


 


def weekly_server():
    bq = BigQueryRepository()
    storage = StorageRepository()

    # ── BLOQUE WEEKLY SELECT*FROM ─────────────────────────────────────────────────────────
    # Igual que el bloque 1 del daily, llama a get_all_table_as_df() por cada vista.
    # En vez de hacerlo por separado, usa un bucle for — cada tupla es:
    # ("nombre_en_bigquery", "nombre_archivo_de_salida.json")
    tables = [
        ("view-playlist-growth-weekly", "weekly/view-playlist-growth-weekly.json"),
        ("view-video-growth-weekly", "weekly/view-video-growth-weekly.json"),
        ("view-video-weekly-evolution-relevant", "weekly/view-video-weekly-evolution-relevant.json"),
        ("view-all-playlist-videos-weekly", "weekly/view-all-playlist-videos-weekly.json")
        
    ]

    for table_name, filename in tables:
        df = bq.get_all_table_as_df(table_name)
        storage.upload_dataframe_as_json(df, filename, max_age=43200)

    # ── BLOQUE WEEKLY PERSONALIZADO ─────────────────────────────────────────────────────────

    # Consulta personalizada — llama al método específico de bigquery_repository.py
    playlist_weekly_evolution = bq.get_view_playlist_weekly_evolution()
    storage.upload_dataframe_as_json(playlist_weekly_evolution, "weekly/view-playlist-weekly-evolution.json", max_age=43200)

    
    # ── AQUÍ AÑADES TUS CONSULTAS WEEKLY ───────────────────────────────────────
    # Patrón A (consulta personalizada):
    #   df = bq.tu_metodo_personalizado()
    #   storage.upload_dataframe_as_json(df, "weekly/nombre_archivo.json")
    # ──────────────────────────────────────────────────────────────────────────
