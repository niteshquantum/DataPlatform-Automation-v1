from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[4]

liquibase_dir = ROOT / "liquibase"
mssql_dir = liquibase_dir / "mssql"
master_xml = mssql_dir / "master.xml"

NS = "http://www.liquibase.org/xml/ns/dbchangelog"
ET.register_namespace("", NS)

# Create master.xml if it doesn't exist
if not master_xml.exists():

    root = ET.Element(
        "databaseChangeLog",
        {
            "xmlns": "http://www.liquibase.org/xml/ns/dbchangelog",
            "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
            "xsi:schemaLocation":
                "http://www.liquibase.org/xml/ns/dbchangelog "
                "https://www.liquibase.org/xml/ns/dbchangelog/dbchangelog-latest.xsd"
        }
    )

    tree = ET.ElementTree(root)
    tree.write(master_xml, encoding="utf-8", xml_declaration=True)

# Load master.xml
tree = ET.parse(master_xml)
root = tree.getroot()

# Remove all existing includes
for include_elem in root.findall(f"{{{NS}}}include"):
    root.remove(include_elem)

# Scan all XML files except master.xml
xml_files = sorted(
    f for f in mssql_dir.glob("*.xml")
    if f.name != "master.xml"
)

for xml_file in xml_files:

    relative_path = xml_file.name

    include_elem = ET.SubElement(
        root,
        f"{{{NS}}}include"
    )

    include_elem.set("file", relative_path)

    # IMPORTANT
    include_elem.set(
        "relativeToChangelogFile",
        "true"
    )

    print(f"Added {relative_path}")

# Save
tree.write(
    master_xml,
    encoding="utf-8",
    xml_declaration=True
)

print("\nmaster.xml updated successfully")