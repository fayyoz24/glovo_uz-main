from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from apps.carts.api.serializers import (
    CartSerializer,
    AddToCartSerializer,
    UpdateCartItemSerializer,
    ApplyPromoSerializer,
)
from apps.carts.selectors import get_active_cart
from apps.carts.services import (
    get_or_create_active_cart,
    add_item_to_cart,
    update_cart_item,
    remove_cart_item,
    clear_cart,
    apply_promo_code,
    remove_promo_code,
)
from apps.carts.exceptions import CartNotFound


class CartView(APIView):
    """GET — aktiv cartni ko'rish | DELETE — cartni tozalash"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        cart = get_active_cart(request.user)
        if not cart:
            cart = get_or_create_active_cart(request.user)
        return Response(CartSerializer(cart).data)

    def delete(self, request):
        clear_cart(request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)


class CartItemAddView(APIView):
    """POST — cartga mahsulot qo'shish"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = AddToCartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        d = serializer.validated_data
        item = add_item_to_cart(
            user=request.user,
            product_id=d["product_id"],
            qty=d["qty"],
            variant_id=d.get("variant_id"),
            modifier_option_ids=d.get("modifier_option_ids", []),
            instructions=d.get("instructions", ""),
        )
        cart = get_active_cart(request.user)
        return Response(CartSerializer(cart).data, status=status.HTTP_201_CREATED)


class CartItemDetailView(APIView):
    """PATCH — miqdor o'zgartirish | DELETE — mahsulotni o'chirish"""
    permission_classes = [IsAuthenticated]

    def patch(self, request, item_id):
        serializer = UpdateCartItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        update_cart_item(request.user, item_id, serializer.validated_data["qty"])
        cart = get_active_cart(request.user)
        return Response(CartSerializer(cart).data)

    def delete(self, request, item_id):
        remove_cart_item(request.user, item_id)
        cart = get_active_cart(request.user)
        return Response(CartSerializer(cart).data)


class CartPromoView(APIView):
    """POST — promo qo'llash | DELETE — promo o'chirish"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ApplyPromoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        cart = apply_promo_code(request.user, serializer.validated_data["code"])
        return Response(CartSerializer(cart).data)

    def delete(self, request):
        cart = remove_promo_code(request.user)
        return Response(CartSerializer(cart).data)
