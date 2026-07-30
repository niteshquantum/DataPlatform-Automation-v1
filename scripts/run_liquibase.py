#!/usr/bin/env python
"""
Run Liquibase Script

Scans liquibase/generated/ for XML files, executes them using Liquibase,
and moves files to archive/ or failed/ based on execution status.
Supports PostgreSQL, MySQL, and MSSQL.
"""

import json
import logging
import platform
import subprocess
from pathlib import Path
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_config(config_path):
    """
    Load database configuration from config file.
    
    Args:
        config_path: Path to config file
        
    Returns:
        Dictionary with configuration
    """
    config = {}
    try:
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        if '=' in line:
                            key, value = line.split('=', 1)
                            config[key.strip()] = value.strip()
            logger.info(f"Loaded config from {config_path.name}")
            return config
        else:
            logger.warning(f"Config file not found: {config_path}")
            return {}
    except Exception as e:
        logger.error(f"Error loading config from {config_path}: {e}")
        return {}


def get_database_url(db_type, config):
    """
    Build database URL based on type and configuration.
    
    Args:
        db_type: Type of database (mysql, postgresql, mssql)
        config: Configuration dictionary
        
    Returns:
        Database URL string
    """
    if db_type.lower() == 'mysql':
        host = config.get('MYSQL_HOST', 'localhost')
        port = config.get('MYSQL_PORT', '3306')
        database = config.get('MYSQL_DB', '')
        user = config.get('MYSQL_USER', 'root')
        password = config.get('MYSQL_PASSWORD', '')
        
        return f"jdbc:mysql://{host}:{port}/{database}?user={user}&password={password}"
    
    elif db_type.lower() == 'postgresql':
        host = config['POSTGRESQL_HOST']
        port = config['POSTGRESQL_PORT']
        database = config['POSTGRESQL_DB']
        user = config['POSTGRESQL_USER']
        password = config['POSTGRESQL_PASSWORD']
        
        return f"jdbc:postgresql://{host}:{port}/{database}?user={user}&password={password}"
    
    elif db_type.lower() == 'mssql':
        host = config.get('MSSQL_HOST', 'localhost')
        port = config.get('MSSQL_PORT', '1433')
        database = config.get('MSSQL_DB', '')
        user = config.get('MSSQL_USER', 'sa')
        password = config.get('MSSQL_PASSWORD', '')
        
        return f"jdbc:sqlserver://{host}:{port};databaseName={database};user={user};password={password}"
    
    return None


def execute_liquibase(xml_file, db_type, config, output_dir):
    """
    Execute Liquibase update command for a specific XML file.
    
    Args:
        xml_file: Path to XML file to execute
        db_type: Type of database
        config: Configuration dictionary
        output_dir: Directory containing the XML file
        
    Returns:
        Tuple (success: bool, message: str)
    """
    try:
        db_url = get_database_url(db_type, config)
        
        if not db_url:
            return False, f"Unsupported database type: {db_type}"
        
        logger.info(f"Executing Liquibase for: {xml_file.name}")
        logger.info(f"Database URL: {db_url[:50]}...")
        
        # Build Liquibase command
        # Note: This assumes liquibase is installed and in PATH
        # Adjust the command based on your Liquibase installation
        command = [
            'liquibase',
            '--changeLogFile=' + str(xml_file),
            '--url=' + db_url,
            '--driver=com.mysql.cj.jdbc.Driver',  # Adjust driver based on db_type
            'update'
        ]
        
        # Execute command
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.returncode == 0:
            logger.info(f"✓ Successfully executed: {xml_file.name}")
            return True, "Execution successful"
        else:
            logger.error(f"✗ Execution failed for {xml_file.name}")
            logger.error(f"Error output: {result.stderr}")
            return False, result.stderr
    
    except subprocess.TimeoutExpired:
        logger.error(f"Liquibase execution timed out for {xml_file.name}")
        return False, "Execution timeout (300 seconds)"
    except Exception as e:
        logger.error(f"Error executing Liquibase for {xml_file.name}: {e}")
        return False, str(e)


def move_file(source_file, dest_dir):
    """
    Move file to destination directory.
    
    Args:
        source_file: Path to source file
        dest_dir: Destination directory
        
    Returns:
        True if successful, False otherwise
    """
    try:
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest_file = dest_dir / source_file.name
        source_file.rename(dest_file)
        logger.info(f"Moved {source_file.name} to {dest_dir.name}")
        return True
    except Exception as e:
        logger.error(f"Error moving file {source_file.name}: {e}")
        return False


def save_execution_history(history_path, execution_log):
    """
    Save execution history to JSON file.
    
    Args:
        history_path: Path to history file
        execution_log: List of execution records
    """
    try:
        history_path.parent.mkdir(parents=True, exist_ok=True)
        with open(history_path, 'a', encoding='utf-8') as f:
            for record in execution_log:
                f.write(json.dumps(record) + '\n')
        logger.info(f"Saved execution history: {len(execution_log)} record(s)")
    except Exception as e:
        logger.error(f"Error saving execution history: {e}")


def main():
    """
    Main function to scan, execute, and archive Liquibase XML files.
    """
    logger.info("Starting Liquibase execution...")
    
    # Define paths
    project_root = Path(__file__).resolve().parents[3]
    generated_dir = project_root / "liquibase" / "generated"
    archive_dir = project_root / "liquibase" / "archive"
    failed_dir = project_root / "liquibase" / "failed"
    history_file = project_root / "metadata" / "liquibase_execution_history.jsonl"
    
    # Load database configuration
    # Try MySQL config first (can be extended for other databases)
    # Load database configuration
    
    
    if platform.system() == "Windows":
        mysql_config_path = project_root / "config" / "mysql.conf"
    else:
        mysql_config_path = project_root / "config" / "ubuntu" / "mysql.conf"
    
    if not mysql_config_path.exists():
        logger.error(f"Config file not found: {mysql_config_path}")
        return
    
    config = load_config(mysql_config_path)
    
    if not config:
        logger.warning("No database configuration found. Using default MySQL settings.")
        config = {
            'MYSQL_HOST': 'localhost',
            'MYSQL_PORT': '3306',
            'MYSQL_DB': 'ecommerce',
            'MYSQL_USER': 'root',
            'MYSQL_PASSWORD': 'root'
        }
    
    # Scan for XML files
    if not generated_dir.exists():
        logger.warning(f"Generated directory not found: {generated_dir}")
        return
    
    xml_files = list(generated_dir.glob("*.xml"))
    logger.info(f"Found {len(xml_files)} XML file(s) to execute")
    
    if not xml_files:
        logger.info("No XML files to process")
        return
    
    # Execute each XML file
    execution_log = []
    successful_count = 0
    failed_count = 0
    
    for xml_file in xml_files:
        logger.info(f"\n--- Processing: {xml_file.name} ---")
        
        # Execute Liquibase
        success, message = execute_liquibase(xml_file, 'mysql', config, generated_dir)
        
        # Create execution record
        record = {
            "timestamp": datetime.now().isoformat(),
            "file": xml_file.name,
            "status": "success" if success else "failed",
            "message": message
        }
        execution_log.append(record)
        
        # Move file based on result
        if success:
            move_file(xml_file, archive_dir)
            successful_count += 1
        else:
            move_file(xml_file, failed_dir)
            failed_count += 1
    
    # Save execution history
    save_execution_history(history_file, execution_log)
    
    # Summary
    logger.info(f"\n{'='*60}")
    logger.info(f"Liquibase Execution Summary:")
    logger.info(f"  Total files: {len(xml_files)}")
    logger.info(f"  Successful: {successful_count}")
    logger.info(f"  Failed: {failed_count}")
    logger.info(f"  Archive dir: {archive_dir}")
    logger.info(f"  Failed dir: {failed_dir}")
    logger.info(f"  History file: {history_file}")
    logger.info(f"{'='*60}")


if __name__ == "__main__":
    main()
