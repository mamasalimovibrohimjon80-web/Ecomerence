from django.contrib import admin

# Register your models here.
from.models import Member,Product,Catgeory, ProductImage ,Review

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 3


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("nomi", "price", "quantity", "is_active")
    list_filter = ("is_active",)
    search_fields = ("nomi", "description")
    inlines = [ProductImageInline]

admin.site.register(Member)
admin.site.register(Catgeory)
admin.site.register(Review)