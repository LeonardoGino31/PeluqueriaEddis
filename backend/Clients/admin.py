from django.contrib import admin

from .models import Cliente


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'telefono']
    search_fields = ['nombre', 'telefono']
    ordering = ['nombre']