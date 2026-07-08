import uuid

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.text import slugify


class CategoryModel(models.Model):
    id = models.UUIDField(default=uuid.uuid4,
                          primary_key=True, editable=False)
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=140, unique=True, blank=True)
    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="children",
    )
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Category"
        verbose_name_plural = "Categories"

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name, allow_unicode=True)
            slug = base_slug
            counter = 1

            while CategoryModel.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

            self.slug = slug

        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class BrandModel(models.Model):
    id = models.UUIDField(default=uuid.uuid4,
                          primary_key=True, editable=False)
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=140, unique=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Brand"
        verbose_name_plural = "Brands"

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name, allow_unicode=True)
            slug = base_slug
            counter = 1

            while BrandModel.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

            self.slug = slug

        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class ProductModel(models.Model):
    class StatusChoices(models.TextChoices):
        DRAFT = "draft", "Draft"
        ACTIVE = "active", "Active"
        ARCHIVED = "archived", "Archived"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    category = models.ForeignKey(
        CategoryModel,
        on_delete=models.PROTECT,
        related_name="products",
    )
    brand = models.ForeignKey(
        BrandModel,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="products",
    )

    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=280, unique=True, blank=True)

    short_description = models.CharField(max_length=500, blank=True)
    description = models.TextField(blank=True)

    status = models.CharField(
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.DRAFT,
    )
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)

    meta_title = models.CharField(max_length=255, blank=True)
    meta_description = models.CharField(max_length=320, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Product"
        verbose_name_plural = "Products"
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["is_active"]),
            models.Index(fields=["is_featured"]),
            models.Index(fields=["category", "status"]),
            models.Index(fields=["slug"]),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name, allow_unicode=True)
            slug = base_slug
            counter = 1

            while ProductModel.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

            self.slug = slug

        super().save(*args, **kwargs)

    @property
    def default_variant(self):
        return self.variants.filter(is_active=True).order_by("sort_order", "id").first()

    def __str__(self):
        return self.name


class ProductImageModel(models.Model):
    id = models.UUIDField(default=uuid.uuid4,
                          primary_key=True, editable=False)
    product = models.ForeignKey(
        ProductModel,
        on_delete=models.CASCADE,
        related_name="images",
    )
    image = models.ImageField(upload_to="products/images/")
    alt_text = models.CharField(max_length=255, blank=True)
    is_primary = models.BooleanField(default=False)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "id"]
        verbose_name = "Product Image"
        verbose_name_plural = "Product Images"
        indexes = [
            models.Index(fields=["product", "is_primary"]),
        ]

    def __str__(self):
        return f"Image - {self.product.name}"


class ProductAttributeModel(models.Model):
    """
    Example:
    - Color
    - Storage
    - Size
    - RAM
    """
    id = models.UUIDField(default=uuid.uuid4,
                          primary_key=True, editable=False)
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Product Attribute"
        verbose_name_plural = "Product Attributes"

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name, allow_unicode=True)
            slug = base_slug
            counter = 1

            while ProductAttributeModel.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

            self.slug = slug

        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class ProductAttributeValueModel(models.Model):
    """
    Example:
    - Color: Black
    - Color: White
    - Storage: 128GB
    - Storage: 256GB
    """
    id = models.UUIDField(default=uuid.uuid4,
                          primary_key=True, editable=False)
    attribute = models.ForeignKey(
        ProductAttributeModel,
        on_delete=models.CASCADE,
        related_name="values",
    )
    value = models.CharField(max_length=100)
    slug = models.SlugField(max_length=140, blank=True)

    class Meta:
        ordering = ["attribute__name", "value"]
        verbose_name = "Product Attribute Value"
        verbose_name_plural = "Product Attribute Values"
        constraints = [
            models.UniqueConstraint(
                fields=["attribute", "value"],
                name="unique_product_attribute_value",
            ),
            models.UniqueConstraint(
                fields=["attribute", "slug"],
                name="unique_product_attribute_slug",
            ),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.value, allow_unicode=True)
            slug = base_slug
            counter = 1

            while ProductAttributeValueModel.objects.filter(
                attribute=self.attribute,
                slug=slug,
            ).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

            self.slug = slug

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.attribute.name}: {self.value}"


class ProductSpecificationModel(models.Model):
    """
    Display-only product details.

    Example for a phone:
    - Screen: 6.1 inch
    - Battery: 3561 mAh
    - Operating System: iOS

    These are not variant options.
    """
    id = models.UUIDField(default=uuid.uuid4,
                          primary_key=True, editable=False)
    product = models.ForeignKey(
        ProductModel,
        on_delete=models.CASCADE,
        related_name="specifications",
    )
    key = models.CharField(max_length=120)
    value = models.CharField(max_length=255)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "id"]
        verbose_name = "Product Specification"
        verbose_name_plural = "Product Specifications"

    def __str__(self):
        return f"{self.product.name} - {self.key}"


class ProductVariantModel(models.Model):
    """
    This is the actual sellable unit.

    Example:
    Product: iPhone 16

    Variants:
    - Black / 128GB
    - Black / 256GB
    - White / 128GB
    """
    id = models.UUIDField(default=uuid.uuid4,
                          primary_key=True, editable=False)
    product = models.ForeignKey(
        ProductModel,
        on_delete=models.CASCADE,
        related_name="variants",
    )

    sku = models.CharField(max_length=80, unique=True)
    display_name = models.CharField(max_length=255, blank=True)

    price_rial = models.BigIntegerField()
    compare_at_price_rial = models.BigIntegerField(null=True, blank=True)
    cost_price_rial = models.BigIntegerField(null=True, blank=True)

    stock = models.PositiveIntegerField(default=0)
    reserved_stock = models.PositiveIntegerField(default=0)

    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)

    attributes_snapshot = models.JSONField(default=dict, blank=True)

    weight_grams = models.PositiveIntegerField(null=True, blank=True)

    attribute_values = models.ManyToManyField(
        ProductAttributeValueModel,
        through="ProductVariantAttributeValueModel",
        related_name="variants",
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["sort_order", "id"]
        verbose_name = "Product Variant"
        verbose_name_plural = "Product Variants"
        indexes = [
            models.Index(fields=["product", "is_active"]),
            models.Index(fields=["sku"]),
            models.Index(fields=["price_rial"]),
        ]

    def clean(self):
        if self.price_rial < 0:
            raise ValidationError({
                "price_rial": "Price cannot be negative."
            })

        if self.compare_at_price_rial is not None and self.compare_at_price_rial < self.price_rial:
            raise ValidationError({
                "compare_at_price_rial": "Compare-at price must be greater than or equal to price."
            })

        if self.cost_price_rial is not None and self.cost_price_rial < 0:
            raise ValidationError({
                "cost_price_rial": "Cost price cannot be negative."
            })

        if self.reserved_stock > self.stock:
            raise ValidationError({
                "reserved_stock": "Reserved stock cannot be greater than total stock."
            })

    @property
    def available_stock(self):
        return max(self.stock - self.reserved_stock, 0)

    @property
    def is_in_stock(self):
        return self.available_stock > 0

    @property
    def price_toman(self):
        return self.price_rial // 10

    @property
    def compare_at_price_toman(self):
        if self.compare_at_price_rial is None:
            return None

        return self.compare_at_price_rial // 10

    @property
    def cost_price_toman(self):
        if self.cost_price_rial is None:
            return None

        return self.cost_price_rial // 10

    @property
    def has_discount(self):
        return (
            self.compare_at_price_rial is not None
            and self.compare_at_price_rial > self.price_rial
        )

    @property
    def discount_amount_rial(self):
        if not self.has_discount:
            return 0

        return self.compare_at_price_rial - self.price_rial

    @property
    def discount_percent(self):
        if not self.has_discount:
            return 0

        return round(
            ((self.compare_at_price_rial - self.price_rial) /
             self.compare_at_price_rial) * 100
        )

    def update_snapshot(self):
        pairs = self.variant_attribute_values.select_related(
            "attribute_value__attribute"
        ).all()

        snapshot = {}
        display_parts = []

        for pair in pairs:
            attribute = pair.attribute_value.attribute
            value = pair.attribute_value

            key = attribute.slug or slugify(attribute.name, allow_unicode=True)

            snapshot[key] = value.value
            display_parts.append(value.value)

        self.attributes_snapshot = snapshot

        if display_parts:
            self.display_name = " / ".join(display_parts)
        else:
            self.display_name = self.product.name

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        if self.display_name:
            return f"{self.product.name} - {self.display_name}"

        return f"{self.product.name} - {self.sku}"


class ProductVariantAttributeValueModel(models.Model):
    id = models.UUIDField(default=uuid.uuid4,
                          primary_key=True, editable=False)
    variant = models.ForeignKey(
        ProductVariantModel,
        on_delete=models.CASCADE,
        related_name="variant_attribute_values",
    )
    attribute_value = models.ForeignKey(
        ProductAttributeValueModel,
        on_delete=models.PROTECT,
        related_name="variant_attribute_values",
    )

    class Meta:
        verbose_name = "Product Variant Attribute Value"
        verbose_name_plural = "Product Variant Attribute Values"
        constraints = [
            models.UniqueConstraint(
                fields=["variant", "attribute_value"],
                name="unique_variant_attribute_value_link",
            ),
        ]

    def clean(self):
        if not self.variant_id or not self.attribute_value_id:
            return

        exists_same_attribute = ProductVariantAttributeValueModel.objects.filter(
            variant=self.variant,
            attribute_value__attribute=self.attribute_value.attribute,
        ).exclude(pk=self.pk).exists()

        if exists_same_attribute:
            raise ValidationError(
                "A variant cannot have multiple values for the same attribute."
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

        self.variant.update_snapshot()
        self.variant.save(update_fields=[
            "attributes_snapshot",
            "display_name",
            "updated_at",
        ])

    def delete(self, *args, **kwargs):
        variant = self.variant

        super().delete(*args, **kwargs)

        variant.update_snapshot()
        variant.save(update_fields=[
            "attributes_snapshot",
            "display_name",
            "updated_at",
        ])

    def __str__(self):
        return f"{self.variant.sku} - {self.attribute_value}"
