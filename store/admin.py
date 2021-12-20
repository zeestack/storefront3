from django.contrib import admin, messages
from django.contrib.admin.filters import SimpleListFilter
from django.contrib.admin.views.main import ChangeList
from django.db import models
from django.db.models.aggregates import Count
from django.db.models.expressions import OrderBy
from django.db.models.query import QuerySet
from django.http.request import HttpRequest
from django.urls import reverse
from django.urls.base import clear_url_caches
from django.utils.html import format_html, urlencode
from typing_extensions import OrderedDict

from . import models

# Register your models here.


class UnorderedChangeList(ChangeList):
    def get_ordering_field(self, field_name):
        return None


@admin.register(models.Collection)
class CollectionAdmin(admin.ModelAdmin):

    list_display = ["title", "product_count"]
    search_fields = ["title"]
    autocomplete_fields = ["featured_product"]

    @admin.display(ordering="product_count")
    def product_count(self, collection):
        url = (
            reverse("admin:store_product_changelist")
            + "?"
            + urlencode({"collection__id": str(collection.id)})
        )
        return format_html("<a href={}>{} Products</>", url, collection.product_count)

    def get_queryset(self, request):
        print(request)
        return (
            super()
            .get_queryset(request)
            .annotate(product_count=Count("products"))
            .order_by("-product_count")
        )

    def get_changelist(self, request, **kwargs):
        return UnorderedChangeList


class InventoryFilter(admin.SimpleListFilter):
    title = "inventory"
    parameter_name = "inventory"

    def lookups(self, request, model_admin):
        return [("<10", "Low")]

    def queryset(self, request, queryset: QuerySet):
        if self.value() == "<10":
            return queryset.filter(inventory__lt=10)


@admin.register(models.Product)
class ProdutAdmin(admin.ModelAdmin):
    #    inlines = [TagInline]
    actions = ["clear_inventory"]
    list_display = [
        "title",
        "unit_price",
        "inventory",
        "inventory_status",
        "collection_title",
    ]
    list_editable = ["unit_price"]
    list_filter = ["collection", "last_update", InventoryFilter]
    list_per_page = 10
    list_select_related = ["collection"]
    search_fields = ["title"]
    # manipulating forms

    # fields = ["title", "slug"]
    # exclude = ["promotions"]
    # readonly_fields = ["title"]
    autocomplete_fields = ["collection"]

    prepopulated_fields = {"slug": ["title"]}

    def collection_title(self, product):
        return product.collection.title

    @admin.display(ordering="inventory")
    def inventory_status(self, product):
        if product.inventory < 10:
            return "Low"
        return "OK"

    @admin.action(description="Clear Inventory")
    def clear_inventory(self, request, queryset):
        updated_count = queryset.update(inventory=0)
        self.message_user(
            request, f"{updated_count} successfully updated.", messages.ERROR
        )


@admin.register(models.Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ["first_name", "last_name", "membership", "order_count"]
    list_editable = ["membership"]
    list_per_page = 10
    list_select_related = ["user"]
    ordering = ["user__first_name", "user__last_name"]
    search_fields = ["first_name__istartswith", "last_name__istartswith"]

    @admin.display(ordering="order_count")
    def order_count(self, customer):
        url = (
            reverse("admin:store_order_changelist")
            + "?"
            + urlencode(
                {
                    "customer__id": str(customer.id),
                }
            )
        )
        return format_html("<a href={}>{} Orders</>", url, customer.order_count)

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(order_count=Count("order"))


# admin.site.register(models.Product, ProdutAdmin)


class OrderItemInline(admin.TabularInline):
    autocomplete_fields = ["product"]
    model = models.OrderItem
    extra = 0
    # min_num = 1
    # max_num = 10


@admin.register(models.Order)
class OrderAdmin(admin.ModelAdmin):
    autocomplete_fields = ["customer"]
    inlines = [OrderItemInline]
    list_display = ["id", "placed_at", "customer", "payment_status"]
