from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Q, F, Avg, Sum
from django.views.decorators.http import require_POST

from .models import Member, Product, Catgeory, Review, Wishlist,CartItem,Cart
from .forms import RegisterForm, ReviewForm


# ---------------------------------------------------------------
# Asosiy sahifa
# ---------------------------------------------------------------
def index(request):
    mymembers = Member.objects.all()
    products = Product.objects.all()

    context = {
        "azolar": mymembers,
        "product": products,
    }
    return render(request, "index.html", context)


# ---------------------------------------------------------------
# Mahsulotlar ro'yxati
# ---------------------------------------------------------------
def products(request):
    products = Product.objects.all()
    categories = Catgeory.objects.all()
    category_id = request.GET.get("kategoriya")
    query = request.GET.get("q")

    if query:
        products = products.filter(
            Q(nomi__icontains=query) | Q(description__icontains=query)
        )

    if category_id:
        products = products.filter(category_id=category_id)

    context = {
        "mahsulot": products,
        "kategoriyalar": categories,
        "query": query,
    }
    return render(request, "products.html", context)


def category_products(request, category_id):
    category = get_object_or_404(Catgeory, id=category_id)
    products = Product.objects.filter(category=category)

    return render(request, "products.html", {
        "mahsulot": products,
        "category": category,
    })


# ---------------------------------------------------------------
# Login / Register / Logout
# ---------------------------------------------------------------
def login_form(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, "Muvaffaqiyatli tizimga kirdingiz!")
            return redirect("index")
        else:
            messages.error(request, "Login yoki parol xato")
            return redirect("login")

    return render(request, "login.html")


def register_view(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password"]
            User.objects.create_user(username=username, password=password)
            messages.success(request, "Muvaffaqiyatli ro'yxatdan o'tdingiz!")
            return redirect("login")
        else:
            messages.error(request, "Forma noto'g'ri to'ldirildi!")
    else:
        form = RegisterForm()

    return render(request, "register.html", {"form": form})


def logout_view(request):
    logout(request)
    messages.success(request, "Siz tizimdan chiqdingiz")
    return redirect("index")


# ---------------------------------------------------------------
# Mahsulot sahifasi (detail)
# ---------------------------------------------------------------
def product_view(request, slug):
    mahsulot = get_object_or_404(Product, slug=slug)
    reviews = mahsulot.reviews.all().order_by("-created_at")

    average_rating = reviews.aggregate(Avg("rating"))["rating__avg"]
    average_rating = round(average_rating, 1) if average_rating else 0

    # Sharh qoldirish
    if request.method == "POST":
        if not request.user.is_authenticated:
            messages.error(request, "Ro'yxatdan o'tishingiz kerak")
            return redirect("login")

        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.mahsulot = mahsulot
            review.user = request.user
            review.save()
            messages.success(request, "Sharhingiz uchun rahmat!")
            return redirect("product-view", slug=mahsulot.slug)
    else:
        form = ReviewForm()

    # Ko'rishlar sonini sessiya bo'yicha bir marta oshirish
    korilganlar = request.session.get("korilgan", [])
    if mahsulot.id not in korilganlar:
        Product.objects.filter(id=mahsulot.id).update(korishlar=F("korishlar") + 1)
        korilganlar.append(mahsulot.id)
        request.session["korilgan"] = korilganlar
        mahsulot.refresh_from_db()

    # Like
    liked = (
        request.user.is_authenticated
        and mahsulot.likes.filter(id=request.user.id).exists()
    )

    # Sevimlilar (modeldagi maydon nomi: products)
    in_wishlist = (
        request.user.is_authenticated
        and Wishlist.objects.filter(user=request.user, products=mahsulot).exists()
    )

    context = {
        "mahsulot": mahsulot,
        "liked": liked,
        "in_wishlist": in_wishlist,
        "form": form,
        "reviews": reviews,
        "average_rating": average_rating,
    }
    return render(request, "product.html", context)


# ---------------------------------------------------------------
# Like
# ---------------------------------------------------------------
@login_required
def like_view(request, slug):
    mahsulot = get_object_or_404(Product, slug=slug)

    if mahsulot.likes.filter(id=request.user.id).exists():
        mahsulot.likes.remove(request.user)
    else:
        mahsulot.likes.add(request.user)

    return redirect(request.META.get("HTTP_REFERER", "index"))


# ---------------------------------------------------------------
# Sevimlilar (Wishlist)
# ---------------------------------------------------------------
@login_required
def wishlist_list(request):
    wishlist_items = (
        Wishlist.objects
        .filter(user=request.user)
        .select_related("products")
        .order_by("-created_at")
    )
    return render(request, "wishlist.html", {"wishlist_items": wishlist_items})


@login_required
@require_POST
def toggle_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    item, created = Wishlist.objects.get_or_create(
        user=request.user,
        products=product,
    )

    if created:
        messages.success(request, "Sevimlilarga qo'shildi")
    else:
        item.delete()
        messages.info(request, "Sevimlilardan olib tashlandi")

    return redirect(request.META.get("HTTP_REFERER", "wishlist_list"))

def cart_qism(request):
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
    else:
        cart = None
        cart_id = request.session.get("cart_id")
        if cart_id:
            cart = Cart.objects.filter(id=cart_id, user=None).first()
        if not cart:
            cart = Cart.objects.create()
            request.session["cart_id"] = cart.id   # <-- cart_id emas, cart.id
    return cart


def add_to_cart(request, slug):
    mahsulot = get_object_or_404(Product, slug=slug)
    cart = cart_qism(request)

    cart_item, created = CartItem.objects.get_or_create(cart=cart, mahsulot=mahsulot)
    if not created:
        cart_item.quantity += 1
        cart_item.save()

    messages.success(request, "Savatchaga qo'shildi")
    return redirect(request.META.get("HTTP_REFERER", "index"))


def cart_detail(request):
    cart = cart_qism(request)
    cart_count = cart.items.aggregate(jami=Sum("quantity"))["jami"] or 0
    context = {
        "cart": cart,
        "cart_count": cart_count,
    }
    return render(request, "cart.html", context)


def remove_from_cart(request, item_id):
    cart = cart_qism(request)
    cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)  # faqat o'z savatidan
    cart_item.delete()
    messages.success(request, "Mahsulot savatdan olib tashlandi")
    return redirect("cart_detail")

def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id)
    cart_item.delete()
    messages.success(request, "Mahsulot savatdan olib tashlandi")
    return redirect('cart_detail')


