_ROUTING_TABLE: dict[str, str] = {
    "Billing": "Billing Team",
    "Technical": "Technical Support",
    "Account Access": "Customer Success",
    "Feature Request": "Product Team",
    "General Inquiry": "General Support",
}


def route_ticket(category: str) -> str:
    return _ROUTING_TABLE.get(category, "General Support")
