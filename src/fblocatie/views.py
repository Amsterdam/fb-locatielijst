from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView

from fblocatie.models import Locatie


class LocatieListView(LoginRequiredMixin, ListView):
    model = Locatie
    template_name = "fblocatie/locations/location-list.html"
    paginate_by = 50

    def get_queryset(self):
        queryset = super().get_queryset().select_related("vastgoed", "vastgoed__bezit")
        search_value = (self.request.GET.get("search") or "").strip()
        if search_value:
            queryset = queryset.filter(naam__icontains=search_value)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search"] = (self.request.GET.get("search") or "").strip()
        return context

    def get_ordering(self):
        order_by = self.request.GET.get("order_by")

        allowed_order_by = {
            "pandcode",
            "naam",
            "dvk_naam__name",
            "locatie_soort__name",
            "vastgoed__bezit__name",
        }

        if order_by not in allowed_order_by:
            order_by = "naam"

        prefix = "-" if self.request.GET.get("order") == "desc" else ""
        return f"{prefix}{order_by}"

