from django.contrib import admin
from rango.models import Category,Page
# Register your models here.

class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug':('name',)}

class PageAdmin(admin.ModelAdmin):
    list_display = ['category','title','url']

admin.site.register(Category,CategoryAdmin)
admin.site.register(Page, PageAdmin)

