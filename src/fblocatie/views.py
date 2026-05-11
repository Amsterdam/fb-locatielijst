from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, render
from django.views import View
from django.views.generic import ListView

from fblocatie.forms import LocatieListForm
from fblocatie.models import Locatie
from fblocatie.utils.locatie_detail import get_locatie_detail_groups


class LocatieListView(LoginRequiredMixin, ListView):
    model = Locatie
    template_name = "fblocatie/locations/location-list.html"
    paginate_by = 50

    def get_queryset(self):
        queryset = super().get_queryset().select_related(
            "adres",
            "dvk_naam",
            "locatie_soort",
            "vastgoed",
            "vastgoed__bezit",
        )
        ordering = self.get_ordering()
        return queryset.search_filter(params=self.request.GET.dict(), user=self.request.user).order_by(ordering)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        initial_data = self.request.GET
        context["form"] = LocatieListForm(initial=initial_data)

        archive = (self.request.GET.get("archive") or "").strip()
        location_count = Locatie.objects.archive_filter(archive).count()
        context["location_count"] = location_count
        context["is_filtered_result"] = context["page_obj"].paginator.count < location_count

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


class LocatieDetailView(LoginRequiredMixin, View):
    template_name = "fblocatie/locations/location-detail.html"

    def _get_locatie(self, pandcode: int) -> Locatie:
        return get_object_or_404(
            Locatie.objects.select_related(
                "adres",
                "bezoekadres",
                "vastgoed",
                "vastgoed__bezit",
                "vastgoed__monument_gem",
                "vastgoed__monument_brkpb",
                "vastgoed__themagv",
                "vastgoed__asset_manager",
                "vastgoed__pl_gv",
                "locatie_soort",
                "dvk_naam",
                "budget_dir",
                "perceel_installateur",
                "gelieerd",
                "pas_lc",
            ).prefetch_related(
                "pand_directies",
                "voorzieningen",
                "contracten",
                "loc_manager",
                "loc_coordinator",
                "contact_dir",
                "tom",
                "tsc",
                "beveiliging",
                "veiligheid",
            ),
            pandcode=pandcode,
        )

    def get(self, request, pandcode: int, *args, **kwargs):
        locatie = self._get_locatie(pandcode)

        context = {
            "locatie": locatie,
            "detail_groups": get_locatie_detail_groups(locatie),
        }
        return render(request=request, template_name=self.template_name, context=context)

