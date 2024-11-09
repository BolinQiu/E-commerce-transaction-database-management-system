import random
import uuid
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
    Adds stock to an existing product by looking up the product by name.
    """
    if request.method == 'POST':
        form = AddStockForm(request.POST)
        if form.is_valid():
            product_name = form.cleaned_data['product_name']
            additional_stock = form.cleaned_data['additional_stock']
            with connection.cursor() as cursor:
                # Fetch the product_id based on product_name
                cursor.execute("SELECT product_id FROM products WHERE product_name = %s", [product_name])
                result = cursor.fetchone()
                
                if result:
                    product_id = result[0]
                    # Update the stock
                    cursor.execute("UPDATE products SET stock = stock + %s WHERE product_id = %s", [additional_stock, product_id])
                    messages.success(request, "库存已更新。")
                else:
                    messages.error(request, "未找到对应的商品名称。")
            return redirect('list_products')
    else:
        form = AddStockForm()
    return render(request, 'backend_manage/add_stock.html', {'form': form})


def delete_product(request, product_id):
    with connection.cursor() as cursor:
        # 先删除关联的 order_items
        cursor.execute("DELETE FROM order_items WHERE product_id = %s", [product_id])
        
        # 然后删除商品本身
        cursor.execute("DELETE FROM products WHERE product_id = %s", [product_id])
        
        if cursor.rowcount == 0:
            messages.error(request, "未找到对应的商品ID。")
        else:
            messages.success(request, "商品已下架。")
    return redirect('list_products')


# ===== 我的订单相关视图 =====

def list_orders(request):
    """
    列出所有订单或根据查询条件过滤订单
    """
    form = QueryOrderForm(request.GET or None)
    base_query = """
        SELECT DISTINCT o.order_id, o.created_at, o.status, l.tracking_number, l.carrier
        FROM orders o
        LEFT JOIN logistics l ON o.order_id = l.order_id
    """
    join_clause = ""
    params = []
    conditions = []

    if form.is_valid():
        if form.cleaned_data.get('start_date'):
            conditions.append("o.created_at >= %s")
            params.append(form.cleaned_data['start_date'])
        if form.cleaned_data.get('end_date'):
            conditions.append("o.created_at <= %s")
            params.append(form.cleaned_data['end_date'])
        if form.cleaned_data.get('tracking_number'):
            conditions.append("l.tracking_number = %s")
            params.append(form.cleaned_data['tracking_number'])
        if form.cleaned_data.get('product_name'):
            # 如果输入了商品名称，则需要 JOIN `order_items` 和 `products`
            join_clause = """
                JOIN order_items oi ON o.order_id = oi.order_id
                JOIN products p ON oi.product_id = p.product_id
            """
            conditions.append("p.product_name LIKE %s")
            params.append(f"%{form.cleaned_data['product_name']}%")

    # 构建最终的 SQL 查询
    query = base_query + join_clause
    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    with connection.cursor() as cursor:
        cursor.execute(query, params)
        orders = cursor.fetchall()

    context = {
        'orders': orders,
        'form': form,
    }
    return render(request, 'backend_manage/list_orders.html', context)


def generate_tracking_number(order_id):
    # 使用 order_id 作为随机数种子，以确保生成的追踪号是唯一且可复现的
    random.seed(order_id)
    tracking_number = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=8))
    return tracking_number


def assign_logistics(request):
    """
    Assign logistics carrier and tracking number to an order, and update the order status to 'delivered'.
    """
    order_id = request.GET.get('order_id')
    if request.method == 'POST':
        form = AssignLogisticsForm(request.POST)
        if form.is_valid():
            carrier = form.cleaned_data['carrier']
            tracking_number = generate_tracking_number(order_id)
            with connection.cursor() as cursor:
                # Check if an entry already exists in the logistics table for the order_id
                check_logistics_sql = "SELECT COUNT(*) FROM logistics WHERE order_id = %s"
                cursor.execute(check_logistics_sql, [order_id])
                logistics_count = cursor.fetchone()[0]
                
                if logistics_count > 0:
                    # Update existing logistics entry
                    update_logistics_sql = """
                        UPDATE logistics SET carrier = %s, tracking_number = %s, status = 'delivered', updated_at = NOW()
                        WHERE order_id = %s
                    """
                    cursor.execute(update_logistics_sql, [carrier, tracking_number, order_id])
                    messages.success(request, "物流信息已更新。")
                else:
                    # Insert new logistics entry if it doesn't exist
                    insert_logistics_sql = """
                        INSERT INTO logistics (order_id, carrier, tracking_number, status, updated_at)
                        VALUES (%s, %s, %s, 'delivered', NOW())
                    """
                    cursor.execute(insert_logistics_sql, [order_id, carrier, tracking_number])
                    messages.success(request, "物流信息已分配并生成物流记录。")

                # Update the order status to 'delivered'
                update_order_status_sql = "UPDATE orders SET status = 'delivered' WHERE order_id = %s"
                cursor.execute(update_order_status_sql, [order_id])
                
            return redirect('list_orders')
    else:
        initial_data = {'order_id': order_id, 'tracking_number': generate_tracking_number(order_id)}
        form = AssignLogisticsForm(initial=initial_data)
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
    查询某个商品对应的订单，以跟踪商品的流向
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

    # 构建 SQL 查询和参数
    sql = """
        SELECT r.review_id, p.product_name, u.username, r.rating, r.comment, r.created_at
        FROM reviews r
        JOIN products p ON r.product_id = p.product_id
        JOIN users u ON r.user_id = u.user_id
    """
    params = []

    # 如果表单有效且商品名称不为空，添加筛选条件
    if form.is_valid() and form.cleaned_data.get('product_name'):
        product_name = form.cleaned_data['product_name']
        sql += " WHERE p.product_name LIKE %s"
        params.append(f"%{product_name}%")

    # 执行查询
    with connection.cursor() as cursor:
        cursor.execute(sql, params)
        reviews = cursor.fetchall()

    context = {
        'reviews': reviews,
        'form': form,
    }
    return render(request, 'backend_manage/list_reviews.html', context)
