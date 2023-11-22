from decimal import Decimal


def get_book_shipping_cost(book_quantity: int = 1) -> Decimal:
    """Calculate shipping costs for books in a cart/order.

    The shipping rules are flat rate for each book, with discounts
    offered for ordering more books.

    The product set can contain other product types, so this function
    should only consider the quantity of books.
    """

    # Apply shipping rules based on total number of books
    # one book is five dollars
    # two to four books are four dollars each
    # five to ten books are three dollars each
    # eleven to fifteen books are two dollars each
    # sixteen or more books have free shipping
    if book_quantity >= 16:
        shipping_rate = 0
    elif book_quantity in range(11, 16):
        shipping_rate = 2
    elif book_quantity in range(5, 11):
        shipping_rate = 3
    elif book_quantity in range(2, 5):
        shipping_rate = 4
    else:
        shipping_rate = 5

    shipping_cost = book_quantity * shipping_rate

    return Decimal(shipping_cost).quantize(Decimal("0.00"))
