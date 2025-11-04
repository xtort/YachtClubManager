from django.contrib import admin
from .models import Event, EventCategory


@admin.register(EventCategory)
class EventCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'color', 'created_at']
    search_fields = ['name', 'description']
    list_filter = ['created_at']


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'start_datetime', 'end_datetime', 'created_at']
    list_filter = ['category', 'start_datetime', 'created_at']
    search_fields = ['title', 'short_description']
    date_hierarchy = 'start_datetime'
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'short_description', 'category')
        }),
        ('Date & Time', {
            'fields': ('start_datetime', 'end_datetime')
        }),
        ('Description', {
            'fields': ('formatted_description',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
