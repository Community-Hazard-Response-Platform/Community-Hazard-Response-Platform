from .logs import die
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

    def select_data(self, query: str) -> pd.DataFrame:
        """This functions abstracts the `SELECT` queries

        Args:
            query (str): the select query to be executed

        Returns:
            pd.DataFrame: the selection
        """
        try:
            con = sql.create_engine(self.uri)
            df = pd.read_sql(query, con)
        except Exception as e:
            die(f"select_data: {e}")
        return df

    def insert_data(self, df: pd.DataFrame, schema: str, table: str, chunksize: int=100) -> None:
        """This function abstracts the `INSERT` queries

        Args:
            df (pd.DataFrame): dataframe to be inserted
            schema (str): the name of the schema
            table (str): the name of the table
            chunksize (int): the number of rows to insert at the time
        """
        try:
            engine = sql.create_engine(self.uri)
            with engine.connect() as con:
                tran = con.begin()
                df.to_sql(
                    name=table, schema=schema,
                    con=con, if_exists="append", index=False,
                    chunksize=chunksize, method="multi"
                )
                tran.commit()
        except Exception as e:
            if 'tran' in locals():
                tran.rollback()
            die(f"{e}")

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
            engine = sql.create_engine(
                self.uri,
                connect_args={"client_encoding": "utf8"}  # ADD THIS
            )
            with engine.connect() as con:
                tran = con.begin()
                for i in range(0, len(gdf), chunksize):
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
                tran.commit()
        except Exception as e:
            if 'tran' in locals():
                tran.rollback()
            die(f"insert_geodata: {e}")