from django.shortcuts import render
from supplychain.models import CompanyRelationship


def index(request):
    relationships = CompanyRelationship.objects.filter(is_active=True).select_related("source_ticker").order_by("-created_at")[:100]
    return render(request, "supplychain/index.html", {"relationships": relationships})