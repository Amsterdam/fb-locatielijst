from django.db.models import Q


def filter_on_archive(archive: str) -> Q:
    """Filter helper for the `Locatie.archief` flag.

    Mirrors the `locations` app behavior:
    - default: only active locations
    - staff can explicitly request archived or all
    """

    match archive:
        case "active" | "":
            return Q(archief=False)
        case "archived":
            return Q(archief=True)
        case "all":
            return Q()
        case _:
            return Q(archief=False)
