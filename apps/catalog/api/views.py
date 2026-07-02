from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny

from apps.catalog.api.serializers import (
    ProductCategorySerializer,
    ProductListSerializer,
    ProductDetailSerializer,
    ProductUpdateSerializer,
    ProductCreateSerializer,
)
from apps.catalog.selectors import (
    get_active_categories,
    get_products_for_merchant,
    get_products_for_branch,
    get_product_by_id,
    search_products,
)
from apps.catalog.services import (
    create_product,
    update_product,
    toggle_product_availability,
)
from apps.catalog.exceptions import ProductNotFound
from apps.catalog.permissions import IsMerchantOwnerOrManager
from apps.common.pagination import StandardPagination


class CategoryListView(APIView):
    """GET /api/v1/categories/ — barcha faol kategoriyalar"""
    permission_classes = [AllowAny]

    def get(self, request):
        parent_id = request.query_params.get("parent")
        categories = get_active_categories(parent_id=parent_id)
        return Response(ProductCategorySerializer(categories, many=True).data)


class BranchProductListView(APIView):
    """GET /api/v1/merchants/<merchant_pk>/products/?branch=&category=&q="""
    permission_classes = [AllowAny]

    def get(self, request, merchant_pk):
        branch_id = request.query_params.get("branch")
        category_id = request.query_params.get("category")
        search = request.query_params.get("q", "")
        products = get_products_for_branch(
            branch_id=branch_id,
            category_id=category_id,
            search=search,
        )
        paginator = StandardPagination()
        page = paginator.paginate_queryset(products, request)
        serializer = ProductListSerializer(page, many=True, context={"request": request})
        return paginator.get_paginated_response(serializer.data)


class ProductDetailView(APIView):
    """GET /api/v1/products/<pk>/ — to'liq ma'lumot (variants, modifiers)"""
    permission_classes = [AllowAny]

    def get(self, request, pk):
        product = get_product_by_id(pk)
        if not product:
            raise ProductNotFound()
        return Response(ProductDetailSerializer(product, context={"request": request}).data)


class ProductSearchView(APIView):
    """GET /api/v1/search/?q=... — mahsulotlar bo'yicha qidiruv"""
    permission_classes = [AllowAny]

    def get(self, request):
        query = request.query_params.get("q", "").strip()
        if len(query) < 2:
            return Response({"results": []})
        merchant_id = request.query_params.get("merchant")
        products = search_products(query, merchant_id=merchant_id)
        return Response({
            "results": ProductListSerializer(products, many=True, context={"request": request}).data
        })


# ── Merchant panel views ───────────────────────────────────────────────────────

class MerchantProductListView(APIView):
    """GET /api/v1/merchant/products/ — merchant panel uchun mahsulotlar ro'yxati"""
    permission_classes = [IsAuthenticated, IsMerchantOwnerOrManager]

    def get(self, request):
        merchant = request.user.merchant_staff_profile.merchant
        search = request.query_params.get("q", "")
        products = get_products_for_merchant(merchant_id=merchant.id, search=search)
        paginator = StandardPagination()
        page = paginator.paginate_queryset(products, request)
        serializer = ProductListSerializer(page, many=True, context={"request": request})
        return paginator.get_paginated_response(serializer.data)


class MerchantProductCreateView(APIView):
    """POST /api/v1/merchant/products/ — yangi mahsulot qo'shish"""
    permission_classes = [IsAuthenticated, IsMerchantOwnerOrManager]

    def post(self, request):
        serializer = ProductCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        merchant = request.user.merchant_staff_profile.merchant
        product = create_product(merchant, serializer.validated_data)
        return Response(ProductDetailSerializer(product).data, status=status.HTTP_201_CREATED)


class MerchantProductUpdateView(APIView):
    """PATCH /api/v1/merchant/products/<pk>/ — mahsulotni yangilash"""
    permission_classes = [IsAuthenticated, IsMerchantOwnerOrManager]

    def patch(self, request, pk):
        serializer = ProductUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        merchant = request.user.merchant_staff_profile.merchant
        try:
            product = update_product(pk, merchant, serializer.validated_data)
        except ProductNotFound as e:
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
        return Response(ProductDetailSerializer(product).data)


class ProductToggleAvailabilityView(APIView):
    """POST /api/v1/merchant/products/<pk>/toggle-availability/"""
    permission_classes = [IsAuthenticated, IsMerchantOwnerOrManager]

    def post(self, request, pk):
        is_available = request.data.get("is_available")
        if is_available is None:
            return Response(
                {"detail": "is_available maydoni kerak."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            product = toggle_product_availability(pk, merchant=request.user.merchant_staff_profile.merchant, is_available=bool(is_available))
        except ProductNotFound as e:
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
        return Response({"id": str(product.id), "is_available": product.is_available})