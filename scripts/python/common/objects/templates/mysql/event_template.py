EVENT_TEMPLATE = """
CREATE EVENT {event_name}
ON SCHEDULE EVERY 1 DAY
DO
    DELETE FROM {table_name}
    WHERE 1=0
""".strip()