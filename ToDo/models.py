from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class Task(models.Model):
    class Priority(models.TextChoices):
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    completed = models.BooleanField(default=False)
    priority = models.CharField(
        max_length=10,
        choices=Priority.choices,
        default=Priority.MEDIUM,
    )
    due_date = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["completed", "due_date", "-created_at"]
        verbose_name = "Task"
        verbose_name_plural = "Tasks"

    def __str__(self) -> str:
        return self.title

    @property
    def is_overdue(self) -> bool:
        return bool(self.due_date and self.due_date < timezone.now() and not self.completed)

    def clean(self) -> None:
        self.title = self.title.strip()
        self.description = self.description.strip()

        if not self.title:
            raise ValidationError({"title": "Task title cannot be empty."})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def mark_done(self, commit: bool = True) -> "Task":
        self.completed = True
        if commit:
            self.save(update_fields=["completed", "updated_at"])
        return self

    def reopen(self, commit: bool = True) -> "Task":
        self.completed = False
        if commit:
            self.save(update_fields=["completed", "updated_at"])
        return self