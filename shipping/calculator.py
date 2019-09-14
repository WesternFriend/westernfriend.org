from decimal import Decimal


def get_book_shipping_cost(order=None):
    """
    Calculate shipping costs for books in a cart/order.

    The shipping rules are flat rate for each book,
    with discounts offered for ordering more books.

    The product set can contain other product types,
    so this function should only consider the quantity of books.
    """

    # Get products

    # if products not None

    # Check whether each of products is a Book
    # and count the total number of books

    # Apply shipping rules based on total number of books

    # returning a dummy value for now
    # make sure to include two decimal places
    return Decimal(10).quantize(Decimal("0.00"))
