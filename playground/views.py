from django.shortcuts import render
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse
from store.models import Collection, Customer, Order, OrderItem, Product
from django.db.models.aggregates import Count, Max, Min, Avg, Sum

# Create your views here.

# request -> response
# action


def say_hello(request):
    # return HttpResponse("Hello World")
    # query_set = Product.objects.all() # query_set is based on lazy evaluation
    # for product in query_set:
    #  print(product)
    # try:
    #   product = Product.objects.get(pk=1)
    # except ObjectDoesNotExist:
    #   pass
    exists = Product.objects.filter(pk=1).exists()
    product = Product.objects.filter(pk=1).first()
    print(product)

    # queryset = Product.objects.filter(unit_price__range=(20, 30))
    # queryset = Product.objects.filter(title__startswith="C")
    queryset = Product.objects.filter(last_update__year=2021)

    queryset_customer = Customer.objects.filter(email__endswith=".com")
    queryset_collection = Collection.objects.filter(featured_product__isnull=True)
    queryset_products = Product.objects.filter(inventory__lt=10)
    queryset_orders = Order.objects.filter(customer__id=1)
    queryset_order_items = OrderItem.objects.filter(product__collection__id=3)

    return render(
        request,
        "hello.html",
        {
            "name": "Zahid Hussain",
            "age": "37",
            "products": list(queryset),
            "customers": list(queryset_customer),
            "collections": list(queryset_collection),
            "orders": list(queryset_orders),
            "products_inventory": list(queryset_products),
            "orderItems": list(queryset_order_items),
        },
    )


def aggregate_hello(request):
    # How many orders do we have?
    orders = Order.objects.aggregate(Count("id"))

    # How many units of product 1 have we sold?
    units_sold = OrderItem.objects.filter(product__id=1).aggregate(
        units_sold=Sum("quantity")
    )

    # How many orders of customer 1 has placed?
    orders_by_customer1 = Order.objects.filter(customer__id=1).aggregate(
        count=Count("id")
    )

    # What is the min, max and average price of the products in collection 3?
    price_stats = Product.objects.filter(collection__id=3).aggregate(
        min=Min("unit_price"), max=Max("unit_price"), average=Avg("unit_price")
    )

    return render(
        request,
        "aggregate.html",
        {
            "name": "Aggregate Excercise",
            "orders": orders,
            "units_sold": units_sold,
            "orders_by_customer1": orders_by_customer1,
            "price_statistics": price_stats,
        },
    )


# 18 - Working with expression wrappers - Annotation Excercise
# Customer with their last orderId
# Collectioins and count of their products
# Customers with more than 5 orders
# Customers and total amount they have spent
# Top 5 best selling products and their total sales
