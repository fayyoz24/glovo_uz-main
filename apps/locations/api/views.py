from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from apps.locations.api.serializers import AddressSerializer, ServiceZoneSerializer
from apps.locations.selectors import get_user_addresses, get_active_zones
from apps.locations.services import create_address, update_address, delete_address, set_default_address


class AddressListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        addresses = get_user_addresses(request.user)
        return Response(AddressSerializer(addresses, many=True).data)

    def post(self, request):
        serializer = AddressSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        address = create_address(request.user, serializer.validated_data)
        return Response(AddressSerializer(address).data, status=status.HTTP_201_CREATED)


class AddressDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        serializer = AddressSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        address = update_address(request.user, pk, serializer.validated_data)
        return Response(AddressSerializer(address).data)

    def delete(self, request, pk):
        delete_address(request.user, pk)
        return Response(status=status.HTTP_204_NO_CONTENT)


class SetDefaultAddressView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        address = set_default_address(request.user, pk)
        return Response(AddressSerializer(address).data)


class ServiceZoneListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        city = request.query_params.get("city")
        zones = get_active_zones(city=city)
        return Response(ServiceZoneSerializer(zones, many=True).data)
