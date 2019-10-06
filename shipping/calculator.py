from decimal import Decimal


def get_book_shipping_cost(book_quantity=1):
    """
    Calculate shipping costs for books in a cart/order.

    The shipping rules are flat rate for each book,
    with discounts offered for ordering more books.

    The product set can contain other product types,
    so this function should only consider the quantity of books.
    """

    # Get base shipping cost
    base_shipping_rate = 3

    base_shipping_cost = book_quantity * base_shipping_rate

    # Apply shipping rules based on total number of books
    if book_quantity >= 16:
        discount_multiplier = 0
    elif book_quantity in range(11, 16):
        discount_multiplier = 0.25
    elif book_quantity in range(5, 11):
        discount_multiplier = 0.5
    elif book_quantity in range(2, 5):
        discount_multiplier = 0.75
    else:
        discount_multiplier = 1

    # returning a dummy value for now
    # make sure to include two decimal places
    discounted_shipping_cost = base_shipping_cost * discount_multiplier

    return Decimal(discounted_shipping_cost).quantize(Decimal("0.00"))
