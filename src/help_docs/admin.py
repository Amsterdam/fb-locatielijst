from django.contrib import admin

from help_docs.models import Documentation


# Register your models here.
@admin.register(Documentation)
class DocumentationAdmin(admin.ModelAdmin):
    list_display = ("title", "description", "order")
    ordering = ["order"]

    def get_form(self, request, obj=None, **kwargs):
        form = super(DocumentationAdmin, self).get_form(request, obj, **kwargs)
        form.base_fields["description"].widget.attrs["style"] = "width: 47em;"
        return form
