from django.shortcuts import render
import json
from on_sale.models import Product, Order, OrderItem, User, Logistics
# Create your views here.
from django.db.models import Q
from django.contrib.auth.decorators import login_required


def app_index(request):
    return render(request, 'index.html')

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login
from on_sale.models import User
from django.contrib import messages
from django.http import HttpResponse
from django.db import connection

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        # 检查用户名和密码是否为空
        if not username or not password:
            messages.error(request, '用户名和密码不能为空')
            return render(request, 'login.html')

        try:
            with connection.cursor() as cursor:
                # 执行原生SQL查询，使用参数化查询防止SQL注入
                cursor.execute("""
                    SELECT user_id, password 
                    FROM users 
                    WHERE username = %s
                """, [username])
                row = cursor.fetchone()

                if row:
                    user_id, stored_password = row
                    if stored_password == password:
                        # 使用会话存储用户信息
                        request.session['user_id'] = user_id
                        request.session['username'] = username
                        messages.success(request, '登录成功')
                        return redirect('on_sale')
                    else:
                        messages.error(request, '密码错误')
                else:
                    messages.error(request, '用户不存在')
                    return HttpResponse('用户不存在')
                
        except Exception as e:
            # 记录异常日志（可选）
            # logger.error(f"登录失败: {e}")
            messages.error(request, '登录过程中发生错误，请稍后再试')
            return HttpResponse('登录过程中发生错误，请稍后再试')

    return render(request, 'login.html')


def register_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        address = request.POST.get('address')
        phone = request.POST.get('phone')
        
        # 检查必填字段是否为空
        if not username or not password or not address or not phone:
            messages.error(request, '所有字段都是必填的')
            return render(request, 'register.html')
        
        try:
            with connection.cursor() as cursor:
                # 检查用户名是否已存在
                cursor.execute("""
                    SELECT 1 FROM users WHERE username = %s
                """, [username])
                if cursor.fetchone():
                    messages.error(request, '用户名已存在')
                    return render(request, 'register.html')
                
                # 对密码进行哈希处理
                hashed_password = password
                
                # 插入新用户记录
                cursor.execute("""
                    INSERT INTO users (username, password, address, phone, created_at)
                    VALUES (%s, %s, %s, %s, NOW())
                """, [username, hashed_password, address, phone])
                
                # 提交事务（Django默认自动处理，但显式提交以确保）
                connection.commit()
                
                messages.success(request, '注册成功')
                return redirect('login')
        except Exception as e:
            # 回滚事务以防止部分提交
            connection.rollback()
            # 记录异常日志（可选）
            # import logging
            # logger = logging.getLogger(__name__)
            # logger.error(f"注册失败: {e}")
            messages.error(request, f'注册失败：{str(e)}')
                
    return render(request, 'register.html')

# views.py
from django.http import JsonResponse
from .models import Product

def get_products(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT product_id, product_name, product_description, price, stock
                FROM products
            """)
            rows = cursor.fetchall()
            columns = [col[0] for col in cursor.description]
            products = [dict(zip(columns, row)) for row in rows]
        return JsonResponse(products, safe=False)
    except Exception:
        return JsonResponse({'error': '获取商品列表失败'}, status=500)



def search_products(request):
    name = request.GET.get('name', '')
    description = request.GET.get('description', '')
    
    query = "SELECT product_id, product_name, product_description, price, stock FROM products"
    conditions = []
    params = []
    
    if name:
        name_keywords = name.split()
        for keyword in name_keywords:
            conditions.append("product_name LIKE %s")
            params.append(f"%{keyword}%")
    
    if description:
        description_keywords = description.split()
        for keyword in description_keywords:
            conditions.append("product_description LIKE %s")
            params.append(f"%{keyword}%")
    
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    
    try:
        with connection.cursor() as cursor:
            cursor.execute(query, params)
            rows = cursor.fetchall()
            columns = [col[0] for col in cursor.description]
            products = [dict(zip(columns, row)) for row in rows]
        return JsonResponse(products, safe=False)
    except Exception:
        return JsonResponse({'error': '搜索商品失败'}, status=500)

from django.views.decorators.csrf import csrf_exempt

@csrf_exempt  # 开发阶段可以临时禁用CSRF保护，生产环境请移除

def create_order(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            items = data.get('items', [])
            username = data.get('username', '')
            print(username)

            if not items:
                return JsonResponse({'error': '购物车为空'}, status=400)

            with connection.cursor() as cursor:
                # 获取用户信息
                cursor.execute("""
                    SELECT user_id, address, phone 
                    FROM users 
                    WHERE username = %s
                """, [username])
                user_row = cursor.fetchone()
                if not user_row:
                    return JsonResponse({'error': '用户不存在'}, status=400)
                user_id, address, phone = user_row

                total_amount = 0
                product_updates = []
                order_items = []

                for item in items:
                    product_id = item.get('product_id')
                    quantity = item.get('quantity', 0)
                    if not product_id or quantity <= 0:
                        return JsonResponse({'error': '无效的商品或数量'}, status=400)

                    # 获取商品信息
                    cursor.execute("""
                        SELECT product_name, price, stock 
                        FROM products 
                        WHERE product_id = %s
                        FOR UPDATE
                    """, [product_id])
                    product = cursor.fetchone()
                    if not product:
                        return JsonResponse({'error': f'商品ID {product_id} 不存在'}, status=400)
                    product_name, price, stock = product

                    if stock < quantity:
                        return JsonResponse({'error': f'商品 "{product_name}" 库存不足'}, status=400)

                    total_amount += price * quantity
                    new_stock = stock - quantity
                    product_updates.append((new_stock, product_id))

                    order_items.append((product_id, quantity, price))

                # 创建订单
                cursor.execute("""
                    INSERT INTO orders (user_id, created_at, total_amount, status, shipping_address, shipping_phone)
                    VALUES (%s, NOW(), %s, %s, %s, %s)
                """, [user_id, total_amount, 'pending', address, phone])
                order_id = cursor.lastrowid

                # 创建订单项并更新库存
                for product_id, quantity, unit_price in order_items:
                    cursor.execute("""
                        INSERT INTO order_items (order_id, product_id, quantity, unit_price)
                        VALUES (%s, %s, %s, %s)
                    """, [order_id, product_id, quantity, unit_price])

                for new_stock, product_id in product_updates:
                    cursor.execute("""
                        UPDATE products 
                        SET stock = %s 
                        WHERE product_id = %s
                    """, [new_stock, product_id])

                # 创建物流单
                cursor.execute("""
                    INSERT INTO logistics (order_id, status, carrier, tracking_number, updated_at)
                    VALUES (%s, %s, %s, %s, NOW())
                """, [order_id, 'pending', '', ''])

                # 提交事务
                connection.commit()

                return JsonResponse({'message': '订单创建成功'}, status=201)

        except json.JSONDecodeError:
            return JsonResponse({'error': '无效的JSON数据'}, status=400)
        except Exception as e:
            connection.rollback()
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': '仅支持POST请求'}, status=400)

from django.contrib.auth import logout

def logout_view(request):
    logout(request)
    return redirect('login')




def get_purchases(request):
    try:
        username = request.GET.get('username', '')
        if not username:
            return JsonResponse({'error': '缺少用户名参数'}, status=400)

        with connection.cursor() as cursor:
            # 获取用户ID
            cursor.execute("""
                SELECT user_id
                FROM users
                WHERE username = %s
            """, [username])
            user_row = cursor.fetchone()
            if not user_row:
                return JsonResponse({'error': '用户不存在'}, status=404)
            user_id = user_row[0]

            # 获取用户的订单
            cursor.execute("""
                SELECT order_id, total_amount, status, shipping_address, shipping_phone, created_at
                FROM orders
                WHERE user_id = %s
                ORDER BY created_at DESC
            """, [user_id])
            orders = cursor.fetchall()
            order_columns = [col[0] for col in cursor.description]
            orders_list = []

            for order in orders:
                order_data = dict(zip(order_columns, order))
                order_id = order_data['order_id']

                # 获取订单项
                cursor.execute("""
                    SELECT p.product_name, oi.quantity, oi.unit_price
                    FROM order_items oi
                    JOIN products p ON oi.product_id = p.product_id
                    WHERE oi.order_id = %s
                """, [order_id])
                items = cursor.fetchall()
                item_columns = [col[0] for col in cursor.description]
                items_list = [dict(zip(item_columns, item)) for item in items]

                # 格式化订单数据
                orders_list.append({
                    'order_id': order_data['order_id'],
                    'total_amount': str(order_data['total_amount']),
                    'status': order_data['status'],
                    'shipping_address': order_data['shipping_address'],
                    'shipping_phone': order_data['shipping_phone'],
                    'created_at': order_data['created_at'].strftime('%Y-%m-%d %H:%M:%S'),
                    'items': items_list
                })

        return JsonResponse({'orders': orders_list}, status=200)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)



def get_profile(request):
    try:
        username = request.session.get('username')
        if not username:
            return JsonResponse({'error': '未登录用户'}, status=401)

        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT username, address, phone
                FROM users
                WHERE username = %s
            """, [username])
            user = cursor.fetchone()
            if not user:
                return JsonResponse({'error': '用户不存在'}, status=404)
            
            user_data = {
                'username': user[0],
                'address': user[1],
                'phone': user[2],
            }

        return JsonResponse({'user': user_data}, status=200)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)



def update_profile(request):
    if request.method != 'POST':
        return JsonResponse({'error': '仅支持POST请求'}, status=405)
    
    try:
        data = json.loads(request.body)
        username = data.get('username')
        address = data.get('address')
        phone = data.get('phone')
        
        if not username:
            return JsonResponse({'error': '缺少用户名参数'}, status=400)
        
        with connection.cursor() as cursor:
            # 获取用户信息
            cursor.execute("""
                SELECT password
                FROM users
                WHERE username = %s
            """, [username])
            user_row = cursor.fetchone()
            if not user_row:
                return JsonResponse({'error': '用户不存在'}, status=404)
            stored_password = user_row[0]
            
            # 准备要更新的字段
            fields = []
            params = []
            
            if address:
                fields.append("address = %s")
                params.append(address)
            if phone:
                fields.append("phone = %s")
                params.append(phone)
            
            # 处理密码修改
            current_password = data.get('current_password')
            new_password = data.get('new_password')
            confirm_password = data.get('confirm_password')
            
            if new_password or confirm_password:
                if not current_password:
                    return JsonResponse({'error': '请提供当前密码以修改密码'}, status=400)
                if current_password!=stored_password:
                    return JsonResponse({'error': '当前密码不正确'}, status=400)
                if new_password != confirm_password:
                    return JsonResponse({'error': '新密码与确认密码不一致'}, status=400)
                hashed_new_password = new_password
                fields.append("password = %s")
                params.append(hashed_new_password)
            
            if not fields:
                return JsonResponse({'error': '没有要更新的字段'}, status=400)
            
            # 添加用户名到参数列表
            params.append(username)
            
            # 执行更新操作
            update_query = f"""
                UPDATE users
                SET {', '.join(fields)}
                WHERE username = %s
            """
            cursor.execute(update_query, params)
            connection.commit()
        
        return JsonResponse({'message': '个人信息已更新'}, status=200)
    
    except json.JSONDecodeError:
        return JsonResponse({'error': '无效的JSON数据'}, status=400)
    except Exception as e:
        connection.rollback()
        return JsonResponse({'error': str(e)}, status=500)

########################前面这些应该有效########################

from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from .models import Order, OrderItem, Review


def get_order_items(request):
    order_id = request.GET.get('order_id')
    user_id = request.session.get('user_id')
    if not user_id:
        return JsonResponse({'error': '未认证用户'}, status=401)
    
    if not order_id:
        return JsonResponse({'error': '缺少订单ID参数'}, status=400)
    
    try:
        with connection.cursor() as cursor:
            # 获取用户信息
            cursor.execute("""
                SELECT username FROM users WHERE user_id = %s
            """, [user_id])
            user_row = cursor.fetchone()
            if not user_row:
                return JsonResponse({'error': '用户不存在'}, status=404)
            
            # 获取订单信息
            cursor.execute("""
                SELECT status FROM orders 
                WHERE order_id = %s AND user_id = %s
            """, [order_id, user_id])
            order_row = cursor.fetchone()
            if not order_row:
                return JsonResponse({'error': '订单不存在'}, status=404)
            status = order_row[0]
            if status != 'delivered':
                return JsonResponse({'error': '订单未送达，无法评价'}, status=400)
            
            # 获取订单项信息
            cursor.execute("""
                SELECT p.product_id, p.product_name, oi.quantity, oi.unit_price
                FROM order_items oi
                JOIN products p ON oi.product_id = p.product_id
                WHERE oi.order_id = %s
            """, [order_id])
            rows = cursor.fetchall()
            columns = [col[0] for col in cursor.description]
            items = [dict(zip(columns, row)) for row in rows]
            for item in items:
                item['product__product_id'] = item['product_id']
                item['product__product_name'] = item['product_name']

            # order_item_list=[]
            # for key, value in items.items():
            #     order_item_list.append(value)
            # items = order_item_list

        print(items)

        return JsonResponse({'items': items}, status=200)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def review_page(request, order_id):
    user_id = request.session.get('user_id')
    if not user_id:
        return JsonResponse({'error': '未认证用户'}, status=401)
    
    try:
        with connection.cursor() as cursor:
            # 获取订单信息，确保订单属于当前用户
            cursor.execute("""
                SELECT status
                FROM orders
                WHERE order_id = %s AND user_id = %s
            """, [order_id, user_id])
            order_row = cursor.fetchone()
            if not order_row:
                return JsonResponse({'error': '订单不存在'}, status=404)
            status = order_row[0]
            if status != 'delivered':
                return JsonResponse({'error': '订单未送达，无法评价'}, status=400)
            
            # 获取订单项信息
            cursor.execute("""
                SELECT oi.order_item_id, p.product_id, p.product_name, oi.quantity, oi.unit_price
                FROM order_items oi
                JOIN products p ON oi.product_id = p.product_id
                WHERE oi.order_id = %s
            """, [order_id])
            rows = cursor.fetchall()
            columns = [col[0] for col in cursor.description]
            order_items = [dict(zip(columns, row)) for row in rows]
        
        return render(request, 'review.html', {'order_id': order_id, 'order_items': order_items})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    

def submit_review(request):
    if request.method != 'POST':
        return JsonResponse({'error': '仅支持POST请求'}, status=405)
    
    try:
        user_id = request.session.get('user_id')
        if not user_id:
            return JsonResponse({'error': '未认证用户'}, status=401)
        
        data = json.loads(request.body)
        order_id = data.get('order_id')
        product_id = data.get('product_id')
        rating = data.get('rating')
        comment = data.get('comment', '')
        
        # 验证必要参数
        if not all([order_id, product_id, rating]):
            return JsonResponse({'error': '缺少必要参数'}, status=400)
        
        try:
            rating = int(rating)
            if not (1 <= rating <= 5):
                return JsonResponse({'error': '评分必须在1到5之间'}, status=400)
        except ValueError:
            return JsonResponse({'error': '评分必须是整数'}, status=400)
        
        with connection.cursor() as cursor:
            # 检查订单是否存在且属于当前用户，并且状态为已送达
            cursor.execute("""
                SELECT status 
                FROM orders 
                WHERE order_id = %s AND user_id = %s
            """, [order_id, user_id])
            order_row = cursor.fetchone()
            if not order_row:
                return JsonResponse({'error': '订单不存在或不属于当前用户'}, status=404)
            status = order_row[0]
            if status != 'delivered':
                return JsonResponse({'error': '订单未送达，无法评价'}, status=400)
            
            # 检查订单中是否包含该商品
            cursor.execute("""
                SELECT 1 
                FROM order_items 
                WHERE order_id = %s AND product_id = %s
            """, [order_id, product_id])
            order_item_exists = cursor.fetchone()
            if not order_item_exists:
                return JsonResponse({'error': '该订单中不存在该商品'}, status=404)
            
            # 检查用户是否已经评价过该商品
            cursor.execute("""
                SELECT 1 
                FROM reviews 
                WHERE user_id = %s AND product_id = %s
            """, [user_id, product_id])
            review_exists = cursor.fetchone()
            if review_exists:
                return JsonResponse({'error': '你已评价过该商品'}, status=400)
            
            # 插入评价
            cursor.execute("""
                INSERT INTO reviews (user_id, product_id, rating, comment, created_at)
                VALUES (%s, %s, %s, %s, NOW())
            """, [user_id, product_id, rating, comment])
            
            # 提交事务
            connection.commit()
        
        return JsonResponse({'message': '评价成功'}, status=201)
    
    except json.JSONDecodeError:
        return JsonResponse({'error': '无效的JSON数据'}, status=400)
    except Exception as e:
        connection.rollback()
        return JsonResponse({'error': str(e)}, status=500)
    


def get_reviews(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return JsonResponse({'error': '未认证用户'}, status=401)
    
    try:
        with connection.cursor() as cursor:
            # 检查用户是否存在
            cursor.execute("""
                SELECT username
                FROM users
                WHERE user_id = %s
            """, [user_id])
            user = cursor.fetchone()
            if not user:
                return JsonResponse({'error': '用户不存在'}, status=404)
            
            # 获取用户的评价
            cursor.execute("""
                SELECT p.product_name, r.rating, r.comment, r.created_at
                FROM reviews r
                JOIN products p ON r.product_id = p.product_id
                WHERE r.user_id = %s
                ORDER BY r.created_at DESC
            """, [user_id])
            reviews = cursor.fetchall()
            columns = [col[0] for col in cursor.description]
            reviews_data = [
                {
                    'product_name': review[0],
                    'rating': review[1],
                    'comment': review[2],
                    'created_at': review[3].strftime('%Y-%m-%d %H:%M:%S'),
                }
                for review in reviews
            ]
        
        return JsonResponse({'reviews': reviews_data}, status=200)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    

