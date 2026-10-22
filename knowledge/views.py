from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from knowledge.models import KnowledgeDocument, KnowledgeChunk


def knowledge_list(request):
    docs = KnowledgeDocument.objects.all().order_by("-uploaded_at")
    return render(request, "knowledge/list.html", {"docs": docs})


def knowledge_upload(request):
    if request.method == "POST":
        title = request.POST.get("title", "")
        category = request.POST.get("category", "general")
        source = request.POST.get("source", "")
        content = request.POST.get("content", "")
        uploaded_file = request.FILES.get("file")
        if uploaded_file:
            try:
                content = uploaded_file.read().decode("utf-8", errors="ignore")
            except Exception:
                content = ""
        if not title:
            title = uploaded_file.name if uploaded_file else "Untitled"
        if content:
            doc = KnowledgeDocument.objects.create(
                title=title, category=category, source=source, content=content,
                source_url=request.POST.get("source_url", ""),
            )
            messages.success(request, f"Uploaded '{title}'. Run processing to chunk and embed.")
        else:
            messages.error(request, "No content provided.")
    return redirect("knowledge:list")


def knowledge_detail(request, doc_id):
    doc = get_object_or_404(KnowledgeDocument, id=doc_id)
    chunks = doc.chunks.all().order_by("chunk_index")
    return render(request, "knowledge/detail.html", {"doc": doc, "chunks": chunks})


def knowledge_delete(request, doc_id):
    if request.method == "POST":
        doc = get_object_or_404(KnowledgeDocument, id=doc_id)
        title = doc.title
        doc.delete()
        messages.success(request, f"Deleted '{title}'.")
    return redirect("knowledge:list")