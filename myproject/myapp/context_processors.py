from django.db.models import Sum
from .models import Cart


def cart_count(request):
    cart = None
    if request.user.is_authenticated:
        cart = Cart.objects.filter(user=request.user).first()
    else:
        cart_id = request.session.get("cart_id")
        if cart_id:
            cart = Cart.objects.filter(id=cart_id, user=None).first()

    count = 0
    if cart:
        count = cart.items.aggregate(jami=Sum("quantity"))["jami"] or 0

    return {"cart_count": count}