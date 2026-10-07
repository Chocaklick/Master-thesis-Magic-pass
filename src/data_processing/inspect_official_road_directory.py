"""Read official archived GeoPackage contact attributes, never polygon centroids."""
import hashlib
import sqlite3
import sys
from pathlib import Path
from zipfile import ZipFile

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.data_processing.prepare_accessibility_road_reference import archived_metadata


def bern_contacts():
    metadata = archived_metadata("BERN_OFFICIAL_MUNICIPAL_CONTACTS_GPKG_2026")
    with ZipFile(ROOT / metadata["raw_file"]) as archive:
        names = [n for n in archive.namelist() if n.endswith(".gpkg")]
        if len(names) != 1:
            raise ValueError("Expected one official GeoPackage")
        content = archive.read(names[0])
    digest = hashlib.sha256(content).hexdigest()
    folder = ROOT / "data_interim/accessibility_road_directory"
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"bern_{digest}.gpkg"
    if not path.exists():
        with path.open("xb") as stream:
            stream.write(content)
    if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
        raise ValueError("Derived decompression differs from immutable original")
    with sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True) as connection:
        tables = connection.execute("SELECT table_name, column_name FROM gpkg_geometry_columns").fetchall()
        if len(tables) != 1:
            raise ValueError("Expected one official municipality layer")
        table, geometry = tables[0]
        quoted = '"' + table.replace('"', '""') + '"'
        columns = [r[1] for r in connection.execute(f"PRAGMA table_info({quoted})") if r[1] != geometry]
        names = ','.join('"' + n.replace('"', '""') + '"' for n in columns)
        return pd.read_sql_query(f"SELECT {names} FROM {quoted}", connection)


if __name__ == "__main__":
    frame = bern_contacts()
    print(list(frame))
    print(frame.head(3).to_string(index=False))
