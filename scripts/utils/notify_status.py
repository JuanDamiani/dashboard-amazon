"""
Notificacion de estado del pipeline.

Este archivo cubre RF13 en modo local/demo. En lugar de enviar correo real,
registra mensajes en los logs de Airflow y delega el detalle de fallos al modulo
de auditoria. En una version productiva podria conectarse a SMTP o a alertas.
"""

from scripts.utils.audit import log_pipeline_failure


def notify_success(**context):
    """Notification hook for a successful pipeline run."""
    print("Pipeline ejecutado correctamente")


def notify_failure(context):
    """Notification hook for a failed pipeline run."""
    log_pipeline_failure(context)
    print("Pipeline fallo. Revisar logs de Airflow.")
