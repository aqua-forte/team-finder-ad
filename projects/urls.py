from django.urls import path

from . import views

app_name = "projects"

urlpatterns = [
    path("", views.index, name="index"),
    path("project/list/", views.project_list, name="project_list"),
    path("projects/favorites/", views.favorite_projects, name="project_favorites"),
    path("projects/<int:pk>/", views.project_detail, name="project_detail"),
    path("projects/create-project/", views.project_create, name="project_create"),
    path("projects/<int:pk>/edit/", views.project_edit, name="project_edit"),
    path("projects/<int:pk>/delete/", views.project_delete, name="project_delete"),
    path(
        "projects/<int:pk>/toggle-participate/",
        views.project_toggle_participate,
        name="project_toggle_participate",
    ),
    path(
        "projects/<int:pk>/favorite/",
        views.project_favorite,
        name="project_favorite",
    ),
    path("projects/<int:pk>/complete/", views.project_close, name="project_close"),
]
