from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, FileResponse, Http404
from django.contrib import messages
from django.db.models import Count, Prefetch, ForeignKey, Q
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.core.exceptions import FieldDoesNotExist
from .models import Document, DocumentCategory, SubCategory
from .forms import DocumentForm, DocumentCategoryForm
from django.views.decorators.http import require_GET
from django.db import IntegrityError, transaction
import logging
from pathlib import Path
from django.contrib.auth import get_user_model



logger = logging.getLogger(__name__)
User = get_user_model()

@login_required
def upload_document(request):
    user_groups = request.user.groups.all()
    categories = DocumentCategory.objects.filter(
        Q(groups__in=user_groups) | Q(is_public=True)
    ).distinct()

    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)

        # Restrict category choices to categories available to the user (if field exists)
        if hasattr(form, 'fields') and 'category' in form.fields:
            form.fields['category'].queryset = categories

        if form.is_valid():
            # prepare but don't commit so we can inspect and set required fields
            document = form.save(commit=False)

            # 1) Always attempt to set common user fields if present
            for possible in ('author', 'owner', 'created_by', 'uploaded_by', 'user'):
                if hasattr(document, possible) and getattr(document, possible) in (None, ''):
                    try:
                        setattr(document, possible, request.user)
                    except Exception:
                        # ignore if not a FK to user
                        pass

            # 2) Inspect model fields for required (NOT NULL) ones that are empty
            missing_required = []
            ModelClass = document.__class__
            for f in ModelClass._meta.fields:
                # skip auto fields and auto timestamp fields
                if f.auto_created or getattr(f, 'auto_now_add', False) or getattr(f, 'auto_now', False):
                    continue
                # skip PK
                if f.primary_key:
                    continue
                # skip fields that allow null or blank or have a default
                if getattr(f, 'null', False) or getattr(f, 'blank', False) or f.has_default():
                    continue

                # field is required at DB level — check current value on instance
                val = getattr(document, f.name, None)
                if val in (None, ''):
                    # If it's a FK to User, set it
                    if isinstance(f, ForeignKey) and f.remote_field.model == User:
                        try:
                            setattr(document, f.name, request.user)
                        except Exception:
                            pass
                    else:
                        # try to populate from form.cleaned_data if available
                        if hasattr(form, 'cleaned_data') and f.name in form.cleaned_data and form.cleaned_data.get(f.name) not in (None, ''):
                            try:
                                setattr(document, f.name, form.cleaned_data.get(f.name))
                            except Exception:
                                pass

                # re-evaluate after attempted assignment
                val_after = getattr(document, f.name, None)
                if val_after in (None, ''):
                    missing_required.append(f.name)

            # if we still have missing required fields, log and inform user
            if missing_required:
                logger.error(
                    "Document missing required fields before save: %s (user=%s). Form cleaned data keys: %s",
                    missing_required, request.user, list(getattr(form, 'cleaned_data', {}).keys())
                )
                messages.error(
                    request,
                    "The form is missing required information (fields: {}). Please check the form and try again.".format(
                        ', '.join(missing_required)
                    )
                )
                # Render the form again so user can correct; do NOT attempt to save
                return render(request, 'documents/upload_document.html', {'form': form, 'categories': categories})

            # Attempt save
            try:
                with transaction.atomic():
                    document.save()
                    # Save any M2M fields
                    try:
                        form.save_m2m()
                    except Exception:
                        pass

                messages.success(request, "Your document has been successfully uploaded.")

                # Redirect to subcategory if set, otherwise category or listing
                subcat = getattr(document, 'subcategory', None)
                if subcat:
                    return redirect('documents:subcategory_detail', pk=subcat.pk)
                cat = getattr(document, 'category', None)
                if cat:
                    return redirect('documents:category_detail', pk=cat.pk)
                return redirect('documents:document_list')

            except IntegrityError as exc:
                # Log the detailed exception and show friendly message.
                logger.exception("IntegrityError while saving Document (user=%s): %s", request.user, exc)
                messages.error(request, "Could not save document (database error). Please contact the administrator.")
                # Re-render form so user doesn't lose inputs
                return render(request, 'documents/upload_document.html', {'form': form, 'categories': categories})

        else:
            messages.error(request, "Please correct the errors below and try again.")

    else:
        form = DocumentForm()
        if hasattr(form, 'fields') and 'category' in form.fields:
            form.fields['category'].queryset = categories

    return render(request, 'documents/upload_document.html', {
        'form': form,
        'categories': categories
    })



def public_downloads(request):
    category = DocumentCategory.objects.filter(name__iexact="Downloads").first()

    if not category:
        context = {
            "category": None,
            "all_subcategories": [],
            "subcategories": [],
            "selected_subcat_id": None,
            "query": "",
            "error_message": "Downloads category has not been created yet.",
        }
        return render(request, "documents/public_downloads.html", context)

    selected_subcat_id = request.GET.get("subcategory")
    query = request.GET.get("q", "").strip()

    documents_qs = Document.objects.all()

    if query:
        documents_qs = documents_qs.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query)
        )

    all_subcategories = SubCategory.objects.filter(category=category).order_by("name")

    subcategories = all_subcategories

    if selected_subcat_id:
        subcategories = subcategories.filter(id=selected_subcat_id)

    subcategories = subcategories.prefetch_related(
        Prefetch("document_set", queryset=documents_qs, to_attr="filtered_documents")
    )

    context = {
        "category": category,
        "all_subcategories": all_subcategories,
        "subcategories": subcategories,
        "selected_subcat_id": selected_subcat_id,
        "query": query,
    }

    return render(request, "documents/public_downloads.html", context)
# ------------------------
# Category / Subcategory
# ------------------------
@login_required
def category_detail(request, pk):
    user_groups = request.user.groups.all()

    # Public folders do not need a group assignment. Private folders still do.
    category = DocumentCategory.objects.filter(pk=pk).filter(
        Q(is_public=True) | Q(groups__in=user_groups)
    ).distinct().first()
    if not category:
        raise Http404("Category not found or access denied")

    # Subcategories for this category visible to user
    subcategories = SubCategory.objects.filter(category=category)
    if not category.is_public:
        subcategories = subcategories.filter(groups__in=user_groups)
    subcategories = subcategories.distinct()

    # Prefetch subcategories for sidebar/categories
    subcategory_qs = SubCategory.objects.filter(
        Q(category__is_public=True) | Q(groups__in=user_groups)
    ).distinct()
    categories = DocumentCategory.objects.filter(
        Q(is_public=True) | Q(groups__in=user_groups)
    ).prefetch_related(
        Prefetch('subcategories', queryset=subcategory_qs)
    ).distinct()

    # Build document queryset defensively (respect groups, is_active, ordering if fields exist)
    documents_qs = Document.objects.filter(category=category)

    # Filter by groups if Document has groups M2M
    if not category.is_public:
        try:
            Document._meta.get_field('groups')
            documents_qs = documents_qs.filter(groups__in=user_groups).distinct()
        except FieldDoesNotExist:
            documents_qs = documents_qs.distinct()

    # Only active if field exists
    try:
        Document._meta.get_field('is_active')
        documents_qs = documents_qs.filter(is_active=True)
    except FieldDoesNotExist:
        pass

    # Order by created_at if exists
    try:
        Document._meta.get_field('created_at')
        documents_qs = documents_qs.order_by('-created_at')
    except FieldDoesNotExist:
        documents_qs = documents_qs.order_by('-date_posted', 'pk')

    # Pagination (12 per page)
    paginator = Paginator(documents_qs, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'category': category,
        'subcategories': subcategories,
        'categories': categories,
        'active_category_pk': category.pk,
        'active_subcategory_pk': None,
        'documents': documents_qs,  # full queryset fallback
        'page_obj': page_obj,
    }
    return render(request, 'documents/category_detail.html', context)


@login_required
def subcategory_detail(request, pk):
    user_groups = request.user.groups.all()

    subcategory = SubCategory.objects.filter(pk=pk).filter(
        Q(category__is_public=True) | Q(groups__in=user_groups)
    ).distinct().first()
    if not subcategory:
        raise Http404("Subcategory not found or access denied")

    documents_qs = Document.objects.filter(subcategory=subcategory)
    if not subcategory.category.is_public:
        try:
            Document._meta.get_field('groups')
            documents_qs = documents_qs.filter(groups__in=user_groups).distinct()
        except FieldDoesNotExist:
            documents_qs = documents_qs.distinct()

    # pagination optional: reuse same pattern if desired (not paginating here)
    subcategory_qs = SubCategory.objects.filter(
        Q(category__is_public=True) | Q(groups__in=user_groups)
    ).distinct()
    categories = DocumentCategory.objects.filter(
        Q(is_public=True) | Q(groups__in=user_groups)
    ).prefetch_related(
        Prefetch('subcategories', queryset=subcategory_qs)
    ).distinct()

    return render(request, 'documents/subcategory_detail.html', {
        'subcategory': subcategory,
        'documents': documents_qs,
        'categories': categories,
    })


# ------------------------
# Listing / Upload
# ------------------------
@login_required
def document_list(request):
    user_groups = request.user.groups.all()

    # Annotate categories with subcategory and document counts
    categories = DocumentCategory.objects.filter(groups__in=user_groups).annotate(
        subcategory_count=Count('subcategories', distinct=True),
        document_count=Count('document', distinct=True)
    ).distinct()

    # Compute total documents and subcategories across all categories
    total_documents = sum(cat.document_count for cat in categories)
    total_subcategories = sum(cat.subcategory_count for cat in categories)

    return render(request, 'documents/document_list.html', {
        'categories': categories,
        'total_documents': total_documents,
        'total_subcategories': total_subcategories,
    })



# ------------------------
# Document detail / view / preview / download
# ------------------------
@login_required
def document_detail(request, pk):
    document = get_object_or_404(Document, pk=pk)
    return render(request, 'documents/document_detail.html', {'document': document})


@login_required
def view_document(request, pk):
    document = get_object_or_404(Document, pk=pk)
    extension = Path(document.file.name).suffix.lower()
    return render(request, 'documents/view_document.html', {
        'document': document,
        'extension': extension,
        'can_embed': extension in {'.pdf', '.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.txt'},
    })


@login_required
def embedded_preview(request, pk):
    """
    Render an embedded preview page for supported formats.
    Note: this single implementation replaces the duplicate version you had.
    """
    document = get_object_or_404(Document, pk=pk)
    extension = Path(document.file.name).suffix.lower()
    return render(request, 'documents/embedded_preview.html', {
        'document': document,
        'extension': extension,
        'can_embed': extension in {'.pdf', '.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.txt'},
    })


@login_required
def inline_document(request, pk):
    """Stream a document inline for the authenticated browser viewer."""
    document = get_object_or_404(Document, pk=pk)
    return FileResponse(
        document.file.open('rb'),
        as_attachment=False,
        filename=document.file.name.rsplit('/', 1)[-1],
    )


@login_required
def download_document(request, pk):
    document = get_object_or_404(Document, pk=pk)
    # return FileResponse for streaming download
    return FileResponse(getattr(document, 'file').open(), as_attachment=True, filename=getattr(document, 'file').name)


def download_public_document(request, pk):
    """Download a document only when its folder is explicitly public."""
    document = get_object_or_404(
        Document.objects.select_related('category'),
        pk=pk,
        category__is_public=True,
    )
    return FileResponse(
        document.file.open('rb'),
        as_attachment=True,
        filename=document.file.name.rsplit('/', 1)[-1],
    )


# ------------------------
# Edit / Update / Delete
# ------------------------
@login_required
def document_edit(request, pk):
    """
    Edit document (GET shows form; POST saves).
    URL name: documents:document_edit
    """
    doc = get_object_or_404(Document, pk=pk)
    # optional permission: only owner or staff can edit
    if not (request.user.is_staff or getattr(doc, 'owner', None) == request.user):
        messages.error(request, "You don't have permission to edit this document.")
        return redirect('documents:document_detail', pk=doc.pk)

    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES, instance=doc)
        if form.is_valid():
            form.save()
            messages.success(request, "Document updated successfully.")
            # redirect back to the document detail or subcategory
            subcat = getattr(doc, 'subcategory', None)
            if subcat:
                return redirect('documents:subcategory_detail', pk=subcat.pk)
            return redirect('documents:document_detail', pk=doc.pk)
    else:
        form = DocumentForm(instance=doc)

    return render(request, 'documents/document_edit.html', {'form': form, 'document': doc})


@require_POST
@login_required
def delete_document(request, pk):
    """
    Delete document via POST only. URL name: documents:document_delete
    Template should submit a small form with csrf token.
    """
    doc = get_object_or_404(Document, pk=pk)

    # optional permission: only owner or staff can delete
    if not (request.user.is_staff or getattr(doc, 'owner', None) == request.user):
        messages.error(request, "You don't have permission to delete this document.")
        return redirect('documents:document_detail', pk=doc.pk)

    # capture redirect target before deletion
    subcat = getattr(doc, 'subcategory', None)
    cat = getattr(doc, 'category', None)
    doc.delete()
    messages.success(request, "Document deleted successfully.")

    if subcat:
        return redirect('documents:subcategory_detail', pk=subcat.pk)
    if cat:
        return redirect('documents:category_detail', pk=cat.pk)
    return redirect('documents:document_list')


# ------------------------
# Downloads & Helpers
# ------------------------
def get_subcategories(request):
    category_id = request.GET.get('category_id')
    subcategories = SubCategory.objects.filter(category_id=category_id).values('id', 'name')
    return JsonResponse({'subcategories': list(subcategories)})


@require_GET
def ajax_subcategories(request):
    """
    Expects ?category_id=<id>
    Returns: [{ "id": 1, "name": "Sub 1" }, ...]
    """
    cat_id = request.GET.get('category_id')
    if not cat_id:
        return JsonResponse({"results": []})
    qs = SubCategory.objects.filter(category_id=cat_id).order_by('name').values('id', 'name')
    data = list(qs)
    return JsonResponse({"results": data})

@login_required
def download_view(request):
    downloads_category = get_object_or_404(DocumentCategory, name='Downloads')
    subcategories = downloads_category.subcategories.all()
    return render(request, 'documents/downloads.html', {
        'downloads_category': downloads_category,
        'subcategories': subcategories,
    })


@login_required
def download_subcategory_detail(request, pk):
    subcategory = get_object_or_404(SubCategory, pk=pk)
    documents = Document.objects.filter(subcategory=subcategory)
    return render(request, 'documents/download_subcategory_detail.html', {
        'subcategory': subcategory,
        'documents': documents,
    })


