import logging

logger = logging.getLogger(__name__)


def send_notification(category: str, priority: str, assigned_team: str) -> None:
    logger.info(
        "NEW TICKET | Category: %-18s | Priority: %-8s | Team: %s",
        category,
        priority,
        assigned_team,
    )
