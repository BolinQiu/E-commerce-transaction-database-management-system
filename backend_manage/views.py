from django.shortcuts import render, redirect
from django.db import connection
from django.contrib import messages
from .forms import (
    ModifyProductForm,
    AddProductForm,
    AddStockForm,
    AssignLogisticsForm,
    QueryProductForm,
    QueryOrderForm,
    QueryReviewForm,
)
from django.http import JsonResponse
import json

def manage_dashboard(request):
    """
    管理后台主界面
    """
    return render(request, 'backend_manage/manage_dashboard.html')

# ===== 陈列柜相关视图 =====

def list_products(request):
    """
    列出所有商品或根据查询条件过滤商品
    """
    form = QueryProductForm(request.GET or None)
    query = ""
    params = []
    if form.is_valid():
        conditions = []
        if form.cleaned_data.get('min_stock') is not None:
            conditions.append("stock >= %s")
            params.append(form.cleaned_data['min_stock'])
        if form.cleaned_data.get('max_stock') is not None:
            conditions.append("stock <= %s")
            params.append(form.cleaned_data['max_stock'])
        if form.cleaned_data.get('start_date'):
            conditions.append("created_at >= %s")
            params.append(form.cleaned_data['start_date'])
        if form.cleaned_data.get('end_date'):
            conditions.append("created_at <= %s")
            params.append(form.cleaned_data['end_date'])
        if form.cleaned_data.get('min_price') is not None:
            conditions.append("price >= %s")
            params.append(form.cleaned_data['min_price'])
        if form.cleaned_data.get('max_price') is not None:
            conditions.append("price <= %s")
            params.append(form.cleaned_data['max_price'])
        if conditions:
            query = "WHERE " + " AND ".join(conditions)
    with connection.cursor() as cursor:
        sql = f"SELECT product_id, product_name, product_description, price, stock, created_at FROM products {query}"
        cursor.execute(sql, params)
        products = cursor.fetchall()
    context = {
        'products': products,
        'form': form,
    }
    return render(request, 'backend_manage/list_products.html', context)

def modify_product(request):
    """
    修改商品信息（描述、单价）
    """
    product_id = request.GET.get('product_id')
    if request.method == 'POST':
        form = ModifyProductForm(request.POST)
        if form.is_valid():
            product_description = form.cleaned_data.get('product_description')
            price = form.cleaned_data.get('price')
            with connection.cursor() as cursor:
                if product_description and price:
                    sql = "UPDATE products SET product_description = %s, price = %s WHERE product_id = %s"
                    cursor.execute(sql, [product_description, price, product_id])
                elif product_description:
                    sql = "UPDATE products SET product_description = %s WHERE product_id = %s"
                    cursor.execute(sql, [product_description, product_id])
                elif price:
                    sql = "UPDATE products SET price = %s WHERE product_id = %s"
                    cursor.execute(sql, [price, product_id])
                else:
                    messages.error(request, "没有提供任何修改内容。")
                    return redirect('list_products')
                messages.success(request, "商品信息已更新。")
            return redirect('list_products')
    else:
        form = ModifyProductForm()
    return render(request, 'backend_manage/modify_product.html', {'form': form})

def add_product(request):
    """
    添加新商品
    """
    if request.method == 'POST':
        form = AddProductForm(request.POST)
        if form.is_valid():
            product_name = form.cleaned_data['product_name']
            product_description = form.cleaned_data.get('product_description', '')
            price = form.cleaned_data['price']
            stock = form.cleaned_data['stock']
            with connection.cursor() as cursor:
                sql = """
                    INSERT INTO products (product_name, product_description, price, stock, created_at)
                    VALUES (%s, %s, %s, %s, NOW())
                """
                cursor.execute(sql, [product_name, product_description, price, stock])
                messages.success(request, "新商品已添加。")
            return redirect('list_products')
    else:
        form = AddProductForm()
    return render(request, 'backend_manage/add_product.html', {'form': form})

def add_stock(request):
    """
    为现有商品添加库存
    """
    if request.method == 'POST':
        form = AddStockForm(request.POST)
        if form.is_valid():
            product_id = form.cleaned_data['product_id']
            additional_stock = form.cleaned_data['additional_stock']
            with connection.cursor() as cursor:
                sql = "UPDATE products SET stock = stock + %s WHERE product_id = %s"
                cursor.execute(sql, [additional_stock, product_id])
                if cursor.rowcount == 0:
                    messages.error(request, "未找到对应的商品ID。")
                else:
                    messages.success(request, "库存已更新。")
            return redirect('list_products')
    else:
        form = AddStockForm()
    return render(request, 'backend_manage/add_stock.html', {'form': form})

def delete_product(request, product_id):
    """
    下架（删除）商品
    """
    with connection.cursor() as cursor:
        sql = "DELETE FROM products WHERE product_id = %s"
        cursor.execute(sql, [product_id])
        if cursor.rowcount == 0:
            messages.error(request, "未找到对应的商品ID。")
        else:
            messages.success(request, "商品已删除。")
    return redirect('list_products')

# ===== 我的订单相关视图 =====

def list_orders(request):
    """
    列出所有订单或根据查询条件过滤订单
    """
    form = QueryOrderForm(request.GET or None)
    query = ""
    params = []
    if form.is_valid():
        conditions = []
        if form.cleaned_data.get('start_date'):
            conditions.append("o.created_at >= %s")
            params.append(form.cleaned_data['start_date'])
        if form.cleaned_data.get('end_date'):
            conditions.append("o.created_at <= %s")
            params.append(form.cleaned_data['end_date'])
        if form.cleaned_data.get('tracking_number'):
            conditions.append("l.tracking_number = %s")
            params.append(form.cleaned_data['tracking_number'])
        if conditions:
            query = "WHERE " + " AND ".join(conditions)
    with connection.cursor() as cursor:
        sql = f"""
            SELECT o.order_id, o.created_at, o.status, l.tracking_number, l.carrier
            FROM orders o
            LEFT JOIN logistics l ON o.order_id = l.order_id
            {query}
        """
        cursor.execute(sql, params)
        orders = cursor.fetchall()
    context = {
        'orders': orders,
        'form': form,
    }
    return render(request, 'backend_manage/list_orders.html', context)

def assign_logistics(request):
    """
    为订单分配物流承运人和追踪号码
    """
    if request.method == 'POST':
        form = AssignLogisticsForm(request.POST)
        if form.is_valid():
            order_id = form.cleaned_data['order_id']
            carrier = form.cleaned_data['carrier']
            tracking_number = form.cleaned_data['tracking_number']
            with connection.cursor() as cursor:
                # 检查订单是否存在且状态为 'shipped'
                check_sql = "SELECT status FROM orders WHERE order_id = %s"
                cursor.execute(check_sql, [order_id])
                result = cursor.fetchone()
                if not result:
                    messages.error(request, "未找到对应的订单ID。")
                    return redirect('list_orders')
                status = result[0]
                if status != 'shipped':
                    messages.error(request, "只有已发货的订单可以分配物流。")
                    return redirect('list_orders')
                # 插入或更新物流信息
                upsert_sql = """
                    INSERT INTO logistics (order_id, carrier, tracking_number, status, updated_at)
                    VALUES (%s, %s, %s, 'shipping', NOW())
                    ON DUPLICATE KEY UPDATE 
                        carrier = VALUES(carrier), 
                        tracking_number = VALUES(tracking_number), 
                        status = VALUES(status), 
                        updated_at = VALUES(updated_at)
                """
                cursor.execute(upsert_sql, [order_id, carrier, tracking_number])
                messages.success(request, "物流信息已更新。")
            return redirect('list_orders')
    else:
        form = AssignLogisticsForm()
    return render(request, 'backend_manage/assign_logistics.html', {'form': form})

def track_order(request, order_id):
    """
    查看订单的物流信息
    """
    with connection.cursor() as cursor:
        sql = """
            SELECT l.carrier, l.tracking_number, l.status, l.updated_at
            FROM logistics l
            WHERE l.order_id = %s
        """
        cursor.execute(sql, [order_id])
        logistics = cursor.fetchone()
    if not logistics:
        messages.error(request, "未找到对应的物流信息。")
        return redirect('list_orders')
    context = {
        'order_id': order_id,
        'carrier': logistics[0],
        'tracking_number': logistics[1],
        'status': logistics[2],
        'updated_at': logistics[3],
    }
    return render(request, 'backend_manage/track_order.html', context)

def query_orders_by_product(request, product_id):
    """
    查询某个商品ID对应的订单，以跟踪商品的流向
    """
    with connection.cursor() as cursor:
        sql = """
            SELECT o.order_id, o.created_at, o.status
            FROM orders o
            JOIN order_items oi ON o.order_id = oi.order_id
            WHERE oi.product_id = %s
        """
        cursor.execute(sql, [product_id])
        orders = cursor.fetchall()
    context = {
        'orders': orders,
        'product_id': product_id,
    }
    return render(request, 'backend_manage/query_orders_by_product.html', context)

# ===== 用户评论相关视图 =====

def list_reviews(request):
    """
    列出所有用户评论或根据商品名称查询评论
    """
    form = QueryReviewForm(request.GET or None)
    reviews = []
    if form.is_valid():
        product_name = form.cleaned_data.get('product_name')
        if product_name:
            with connection.cursor() as cursor:
                sql = """
                    SELECT r.review_id, p.product_name, u.username, r.rating, r.comment, r.created_at
                    FROM reviews r
                    JOIN products p ON r.product_id = p.product_id
                    JOIN users u ON r.user_id = u.user_id
                    WHERE p.product_name LIKE %s
                """
                cursor.execute(sql, [f"%{product_name}%"])
                reviews = cursor.fetchall()
    context = {
        'reviews': reviews,
        'form': form,
    }
    return render(request, 'backend_manage/list_reviews.html', context)
