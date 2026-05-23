def notify_success(**context):
    """
    Notifica que el pipeline se ejecutó correctamente.
    Cumple RF13 de notificación de estado de carga.
    """
    print("Pipeline ejecutado correctamente")


def notify_failure(**context):
    """
    Notifica que el pipeline falló.
    Cumple RF13 de notificación de estado de carga.
    """
    print("Pipeline falló. Revisar logs de Airflow.")