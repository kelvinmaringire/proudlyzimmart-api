"""
Admin views for import/export functionality.
These views are registered at the Wagtail admin level.
"""
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpResponse
from django.core.exceptions import PermissionDenied
from wagtail_modeladmin.helpers import AdminURLHelper

from .models import Product, Category
from .resources import ProductResource, CategoryResource
from .services import (
    import_data,
    export_data,
    process_import_result,
)


def get_model_admin_instance(model_class):
    """Get ModelAdmin instance for a given model."""
    from .wagtail_hooks import ProductAdmin, CategoryAdmin
    
    if model_class == Product:
        admin_class = ProductAdmin
    elif model_class == Category:
        admin_class = CategoryAdmin
    else:
        return None
    
    model_admin = admin_class()
    if not hasattr(model_admin, 'url_helper'):
        model_admin.url_helper = AdminURLHelper(model_admin.model)
    
    return model_admin


def product_import_view(request):
    """
    Handle product import.
    
    GET /admin/products/product/import/
    POST /admin/products/product/import/
    """
    if not request.user.is_staff:
        raise PermissionDenied
    
    model_admin = get_model_admin_instance(Product)
    if not model_admin:
        messages.error(request, "Product admin not found.")
        return redirect('/admin/')
    
    if request.method == 'POST':
        file_format = request.POST.get('file_format', 'csv')
        file = request.FILES.get('import_file')
        
        if not file:
            messages.error(request, "Please select a file to import.")
            return render(request, 'products/admin/import.html', {
                'model_admin': model_admin,
                'formats': [('csv', 'CSV'), ('xlsx', 'Excel')],
            })
        
        try:
            result = import_data(ProductResource, file, file_format)
            import_status = process_import_result(result)
            
            if import_status['has_errors']:
                totals = import_status['totals']
                if totals.get('new', 0) > 0 or totals.get('update', 0) > 0:
                    messages.warning(
                        request,
                        f"Import partially completed. {totals.get('new', 0)} new, "
                        f"{totals.get('update', 0)} updated records. Errors:\n" + 
                        "\n".join(import_status['error_messages'][:10])
                    )
                else:
                    messages.error(
                        request,
                        f"Import failed with errors:\n" + 
                        "\n".join(import_status['error_messages'][:10])
                    )
            else:
                totals = import_status['totals']
                messages.success(
                    request,
                    f"Successfully imported {totals.get('new', 0)} new, "
                    f"{totals.get('update', 0)} updated, "
                    f"{totals.get('skip', 0)} skipped records."
                )
        
        except Exception as e:
            messages.error(request, f"Error importing file: {str(e)}")
        
        return redirect(model_admin.url_helper.index_url)
    
    return render(request, 'products/admin/import.html', {
        'model_admin': model_admin,
        'formats': [('csv', 'CSV'), ('xlsx', 'Excel')],
    })


def product_export_view(request):
    """
    Handle product export.
    
    GET /admin/products/product/export/?format=csv
    GET /admin/products/product/export/?format=xlsx
    """
    if not request.user.is_staff:
        raise PermissionDenied
    
    model_admin = get_model_admin_instance(Product)
    if not model_admin:
        messages.error(request, "Product admin not found.")
        return redirect('/admin/')
    
    file_format = request.GET.get('format', 'csv')
    
    try:
        export_result = export_data(ProductResource, Product.objects.all(), file_format)
        
        response = HttpResponse(
            export_result['data'],
            content_type=export_result['content_type']
        )
        response['Content-Disposition'] = (
            f'attachment; filename="product_export.{export_result["extension"]}"'
        )
        
        return response
    
    except Exception as e:
        messages.error(request, f"Error exporting products: {str(e)}")
        return redirect(model_admin.url_helper.index_url)


def category_import_view(request):
    """
    Handle category import.
    
    GET /admin/products/category/import/
    POST /admin/products/category/import/
    """
    if not request.user.is_staff:
        raise PermissionDenied
    
    model_admin = get_model_admin_instance(Category)
    if not model_admin:
        messages.error(request, "Category admin not found.")
        return redirect('/admin/')
    
    if request.method == 'POST':
        file_format = request.POST.get('file_format', 'csv')
        file = request.FILES.get('import_file')
        
        if not file:
            messages.error(request, "Please select a file to import.")
            return render(request, 'products/admin/import.html', {
                'model_admin': model_admin,
                'formats': [('csv', 'CSV'), ('xlsx', 'Excel')],
            })
        
        try:
            result = import_data(CategoryResource, file, file_format)
            import_status = process_import_result(result)
            
            if import_status['has_errors']:
                totals = import_status['totals']
                if totals.get('new', 0) > 0 or totals.get('update', 0) > 0:
                    messages.warning(
                        request,
                        f"Import partially completed. {totals.get('new', 0)} new, "
                        f"{totals.get('update', 0)} updated records. Errors:\n" + 
                        "\n".join(import_status['error_messages'][:10])
                    )
                else:
                    messages.error(
                        request,
                        f"Import failed with errors:\n" + 
                        "\n".join(import_status['error_messages'][:10])
                    )
            else:
                totals = import_status['totals']
                messages.success(
                    request,
                    f"Successfully imported {totals.get('new', 0)} new, "
                    f"{totals.get('update', 0)} updated, "
                    f"{totals.get('skip', 0)} skipped records."
                )
        
        except Exception as e:
            messages.error(request, f"Error importing file: {str(e)}")
        
        return redirect(model_admin.url_helper.index_url)
    
    return render(request, 'products/admin/import.html', {
        'model_admin': model_admin,
        'formats': [('csv', 'CSV'), ('xlsx', 'Excel')],
    })


def category_export_view(request):
    """
    Handle category export.
    
    GET /admin/products/category/export/?format=csv
    GET /admin/products/category/export/?format=xlsx
    """
    if not request.user.is_staff:
        raise PermissionDenied
    
    model_admin = get_model_admin_instance(Category)
    if not model_admin:
        messages.error(request, "Category admin not found.")
        return redirect('/admin/')
    
    file_format = request.GET.get('format', 'csv')
    
    try:
        export_result = export_data(CategoryResource, Category.objects.all(), file_format)
        
        response = HttpResponse(
            export_result['data'],
            content_type=export_result['content_type']
        )
        response['Content-Disposition'] = (
            f'attachment; filename="category_export.{export_result["extension"]}"'
        )
        
        return response
    
    except Exception as e:
        messages.error(request, f"Error exporting categories: {str(e)}")
        return redirect(model_admin.url_helper.index_url)
