from decimal import Decimal

from core import models
from core.serializers import SimpleUserSerializer
from django.core.exceptions import ValidationError
from django.db import transaction
from rest_framework import serializers
from rest_framework.fields import ReadOnlyField
from rest_framework.relations import HyperlinkedRelatedField
from typing_extensions import Required

from store.models import (
    Cart,
    CartItem,
    Collection,
    Customer,
    Order,
    OrderItem,
    Product,
    ProductImage,
    Reviews,
)

from .signals import order_created


class CollectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Collection
        fields = ["id", "title", "products_count"]

    products_count = serializers.IntegerField(read_only=True)


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ["id", "image"]

    def create(self, validated_data):
        product_id = self.context["product_id"]
        instance = ProductImage.objects.create(product_id=product_id, **validated_data)
        return instance


class ProductSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        # fields = "__all__" # bad practice
        fields = [
            "id",
            "title",
            "slug",
            "description",
            "inventory",
            "unit_price",
            "price_with_tax",
            "collection",
            "images",
        ]

    # id = serializers.IntegerField()
    # title = serializers.CharField(max_length=255)
    # price = serializers.DecimalField(
    #     max_digits=6, decimal_places=2, source="unit_price"
    # )
    # # calculated field in serializer class
    price_with_tax = serializers.SerializerMethodField(method_name="calculate_tax")

    # # serialize by primary key
    # # collection = serializers.PrimaryKeyRelatedField(queryset=Collection.objects.all())
    # # serialize by string
    # # collection = serializers.StringRelatedField()
    # # serialize by nested object
    # # collection = CollectionSerializer()
    # # serialize by hyperlink

    # collection = HyperlinkedRelatedField(
    #     queryset=Collection.objects.all(), view_name="collection-detail"
    # )

    def calculate_tax(self, product: Product):
        return product.unit_price * Decimal(1.1)

    # override the validate method of the ModelSerializer class to perform custom validation.
    # def validate(self, attrs):
    #  return super().validate(attrs)

    # we can overwrite the create method if we want to set somefields.
    def create(self, validated_data):
        product = Product(**validated_data)
        product.description = "setting up description by overriding a create method."
        product.save()
        return product

    # similary update method can also be overridden
    # def update(self, instance, validated_data):
    # in    stance.unit_price = validated_data.get("unit_price")
    # instance.save()
    # return instance


class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reviews
        fields = ["id", "date", "name", "description"]

    def create(self, validated_data):
        product_id = self.context["product_id"]
        return Reviews.objects.create(product_id=product_id, **validated_data)


class SimpleProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ["id", "title", "unit_price"]


class AddCartItemSerializer(serializers.ModelSerializer):
    product_id = serializers.IntegerField()

    class Meta:
        model = CartItem
        fields = ["id", "product_id", "quantity"]

    def validate_product_id(self, value):
        if not Product.objects.filter(pk=value).exists():
            raise serializers.ValidationError(
                "The product does not exist with a given product_id."
            )
        return value

    def save(self, **kwargs):
        cart_id = self.context["cart_id"]
        producd_id = self.validated_data["product_id"]
        quantity = self.validated_data["quantity"]
        try:
            cart_item = CartItem.objects.get(cart_id=cart_id, product_id=producd_id)
            cart_item.quantity += quantity
            cart_item.save()
            self.instance = cart_item
        except CartItem.DoesNotExist:
            self.instance = CartItem.objects.create(
                cart_id=cart_id, **self.validated_data
            )
        return self.instance


class UpdateCartItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = CartItem
        fields = ["quantity"]


class CartItemSerializer(serializers.ModelSerializer):
    product = SimpleProductSerializer()
    total_price = serializers.SerializerMethodField(method_name="get_total_price")

    def get_total_price(self, cart_item: CartItem):
        return cart_item.quantity * cart_item.product.unit_price

    class Meta:
        model = CartItem
        fields = ["id", "product", "quantity", "total_price"]


class CartSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    items = CartItemSerializer(many=True, read_only=True)
    total_price = serializers.SerializerMethodField(method_name="get_total_price")

    def get_total_price(self, cart: Cart):

        return sum(
            [item.quantity * item.product.unit_price for item in cart.items.all()]
        )

    class Meta:
        model = Cart
        fields = ["id", "items", "total_price"]


class OrderItemSerializer(serializers.ModelSerializer):
    product = SimpleProductSerializer()
    total_price = serializers.SerializerMethodField(method_name="get_total_price")

    class Meta:
        model = OrderItem
        fields = ["id", "quantity", "product", "unit_price", "total_price"]

    def get_total_price(self, order_item: OrderItem):
        return order_item.unit_price * order_item.quantity


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ["id", "first_name", "last_name"]


class CustomerProfileSerializer(CustomerSerializer):
    user = SimpleUserSerializer()

    class Meta(CustomerSerializer.Meta):
        fields = ["id", "user", "phone", "membership", "birth_date"]


class OrderSerializer(serializers.ModelSerializer):
    customer = CustomerSerializer()
    items = OrderItemSerializer(many=True)
    total_order_price = serializers.SerializerMethodField(
        method_name="get_total_order_price"
    )

    class Meta:
        model = Order
        fields = [
            "id",
            "customer",
            "placed_at",
            "payment_status",
            "items",
            "total_order_price",
        ]

    def get_total_order_price(self, order: Order):
        return sum([item.quantity * item.unit_price for item in order.items.all()])


class CreateOrderSerializer(serializers.Serializer):
    cart_id = serializers.UUIDField()

    def validate_cart_id(self, cart_id):
        if not Cart.objects.filter(pk=cart_id).exists():
            raise serializers.ValidationError(
                "The card does not exist with the given id."
            )
        if CartItem.objects.filter(cart_id=cart_id).count() == 0:
            raise serializers.ValidationError("The cart is empty.")

        return cart_id

    def save(self, **kwargs):
        cart_id = self.validated_data["cart_id"]
        user_id = self.context["user_id"]
        with transaction.atomic():
            customer = Customer.objects.get(pk=user_id)
            order = Order.objects.create(customer=customer)
            cart_items = CartItem.objects.select_related("product").filter(
                cart_id=cart_id
            )
            order_items = [
                OrderItem(
                    order=order,
                    product=item.product,
                    quantity=item.quantity,
                    unit_price=item.product.unit_price,
                )
                for item in cart_items
            ]
            OrderItem.objects.bulk_create(order_items)
            Cart.objects.filter(pk=cart_id).delete()
            order_created.send_robust(self.__class__, order=order)
            return order


class UpdateOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ["payment_status"]
