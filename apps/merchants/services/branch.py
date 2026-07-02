from django.db import transaction
from apps.merchants.models import MerchantBranch
from apps.merchants.selectors import get_branch_by_id
from apps.merchants.exceptions import BranchNotFound


def create_branch(merchant, validated_data: dict) -> MerchantBranch:
    with transaction.atomic():
        branch = MerchantBranch.objects.create(merchant=merchant, **validated_data)
    return branch


def update_branch(branch_id, merchant, validated_data: dict) -> MerchantBranch:
    branch = get_branch_by_id(branch_id, merchant_id=merchant.id)
    if not branch:
        raise BranchNotFound()
    for field, value in validated_data.items():
        setattr(branch, field, value)
    branch.save()
    return branch


def toggle_accepting_orders(branch_id, merchant, accepting: bool) -> MerchantBranch:
    branch = get_branch_by_id(branch_id, merchant_id=merchant.id)
    if not branch:
        raise BranchNotFound()
    branch.accepting_orders = accepting
    branch.save(update_fields=["accepting_orders"])
    return branch
