from contextlib import contextmanager
import sqlite3
import logging
import os

logger = logging.getLogger(__name__)
DATABASE_URL = os.getcwd() + "/src/docker_proxy/zeta.db"


@contextmanager
def get_db_connection():
    conn = sqlite3.connect(DATABASE_URL)
    conn.row_factory = sqlite3.Row  # Enables dict-like access to rows
    try:
        yield conn
    finally:
        conn.close()


def initialize_db():
    if not os.path.isfile(DATABASE_URL):
        logger.info(f"Creating db: {DATABASE_URL}")
        open(DATABASE_URL, "x")
    create_zeta_runner_image_table()
    create_zeta_runner_container_table()
    create_zeta_function_table()


# Creation ===================================================================
def create_zeta_runner_image_table():
    """Create the `zeta_runner_image` table if it doesn't exist."""
    with get_db_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS zeta_runner_image(
                id                  TEXT PRIMARY KEY NOT NULL,
                tag                 TEXT NOT NULL
            );
        """)
        conn.commit()
        logger.info("created (if not exist) zeta runner image table")


def create_zeta_runner_container_table():
    """Create the `zeta_runner_container` table if it doesn't exist."""
    with get_db_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS zeta_runner_container(
                id                  TEXT PRIMARY KEY NOT NULL,
                name                TEXT NOT NULL,
                port                INTEGER DEFAULT 8000,
                host_port           INTEGER NOT NULL,
                host_ip             TEXT NOT NULL,
                last_heartbeat      INTEGER DEFAULT 0
            );
        """)
        conn.commit()
        logger.info("created (if not exist) zeta runner container table")


def create_zeta_function_table():
    """Create the `zeta_function` table if it doesn't exist."""
    with get_db_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS zeta_function(
                id                  INTEGER PRIMARY KEY AUTOINCREMENT,
                name                TEXT NOT NULL,
                created_at          DATETIME NOT NULL,
                runner_image_id     REFERENCES zeta_runner_image(id) NOT NULL,
                runner_container_id REFERENCES zeta_runner_container(id)
            );
        """)
        conn.commit()
        logger.info("created (if not exist) zeta function table")


# Insertions ==================================================================
def insert_zeta_runner_image(image_id: str, tag: str):
    """Insert a new zeta_runner_image into the database."""
    with get_db_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO zeta_runner_image (id, tag) VALUES (?, ?)",
            (image_id, tag)
        )
        conn.commit()
        return cursor.lastrowid


def insert_zeta_runner_container(function_name, container_id, container_name, host_port, host_ip):
    """Insert a new zeta_runner_container into the database, and link it to the zeta"""
    with get_db_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO zeta_runner_container (id, name, host_port, host_ip) VALUES (?, ?, ?, ?);
            """,
            (container_id, container_name, host_port, host_ip,)
        )
        conn.execute(
            """
            UPDATE zeta_function SET runner_container_id = ? WHERE name = ?;
            """,
            (container_id, function_name,),
        )
        conn.commit()
        return cursor.lastrowid


def insert_zeta_function(name, created_at, runner_image_id, runner_container_id):
    """Insert a new zeta_function into the database."""
    with get_db_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO zeta_function (name, created_at, runner_image_id, runner_container_id) VALUES (?, ?, ?, ?)",
            (name, created_at, runner_image_id, runner_container_id),
        )
        conn.commit()
        return cursor.lastrowid


# Fetching ===================================================================
def fetch_all_zeta_functions() -> list:
    """Fetch all zeta functions with their associated runner image and container details."""
    with get_db_connection() as conn:
        cursor = conn.execute("""
            SELECT
                zf.id,
                zf.name,
                zf.created_at,
                zri.id AS runner_image_id,
                zri.tag AS runner_image_tag,
                zrc.id AS runner_container_id,
                zrc.name AS runner_container_name,
                zrc.host_port AS runner_container_host_port,
                zrc.last_heartbeat AS runner_container_last_heartbeat
            FROM zeta_function zf
            JOIN zeta_runner_image zri ON zf.runner_image_id = zri.id
            LEFT JOIN zeta_runner_container zrc ON zf.runner_container_id = zrc.id;
        """)
        rows = cursor.fetchall()
        try:
            dict_rows = [dict(row) for row in rows]
        except Exception:
            logger.warning("No record fetched for zetas")
            dict_rows = []
        return dict_rows


def fetch_zeta_function_by_name(function_name):
    """Fetch a specific zeta function by its ID."""
    with get_db_connection() as conn:
        logger.info(f"Retrieving metadata for {function_name}")
        cursor = conn.execute("""
            SELECT
                zf.id,
                zf.name,
                zf.created_at,
                zri.id AS runner_image_id,
                zri.tag AS runner_image_tag,
                zrc.id AS runner_container_id,
                zrc.name AS runner_container_name,
                zrc.host_port AS runner_container_host_port,
                zrc.last_heartbeat AS runner_container_last_heartbeat
            FROM zeta_function zf
            JOIN zeta_runner_image zri ON zf.runner_image_id = zri.id
            LEFT JOIN zeta_runner_container zrc ON zf.runner_container_id = zrc.id
            WHERE zf.name = ?;
        """, (function_name,))
        row = cursor.fetchone()
        try:
            dict_row = dict(row)
        except Exception:
            logger.warning(f"No record fetched for {function_name}")
            dict_row = {}
        return dict_row


def check_table_contents(table_name):
    # TODO: delete thisss later
    with get_db_connection() as conn:
        cursor = conn.execute(f"SELECT * FROM {table_name};")
        rows = cursor.fetchall()
        dict_rows = [dict(row) for row in rows]
        logger.info(f"DICT : Content for table {table_name}: {dict_rows}")
        return dict_rows


def fetch_zeta_function_by_id(function_id):
    """Fetch a specific zeta function by its ID."""
    with get_db_connection() as conn:
        cursor = conn.execute("""
            SELECT
                zf.id,
                zf.name,
                zf.created_at,
                zri.id AS runner_image_id,
                zri.tag AS runner_image_tag,
                zrc.id AS runner_container_id,
                zrc.name AS runner_container_name,
                zrc.host_port AS runner_container_host_port,
                zrc.last_heartbeat AS runner_container_last_heartbeat
            FROM zeta_function zf
            JOIN zeta_runner_image zri ON zf.runner_image_id = zri.id
            JOIN zeta_runner_container zrc ON zf.runner_container_id = zrc.id
            WHERE zf.id = ?;
        """, (function_id,))
        row = cursor.fetchone()
        try:
            dict_row = dict(row)
        except Exception:
            logger.warning(f"No record fetched for {function_id}")
            dict_row = {}
        return dict_row


def fetch_all_containers_used_by_function(function_name: str):
    """Fetch all distinct containers used by zeta functions."""
    with get_db_connection() as conn:
        cursor = conn.execute("""
            SELECT DISTINCT zf.name, zrc.id, zrc.name, zrc.host_ip, zrc.host_port
            FROM zeta_function zf
            JOIN zeta_runner_container zrc ON zf.runner_container_id = zrc.id
            WHERE zf.name = ?
        """, (function_name,))
        rows = cursor.fetchall()
        try:
            dict_rows = [dict(row) for row in rows]
        except Exception:
            logger.warning("No record fetched for zetas")
            dict_rows = []
        return dict_rows


# Updating ==============================last_heartbeat=====================================
def update_zeta_runner_container_heartbeat(container_id, last_heartbeat):
    """Update the last_heartbeat for a specific zeta_runner_container."""
    with get_db_connection() as conn:
        logger.info(f"HEARTBEAT IN DB: {container_id} && {last_heartbeat}")
        logger.info(check_table_contents("zeta_runner_container"))
        conn.execute(
            "UPDATE zeta_runner_container SET last_heartbeat = ? WHERE id LIKE ?",
            (last_heartbeat, f"{container_id}%",),
        )
        conn.commit()


# Deletion ===================================================================
def delete_zeta_runner_container(function_name):
    with get_db_connection() as conn:
        cursor = conn.execute("""
            SELECT
                zrc.id AS runner_container_id
            FROM zeta_function zf
            LEFT JOIN zeta_runner_container zrc ON zf.runner_container_id = zrc.id
            WHERE zf.name = ?;
        """, (function_name,))
        row = cursor.fetchone()
        if row:
            logger.info(f"Row present for {function_name}")
            container_id = dict(row)["runner_container_id"]
            conn.execute("""
                UPDATE zeta_function SET runner_container_id = ? WHERE name = ?
            """, (container_id, function_name,))
            conn.execute("""
                DELETE FROM zeta_runner_container WHERE id = ?;
            """, (container_id,))
            conn.commit()


def delete_zeta_metadata(function_name):
    with get_db_connection() as conn:
        conn.execute("""
            DELETE FROM zeta_function WHERE name = ?;
        """, (function_name,))
        conn.commit()
