import json, runpy, shutil
from pathlib import Path
from tempfile import TemporaryDirectory

with TemporaryDirectory() as tmp_dir:
    root = Path(tmp_dir)
    (root/'metadata'/'mssql').mkdir(parents=True)
    (root/'liquibase'/'mssql').mkdir(parents=True)
    (root/'metadata'/'mssql'/'schema_registry.json').write_text(json.dumps({'orders':['id','amount','obsolete']}), encoding='utf-8')
    (root/'metadata'/'mssql'/'datatype_registry.json').write_text(json.dumps({'orders': {'id': {'final_type': 'INTEGER'}, 'amount': {'selected_type':'VARCHAR(255)'}, 'obsolete': {'detected_type':'DATE'}}}), encoding='utf-8')
    src = Path('f:/Team_D/automation-merge/c77b38a-code/scripts/python/mssql/setup/generate_liquibase_xml.py')
    dst = root/'scripts'/'python'/'mssql'/'setup'/'generate_liquibase_xml.py'
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_bytes(src.read_bytes())
    import sys
    sys.path.insert(0, str(root))
    runpy.run_path(str(dst), run_name='__main__')
    p = root/'liquibase'/'mssql'/'mssql-create-orders.xml'
    print(p.read_text(encoding='utf-8'))
