from rest_framework import views, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.carts.services import (
    add_item_to_cart,
    update_cart_item,
    remove_cart_item,
    clear_cart,
    apply_promo_code,
    get_or_create_active_cart
)
from apps.carts.api.serializers import (
    CartSerializer,
    AddToCartSerializer,
    UpdateCartItemSerializer,
    ApplyPromoSerializer,
)
from apps.carts.exceptions import CartItemNotFound, CartBranchConflict, InvalidPromoCode


class CartView(views.APIView):
    """GET /api/v1/cart/ — joriy faol savat"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        cart = get_or_create_active_cart(request.user)
        return Response(CartSerializer(cart).data)


class CartItemAddView(views.APIView):
    """POST /api/v1/cart/items/ — savatga mahsulot qo'shish"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = AddToCartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        d = serializer.validated_data
        try:
            item = add_item_to_cart(
                user=request.user,
                product_id=d["product_id"],
                variant_id=d.get("variant_id"),
                qty=d["qty"],
                modifier_option_ids=d.get("modifier_option_ids", []),
                instructions=d.get("instructions", ""),
            )
        except CartBranchConflict as e:
            return Response({"detail": str(e)}, status=status.HTTP_409_CONFLICT)
        return Response({"id": str(item.id)}, status=status.HTTP_201_CREATED)


class CartItemUpdateView(views.APIView):
    """PATCH /api/v1/cart/items/{id}/ — miqdorni o'zgartirish"""
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        serializer = UpdateCartItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            update_cart_item(user=request.user, item_id=pk, qty=serializer.validated_data["qty"])
        except CartItemNotFound as e:
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_204_NO_CONTENT)


class CartItemDeleteView(views.APIView):
    """DELETE /api/v1/cart/items/{id}/"""
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        try:
            remove_cart_item(user=request.user, item_id=pk)
        except CartItemNotFound as e:
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_204_NO_CONTENT)


class CartApplyPromoView(views.APIView):
    """POST /api/v1/cart/apply-promo/"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ApplyPromoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            cart = apply_promo_code(user=request.user, code=serializer.validated_data["code"])
        except InvalidPromoCode as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(CartSerializer(cart).data)


class CartClearView(views.APIView):
    """POST /api/v1/cart/clear/"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        cart = clear_cart(user=request.user)
        return Response(CartSerializer(cart).data)
