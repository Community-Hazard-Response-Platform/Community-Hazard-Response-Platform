from .logs import die, info
import sqlalchemy as sql
import pandas as pd


class DBController:
    def __init__(self, host: str, port: str, database: str, username: str, password: str):
        self.host = host
        self.port = port
        self.database = database
        self.username = username
        self.password = password
        self.uri = f"postgresql+psycopg2://{username}:{password}@{host}:{port}/{database}"
        self.engine = sql.create_engine(
            self.uri,
            connect_args={"client_encoding": "utf8"}
        )

    def select_data(self, query: str) -> pd.DataFrame:
        """This functions abstracts the `SELECT` queries

        Args:
            query (str): the select query to be executed

        Returns:
            pd.DataFrame: the selection
        """
        try:
            df = pd.read_sql(query, self.engine)
        except Exception as e:
            die(f"select_data: {e}")
        return df

    def insert_geodata(self, gdf, schema: str, table: str, srid: int = 3857, chunksize: int = 100) -> None:
        """Inserts a GeoDataFrame into a PostGIS table using WKT geometry conversion.

        Args:
            gdf (gpd.GeoDataFrame): geodataframe to insert
            schema (str): the name of the schema
            table (str): the name of the table
            srid (int): the SRID/CRS of the geometry
            chunksize (int): number of rows to insert at a time
        """
        try:
            with self.engine.connect() as con:
                tran = con.begin()
                total = len(gdf)
                for i in range(0, total, chunksize):
                    chunk = gdf.iloc[i:i + chunksize]
                    for _, row in chunk.iterrows():
                        cols = [c for c in gdf.columns if c not in ('geometry', 'id')]
                        col_str = ', '.join(cols) + ', geom'
                        placeholders = ', '.join([f':{c}' for c in cols])
                        query = sql.text(f"""
                            INSERT INTO {schema}.{table} ({col_str})
                            VALUES ({placeholders}, ST_GeomFromText(:wkt, {srid}))
                        """)
                        params = {c: row[c] for c in cols}
                        params['wkt'] = row['geometry'].wkt
                        con.execute(query, params)
                    # Dynamic progress bar - bypass logging
                    current = min(i + chunksize, total)
                    percent = current / total
                    filled = int(40 * percent)
                    bar = '#' * filled + '-' * (40 - filled)
                    msg = f"[>>] Inserting into {table} [{bar}] {current}/{total} ({percent*100:.0f}%)".ljust(100)
                    if current == total:
                        print(f"\r{msg}")
                    else:
                        print(f"\r{msg}", end='', flush=True)
                tran.commit()
        except Exception as e:
            if 'tran' in locals():
                tran.rollback()
            die(f"insert_geodata: {e}")

    def truncate_tables(self, tables: list) -> None:
        """Truncates the given tables and restarts their identity sequences.

        Args:
            tables (list): list of table names to truncate
        """
        try:
            with self.engine.connect() as con:
                tran = con.begin()
                for table in tables:
                    con.execute(sql.text(f"TRUNCATE TABLE public.{table} RESTART IDENTITY CASCADE"))
                    info(f"Truncated {table}")
                tran.commit()
        except Exception as e:
            die(f"truncate_tables: {e}")