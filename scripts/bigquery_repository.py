import os
from google.cloud import bigquery
from dotenv import load_dotenv

load_dotenv()


# CLASE: cajón que agrupa todo lo relacionado con BigQuery en un solo sitio.
class BigQueryRepository:

    # __init__: lo primero que se ejecuta al abrir el cajón.
    # Conecta con BigQuery y guarda el proyecto y dataset.
    def __init__(self):
        project = os.getenv("GCP_PROJECT")
        if not project:
            raise ValueError("GCP_PROJECT no definido")
        # self: forma de decir "guarda esto dentro del cajón para usarlo después".
        self.client = bigquery.Client(project=project)
        self.dataset = os.getenv("BIGQUERY_DATASET", "angelgarciadatablog")


    # MÉTODO GENÉRICO: función reutilizable para cualquier tabla con SELECT *.
    # El nombre de la tabla lo decides tú al llamarla desde server.py o test.py.
    # Parámetro (table_name): el hueco que tú rellenas cuando llamas a la función.
    def get_all_table_as_df(self, table_name):
        query = f"SELECT * FROM `{self.client.project}.{self.dataset}.{table_name}`"
        # return: ejecuta la query y devuelve el resultado como tabla de Python (DataFrame).
        return self.client.query(query).to_dataframe()



    # MÉTODO ESPECÍFICO: función con su propio SQL.
    # Úsalo cuando necesitas filtros, ORDER BY, LIMIT, etc.

    def get_view_playlist_weekly_evolution(self):
        query = f"""
            SELECT *
            FROM `{self.client.project}.{self.dataset}.view-playlist-weekly-evolution`
            WHERE is_baseline = FALSE
            ORDER BY playlist_id, snapshot_date ASC
        """
        return self.client.query(query).to_dataframe()

    # ─────────────────────────────────────────────────────────────────
    # Si tienes una consulta personalizada, agrégala como método nuevo
    # siguiendo este mismo patrón:
    #
    #   def nombre_descriptivo(self):
    #       query = f"""
    #           TU CONSULTA SQL AQUÍ
    #       """
    #       return self.client.query(query).to_dataframe()
    # ─────────────────────────────────────────────────────────────────