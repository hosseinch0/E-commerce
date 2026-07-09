from django.contrib import admin

from .models import PaymentModel


@admin.register(PaymentModel)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "order",
        "user",
        "amount_rial",
        "gateway",
        "status",
        "authority",
        "ref_id",
        "paid_at",
        "created_at",
    )
    list_filter = ("status", "gateway", "created_at", "paid_at")
    search_fields = (
        "id",
        "order__id",
        "user__phone_number",
        "authority",
        "ref_id",
    )
    readonly_fields = (
        "id",
        "created_at",
        "updated_at",
        "paid_at",
    )
