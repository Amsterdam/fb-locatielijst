from django.views.generic import ListView, DetailView
from django.contrib import admin
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from help_docs.models import Documentation

# Create your views here.
class DocumentationListView(ListView):
    model = Documentation
    template_name = 'help_docs/documentation-list.html'

    def get_context_data(self, *args, **kwargs):
        context = super(DocumentationListView,
             self).get_context_data(*args, **kwargs, **admin.site.each_context(self.request))
        # add extra field
        return context
    
    @method_decorator(staff_member_required)
    def get(self, request, *args, **kwargs):
        return super(DocumentationListView, self).get(request, *args, **kwargs)


class DocumentationDetailView(DetailView):
    model = Documentation
    template_name = 'help_docs/documentation-detail.html'

    def get_context_data(self, *args, **kwargs):
        context = super(DocumentationDetailView,
             self).get_context_data(*args, **kwargs, **admin.site.each_context(self.request))
        # add extra field
        return context

    @method_decorator(staff_member_required)
    def get(self, request, *args, **kwargs):
        return super(DocumentationDetailView, self).get(request, *args, **kwargs)