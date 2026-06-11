from django.urls import path
from . import views

app_name = "users"

urlpatterns = [
    path("register/", views.register, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("<int:pk>/", views.profile, name="profile"),
    path("profile/edit/", views.edit_profile, name="edit_profile"),
    path("password/change/", views.change_password, name="change_password"),
    path(
        "password/admin-change/<int:pk>/",
        views.admin_change_password,
        name="admin_change_password",
    ),
    path("block/<int:pk>/", views.admin_block_user, name="admin_block_user"),
    path("delete/<int:pk>/", views.admin_delete_user, name="admin_delete_user"),
    path("list/", views.user_list, name="user_list"),
    path("<int:user_id>/skills/add/", views.add_skill, name="add_skill"),
    path(
        "<int:user_id>/skills/<int:skill_id>/remove/",
        views.remove_skill,
        name="remove_skill",
    ),
    path("skills/", views.get_skills_suggestions, name="get_skills_suggestions"),
]
