"""Fail fast when an MSSQL master changelog references a missing file."""
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
MSSQL_DIR = ROOT / "liquibase" / "mssql"
MASTER_XML = MSSQL_DIR / "master.xml"
NS = "http://www.liquibase.org/xml/ns/dbchangelog"


def validate_master_xml():
    if not MASTER_XML.is_file():
        raise RuntimeError(f"MSSQL_CHANGELOG_INTEGRITY_ERROR: master.xml is missing: {MASTER_XML}")
    root = ET.parse(MASTER_XML).getroot()
    for include in root.findall(f"{{{NS}}}include"):
        filename = include.get("file")
        if not filename or Path(filename).name != filename or not (MSSQL_DIR / filename).is_file():
            raise RuntimeError(
                "MSSQL_CHANGELOG_INTEGRITY_ERROR: "
                f"master.xml references missing file: liquibase/mssql/{filename}"
            )
    print("MSSQL master.xml changelog integrity verified")


if __name__ == "__main__":
    try:
        validate_master_xml()
    except Exception as exc:
        print(exc, file=sys.stderr)
        raise SystemExit(1)
