from scripts.server import daily_server, weekly_server


def daily(request):
    daily_server()
    return "daily server OK", 200


def weekly(request):
    weekly_server()
    return "weekly server OK", 200
