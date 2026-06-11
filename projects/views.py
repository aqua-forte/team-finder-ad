from django import forms
from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import Project


def project_list(request):
    projects = Project.objects.all().select_related("owner").order_by("-created_at")
    # Pagination
    paginator = Paginator(projects, 12)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, "projects/project_list.html", {"page_obj": page_obj})


def index(request):
    return redirect("projects:project_list")


@login_required
def project_favorites(request):
    projects = Project.objects.filter(favorites=request.user).order_by("-created_at")
    paginator = Paginator(projects, 12)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, "projects/favorite_projects.html", {"page_obj": page_obj})


def project_detail(request, pk):
    project = get_object_or_404(Project, pk=pk)
    return render(request, "projects/project-details.html", {"project": project})


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ("name", "description", "github_url", "status")
        widgets = {
            "status": forms.Select(choices=Project.STATUS_CHOICES),
        }

    def clean_github_url(self):
        url = self.cleaned_data.get("github_url")
        if url and "github.com" not in url:
            raise forms.ValidationError("Ссылка должна вести на github.com")
        return url


@login_required
def project_create(request):
    if request.method == "POST":
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.owner = request.user
            project.save()
            project.participants.add(request.user)
            return redirect("projects:project_detail", pk=project.pk)
    else:
        form = ProjectForm()

    return render(
        request, "projects/create-project.html", {"form": form, "is_edit": False}
    )


@login_required
def project_edit(request, pk):
    project = get_object_or_404(Project, pk=pk)
    if project.owner != request.user and not request.user.is_staff:
        return redirect("projects:project_detail", pk=pk)

    if request.method == "POST":
        form = ProjectForm(request.POST, instance=project)
        if form.is_valid():
            form.save()
            return redirect("projects:project_detail", pk=pk)
    else:
        form = ProjectForm(instance=project)

    return render(
        request, "projects/create-project.html", {"form": form, "is_edit": True}
    )


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
    else:
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

    project.status = "closed"
    project.save()
    return JsonResponse({"status": "ok", "project_status": "closed"})
