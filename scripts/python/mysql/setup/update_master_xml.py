from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[4]

liquibase_dir = ROOT / "liquibase"
mysql_dir = liquibase_dir / "mysql"
master_xml = mysql_dir / "master.xml"

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

# Preserve historical include order.  Existing includes are changelog history;
# only append changelogs that have not yet been included.  A duplicate include
# is removed because it would cause Liquibase to process the same file twice.
xml_files = sorted(
    f for f in mysql_dir.glob("*.xml")
    if f.name not in {"master.xml", "master_objects.xml"}
)
existing_includes = [
    elem.get("file")
    for elem in root.findall(f"{{{NS}}}include")
    if elem.get("file")
]
desired_includes = []
for include in existing_includes:
    if include not in desired_includes:
        desired_includes.append(include)
for xml_file in xml_files:
    if xml_file.name not in desired_includes:
        desired_includes.append(xml_file.name)

if existing_includes == desired_includes:
    print("master.xml already up to date")
else:
    # Remove all existing includes so the file can be rebuilt deterministically.
    for include_elem in list(root.findall(f"{{{NS}}}include")):
        root.remove(include_elem)

    for relative_path in desired_includes:
        include_elem = ET.SubElement(
            root,
            f"{{{NS}}}include"
        )

        include_elem.set("file", relative_path)
        include_elem.set("relativeToChangelogFile", "true")
        print(f"Added {relative_path}")

    tree.write(
        master_xml,
        encoding="utf-8",
        xml_declaration=True
    )

    print("\nmaster.xml updated successfully")
