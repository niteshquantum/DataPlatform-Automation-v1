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

current_order = []
for include_elem in root.findall(f"{{{NS}}}include"):
    filename = include_elem.get("file")
    if filename:
        current_order.append(Path(filename).name)

# Scan all XML files except master.xml
xml_files = sorted(
    f for f in mssql_dir.glob("*.xml")
    if f.name != "master.xml"
)
xml_names = [f.name for f in xml_files]

include_order = [name for name in current_order if name in xml_names]
include_order += [name for name in xml_names if name not in include_order]

if include_order == current_order:
    print("master.xml is already up to date")
else:
    for include_elem in root.findall(f"{{{NS}}}include"):
        root.remove(include_elem)

    for relative_path in include_order:
        include_elem = ET.SubElement(root, f"{{{NS}}}include")
        include_elem.set("file", relative_path)
        include_elem.set("relativeToChangelogFile", "true")
        print(f"Added {relative_path}")

    tree.write(
        master_xml,
        encoding="utf-8",
        xml_declaration=True
)

print("\nmaster.xml updated successfully")