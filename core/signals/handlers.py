from django.dispatch import receiver
from store.signals import order_created


@receiver(order_created)
def on_order_created(sender, **kwargs):
    print(f'{kwargs["order"]} has been successfully created')
