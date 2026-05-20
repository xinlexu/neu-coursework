from django.urls import path
from . import views
urlpatterns = [
    path("hello/", views.hello),
    path("todos/", views.todos_collection),
    path("todos/stats/", views.todos_stats),
    path("todos/<int:item_id>/", views.todos_detail),
    path("feedback/", views.feedback),
    path("meta/", views.meta),
]
