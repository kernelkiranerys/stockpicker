from django.shortcuts import render
from feedback.models import LessonLearned, TradeReview


def index(request):
    lessons = LessonLearned.objects.filter(is_active=True).order_by("-created_at")[:50]
    reviews = TradeReview.objects.order_by("-reviewed_at")[:20]
    return render(request, "feedback/index.html", {"lessons": lessons, "reviews": reviews})