from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import EmailMessage, mail_admins, send_mail
from django.db.models.aggregates import Avg, Count, Max, Min, Sum
from django.http import HttpResponse
from django.http.response import BadHeaderError
from django.shortcuts import render
from store.models import Collection, Customer, Order, OrderItem, Product
from templated_mail.mail import BaseEmailMessage

# Create your views here.

# request -> response
# action


def send_email(request):
    try:
        temp_email = BaseEmailMessage(
            template_name="emails/hello.html",
            context={"name": "Zahid Hussain"},
        )
        temp_email.send(["zahid@tf.com"])
        mail = EmailMessage("subject", "message", "hello@zahid.com", ["info@zahid.com"])
        mail.attach_file("store/static/store/styles.css")
        mail.send()

        send_mail(
            subject="Hello World",
            message="message",
            from_email="zahid@info.com",
            recipient_list=["zahid.ce@gmail.com"],
        )
        mail_admins(subject="Issue", message="message", html_message="message")
    except BadHeaderError:
        return HttpResponse("Error", status=400)
    return HttpResponse("Email sent", status=200)


def say_hello(request):

    exists = Product.objects.filter(pk=1).exists()
    product = Product.objects.filter(pk=1).first()

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
