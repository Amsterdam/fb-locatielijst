from django.urls import path
from help_docs.views import DocumentationListView, DocumentationDetailView

urlpatterns = [
    path('', view=DocumentationListView.as_view(), name='documentation-list'),
    path('<int:pk>', view=DocumentationDetailView.as_view(), name='documentation-detail'),
]