from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from team_finder.utils import paginate_queryset
from users.constants import PAGINATION_LIMIT

from .forms import ProjectForm
from .models import Project


def project_list(request):
    projects = Project.objects.select_related("owner").prefetch_related("participants")
    page_number = request.GET.get("page", 1)
    page_obj = paginate_queryset(projects, page_number, PAGINATION_LIMIT)

    return render(request, "projects/project_list.html", {"page_obj": page_obj})


def index(request):
    return redirect("projects:project_list")


@login_required
def favorite_projects(request):
    projects = (
        Project.objects.filter(favorites=request.user)
        .select_related("owner")
        .prefetch_related("participants")
    )
    page_number = request.GET.get("page", 1)
    page_obj = paginate_queryset(projects, page_number, PAGINATION_LIMIT)

    return render(request, "projects/favorite_projects.html", {"page_obj": page_obj})


def project_detail(request, pk):
    project = get_object_or_404(
        Project.objects.select_related("owner").prefetch_related("participants"),
        pk=pk,
    )
    return render(request, "projects/project-details.html", {"project": project})


@login_required
def project_create(request):
    form = (
        ProjectForm(request.POST or None) if request.method == "POST" else ProjectForm()
    )
    if request.method != "POST" or not form.is_valid():
        return render(
            request,
            "projects/create-project.html",
            {"form": form, "is_edit": False},
        )

    project = form.save(commit=False)
    project.owner = request.user
    project.save()
    project.participants.add(request.user)
    return redirect("projects:project_detail", pk=project.pk)


@login_required
def project_edit(request, pk):
    project = get_object_or_404(Project, pk=pk)
    if project.owner != request.user and not request.user.is_staff:
        return redirect("projects:project_detail", pk=pk)

    form = (
        ProjectForm(request.POST or None, instance=project)
        if request.method == "POST"
        else ProjectForm(instance=project)
    )
    if request.method != "POST" or not form.is_valid():
        return render(
            request,
            "projects/create-project.html",
            {"form": form, "is_edit": True},
        )

    form.save()
    return redirect("projects:project_detail", pk=pk)


@login_required
def project_delete(request, pk):
    project = get_object_or_404(Project, pk=pk)
    if not request.user.is_staff:
        return redirect("projects:project_detail", pk=pk)

    if request.method == "POST":
        project.delete()
        return redirect("projects:project_list")

    return render(request, "projects/project_confirm_delete.html", {"project": project})


@login_required
def project_toggle_participate(request, pk):
    project = get_object_or_404(Project, pk=pk)
    if request.user in project.participants.all():
        project.participants.remove(request.user)
        messages.info(request, "You left the project")
        return JsonResponse({"status": "ok", "participant": False})

    project.participants.add(request.user)
    messages.success(request, "You joined the project")
    return JsonResponse({"status": "ok", "participant": True})


@login_required
def project_favorite(request, pk):
    project = get_object_or_404(Project, pk=pk)
    if request.user in project.favorites.all():
        project.favorites.remove(request.user)
    else:
        project.favorites.add(request.user)
    return redirect("projects:project_detail", pk=pk)


@login_required
def project_close(request, pk):
    project = get_object_or_404(Project, pk=pk)
    if project.owner != request.user and not request.user.is_staff:
        return redirect("projects:project_detail", pk=pk)

    project.status = Project.Status.CLOSED
    project.save()
    return JsonResponse({"status": "ok", "project_status": Project.Status.CLOSED})
