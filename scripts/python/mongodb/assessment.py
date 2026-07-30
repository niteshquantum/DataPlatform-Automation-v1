"""MongoDB assessment inventories for databases, collections, and indexes."""

import argparse

from scripts.python.common.assessment import run_selected, write_inventory
from scripts.python.mongodb.setup.db_connection import get_client, get_db


def database_inventory():
    client = get_client()
    try:
        return [{"database_name": item["name"], "size_on_disk": item.get("sizeOnDisk"), "empty": item.get("empty", False)} for item in client.list_databases()]
    finally:
        client.close()


def collection_inventory():
    database = get_db()
    try:
        return [{"collection_name": item["name"], "collection_type": item.get("type", "collection"), "options": item.get("options", {})} for item in database.list_collections()]
    finally:
        database.client.close()


def index_inventory():
    database = get_db()
    try:
        rows = []
        for collection in database.list_collection_names():
            for index in database[collection].list_indexes():
                index = dict(index)
                rows.append({"collection_name": collection, "index_name": index.get("name"), "key": dict(index.get("key", {})), "unique": index.get("unique", False), "sparse": index.get("sparse", False)})
        return rows
    finally:
        database.client.close()


INVENTORIES = {"database": database_inventory, "collection": collection_inventory, "index": index_inventory}


def run(inventory):
    return write_inventory("mongodb", inventory, INVENTORIES[inventory]())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run a MongoDB assessment inventory")
    parser.add_argument("inventory", choices=[*INVENTORIES, "all"])
    run_selected(run, list(INVENTORIES), parser.parse_args().inventory)
