class InsufficientStock(Exception):
    """Validating the order would push a product's stock below zero."""


class IllegalStatusTransition(Exception):
    """The requested status is not reachable from the order's current one."""


def set_order_status(order, new_status):
    if order.status in ["pending", "cancelled"] and new_status == "validated":
        for item in order.items:
            if item.product.stock - item.quantity < 0:
                raise InsufficientStock(
                    f"Not enough stock for product {item.product.id}"
                )
        for item in order.items:
            item.product.stock -= item.quantity

    elif order.status == "validated" and new_status == "cancelled":
        for item in order.items:
            item.product.stock += item.quantity

    elif (
        order.status == "validated"
        and new_status == "shipped"
        or order.status == "pending"
        and new_status == "cancelled"
    ):
        pass

    else:
        raise IllegalStatusTransition(
            f"It's not possible to change order from status {order.status} to {new_status}"
        )

    order.status = new_status
