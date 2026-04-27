rom django import forms
from django.contrib import messages
from django.db import models
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import NoReverseMatch, reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils import timezone
from django.views import View
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from .models import Task


def _task_list_url() -> str:
    try:
        return reverse("task_list")
    except NoReverseMatch:
        return "/"


def _redirect_back(request: HttpRequest) -> HttpResponse:
    next_url = (
        request.POST.get("next")
        or request.GET.get("next")
        or request.META.get("HTTP_REFERER")
    )

    if next_url and url_has_allowed_host_and_scheme(
        url=next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return redirect(next_url)

    return redirect(_task_list_url())


class TaskForm(forms.ModelForm):
    due_date = forms.DateTimeField(
        required=False,
        input_formats=["%Y-%m-%dT%H:%M"],
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"}),
    )

    class Meta:
        model = Task
        fields = ["title", "description", "priority", "due_date", "completed"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        due_date = self.instance.due_date
        if due_date:
            if timezone.is_aware(due_date):
                due_date = timezone.localtime(due_date)
            self.initial["due_date"] = due_date.strftime("%Y-%m-%dT%H:%M")


class TaskListView(ListView):
    model = Task
    context_object_name = "tasks"
    template_name = "task_list.html"

    def get_queryset(self):
        queryset = Task.objects.all()
        status = self.request.GET.get("status", "all")
        query = self.request.GET.get("q", "").strip()

        if status == "completed":
            queryset = queryset.filter(completed=True)
        elif status == "pending":
            queryset = queryset.filter(completed=False)
        elif status == "overdue":
            queryset = queryset.filter(completed=False, due_date__lt=timezone.now())

        if query:
            queryset = queryset.filter(models.Q(title__icontains=query) | models.Q(description__icontains=query))

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["current_status"] = self.request.GET.get("status", "all")
        context["query"] = self.request.GET.get("q", "").strip()
        context["total_tasks"] = Task.objects.count()
        context["completed_tasks"] = Task.objects.filter(completed=True).count()
        context["pending_tasks"] = Task.objects.filter(completed=False).count()
        return context


class TaskCreateView(CreateView):
    model = Task
    form_class = TaskForm
    template_name = "task_form.html"

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Task created successfully.")
        return response

    def get_success_url(self) -> str:
        return _task_list_url()


class TaskUpdateView(UpdateView):
    model = Task
    form_class = TaskForm
    template_name = "task_form.html"

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Task updated successfully.")
        return response

    def get_success_url(self) -> str:
        return _task_list_url()


class TaskDeleteView(DeleteView):
    model = Task
    template_name = "task_confirm_delete.html"

    def form_valid(self, form):
        title = self.object.title
        response = super().form_valid(form)
        messages.success(self.request, f'Task "{title}" deleted successfully.')
        return response

    def get_success_url(self) -> str:
        return _task_list_url()


class TaskToggleStatusView(View):
    http_method_names = ["post"]

    def post(self, request: HttpRequest, pk: int) -> HttpResponse:
        task = get_object_or_404(Task, pk=pk)

        if task.completed:
            task.reopen()
            messages.success(request, f'Task "{task.title}" reopened.')
        else:
            task.mark_done()
            messages.success(request, f'Task "{task.title}" marked as completed.')

        return _redirect_back(request)