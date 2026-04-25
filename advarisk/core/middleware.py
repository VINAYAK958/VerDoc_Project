from django.utils import timezone


class UpdateLastActiveMiddleware:
    """
    Stamps CustomUser.last_active on every authenticated request.
    Throttled to at most one DB write per 60 seconds per user to avoid
    hammering the database on every page load.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if request.user.is_authenticated:
            now = timezone.now()
            last = request.user.last_active
            # Only write to DB if more than 60 seconds have elapsed
            if last is None or (now - last).total_seconds() > 60:
                request.user.__class__.objects.filter(pk=request.user.pk).update(
                    last_active=now
                )
        return response
