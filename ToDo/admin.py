from django.contrib import admin

from .models import Task


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "priority",
        "completed",
        "due_date",
        "created_at",
        "is_overdue_display",
    )
    list_editable = ("priority", "completed")
    list_filter = ("completed", "priority", "created_at", "due_date")
    search_fields = ("title", "description")
    ordering = ("completed", "due_date", "-created_at")
    readonly_fields = ("created_at", "updated_at", "is_overdue")
    date_hierarchy = "created_at"
    actions = ("mark_completed", "mark_pending")
    fieldsets = (
        (
            None,
            {
                "fields": ("title", "description", "priority", "completed", "due_date"),
            },
        ),
        (
            "Metadata",
            {
                "fields": ("created_at", "updated_at", "is_overdue"),
                "classes": ("collapse",),
            },
        ),
    )

    @admin.display(boolean=True, description="Overdue")
    def is_overdue_display(self, obj: Task) -> bool:
        return obj.is_overdue

    @admin.action(description="Mark selected tasks as completed")
    def mark_completed(self, request, queryset):
        updated = queryset.update(completed=True)
        self.message_user(request, f"{updated} task(s) marked as completed.")

    @admin.action(description="Mark selected tasks as pending")
    def mark_pending(self, request, queryset):
        updated = queryset.update(completed=False)
        self.message_user(request, f"{updated} task(s) marked as pending.")