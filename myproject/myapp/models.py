from django.db import models
from django.utils.text import slugify
# Create your models here.
# Modellar malumotlar bazasida admin panelga
from django.contrib.auth.models import User
class Member(models.Model):
    ism = models.CharField("Ism", max_length=20)
    familya = models.CharField("Familya", max_length=25)
    yosh = models.IntegerField(null=True)
    email = models.EmailField("Email")

class Catgeory(models.Model):
    nomi = models.CharField(max_length=200)

    def __str__(self):
        return self.nomi


class Product(models.Model):
    omage = models.ImageField(upload_to="media")
    description = models.TextField()
    price = models.DecimalField(max_digits=10,decimal_places=2)
    quantity = models.IntegerField()
    is_active = models.BooleanField(default=True)
    nomi = models.CharField("Mahsulot nomi")
    korishlar = models.PositiveIntegerField(default=0)
    likes = models.ManyToManyField(User, related_name="likes_products", blank=True)
    views_count = models.PositiveBigIntegerField("Ko'rishlar soni", default=0)

    def like_soni(self):
        return self.likes.count()

    # Modelni modelga ulash
    category = models.ForeignKey(Catgeory, on_delete=models.CASCADE,blank=True,null=True)

    slug = models.SlugField(unique=True, blank=True, null=True)

    def save(self, *args, **kwarge):
        if not self.slug:
            self.slug = slugify(self.nomi)
        super().save(*args, **kwarge)
        

    def __str__(self):
        return self.nomi

class ProductImage(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="images"
    )
    image = models.ImageField(upload_to="products/")

    def __str__(self):
        return f"{self.product.nomi} - rasm"



class Review(models.Model):
    mahsulot = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="reviews")
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField(choices=[(i, f"{i} Yulduz") for i in range(1, 6)], default=5, verbose_name="Reyting")
    comment = models.TextField(verbose_name="Izoh")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Sana")

    def __str__(self):
        return f"{self.user.username} - {self.mahsulot.nomi} ({self.rating}*)"


class Wishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE,related_name='wishlist')
    products = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='wishlisted_by')
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        unique_together = ('user', 'products')


class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Savat #{self.id} - {self.user.username if self.user else 'Mehmon'}"

    @property
    def total_price(self):
        return sum(item.total_price for item in self.items.all())

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    mahsulot = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} x {self.mahsulot.nomi}"

    @property
    def total_price(self):
        return self.mahsulot.price * self.quantity

    @property
    def total_items(self):
        return sum(item.quantity for item in self.item.all())