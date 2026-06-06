def send_notification(category: str, priority: str, assigned_team: str) -> None:
    print("\n===================================")
    print("NEW SUPPORT TICKET")
    print("===================================\n")
    print(f"Category:      {category}")
    print(f"Priority:      {priority}")
    print(f"Assigned Team: {assigned_team}")
    print("\n===================================\n")
