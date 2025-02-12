from django.db.models import Q


def filter_on_archive(archive) -> Q:
    match archive:
        case "active":
            qfilter = Q(is_archived=False)
        case "archived":
            qfilter = Q(is_archived=True)
        case "all":
            qfilter = Q()
        case _:
            qfilter = Q(is_archived=False)
    return qfilter
