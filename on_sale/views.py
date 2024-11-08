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

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        
        try:
            user = User.objects.get(username=username)
            if user.password == password:
                # 使用会话存储用户信息
                request.session['user_id'] = user.user_id
                request.session['username'] = user.username
                messages.success(request, '登录成功')
                return redirect('on_sale')
            else:
                messages.error(request, '密码错误')
        except User.DoesNotExist:
            messages.error(request, '用户不存在')
    
    return render(request, 'login.html')



def register_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        address = request.POST['address']
        phone = request.POST['phone']
        
        try:
            # 检查用户名是否已存在
            if User.objects.filter(username=username).exists():
                messages.error(request, '用户名已存在')
                return render(request, 'register.html')
            
            # 创建新用户
            user = User(
                username=username,
                password=password,
                address=address,
                phone=phone
            )
            user.save()
            messages.success(request, '注册成功')
            return redirect('login')
        except Exception as e:
            messages.error(request, f'注册失败：{str(e)}')
            
    return render(request, 'register.html')

# views.py
from django.http import JsonResponse
from .models import Product

def get_products(request):
    products = Product.objects.all().values('product_id', 'product_name', 'product_description', 'price','stock')  # 假设有image字段
    return JsonResponse(list(products), safe=False)


# views.py
def search_products(request):
    name = request.GET.get('name', '')
    description = request.GET.get('description', '')
    
    query = Q()
    
    if name:
        name_keywords = name.split()
        for keyword in name_keywords:
            query &= Q(product_name__icontains=keyword)
    
    if description:
        description_keywords = description.split()
        for keyword in description_keywords:
            query &= Q(product_description__icontains=keyword)
    
    products = Product.objects.filter(query)
    
    return JsonResponse(list(products.values()), safe=False)

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
            
            user=User.objects.get(username=username)

            # 计算订单总金额
            total_amount = 0
            for item in items:
                product = Product.objects.get(product_id=item['product_id'])
                if product.stock >= item['quantity']:
                    total_amount += product.price * item['quantity']
                else:
                    # 库存不足，返回错误信息
                    #return JsonResponse({'status': 'fail', 'message': f'商品 "{product.product_name}" 库存不足，无法下单'})
                    return JsonResponse({'error': '库存不足'}, status=400)


            # 创建订单
            order = Order.objects.create(
                user=user,
                total_amount=total_amount,
                status='pending',
                shipping_address=user.address,
                shipping_phone=user.phone
            )

            # 创建订单项
            for item in items:
                product = Product.objects.get(product_id=item['product_id'])
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=item['quantity'],
                    unit_price=product.price
                )
                # 减少库存
                product.stock -= item['quantity']
                product.save()
                        # 创建物流单
            Logistics.objects.create(
                order=order,
                status='pending',  # 初始状态为待发货
                carrier='',        # 承运人信息可为空，后续由商家更新
                tracking_number='', # 追踪号码可为空，后续由商家更新
            )

            return JsonResponse({'message': '订单创建成功'}, status=201)
        
        except Product.DoesNotExist:
            return JsonResponse({'error': '商品不存在'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': '仅支持POST请求'}, status=400)

from django.contrib.auth import logout

def logout_view(request):
    logout(request)
    return redirect('login')




def get_purchases(request):
    print("get_purchases")
    try:
        
        print(request.GET)
        username = request.GET.get('username')  # 从GET参数获取用户名
        if not username:
            return JsonResponse({'error': '缺少用户名参数'}, status=400)
        print(f"获取用户名: {username}")

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return JsonResponse({'error': '用户不存在'}, status=404)

        orders = Order.objects.filter(user=user).order_by('-created_at')
        print("获取到订单")
        orders_list = []
        for order in orders:
            items = OrderItem.objects.filter(order=order).values('product__product_name', 'quantity', 'unit_price')
            orders_list.append({
                'order_id': order.order_id,
                'total_amount': str(order.total_amount),
                'status': order.status,
                'shipping_address': order.shipping_address,
                'shipping_phone': order.shipping_phone,
                'created_at': order.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'items': list(items)
            })

        return JsonResponse({'orders': orders_list}, status=200)
    except Exception as e:
        print(f"获取购买记录时出错: {e}")
        return JsonResponse({'error': str(e)}, status=500)
    


def get_profile(request):
    print("get_profile")
    try:
        username = request.session.get('username')  # 从会话中获取用户名
        if not username:
            return JsonResponse({'error': '未登录用户'}, status=401)
        print(f"获取用户名: {username}")

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return JsonResponse({'error': '用户不存在'}, status=404)

        user_data = {
            'username': user.username,
           
            'address': user.address,
            'phone': user.phone,
        }

        print(f"获取到用户信息: {user_data}")

        return JsonResponse({'user': user_data}, status=200)
    except Exception as e:
        print(f"获取个人信息时出错: {e}")
        return JsonResponse({'error': str(e)}, status=500)


def update_profile(request):
    print("update_profile")
    if request.method != 'POST':
        return JsonResponse({'error': '仅支持POST请求'}, status=405)
    
    try:
        data = json.loads(request.body)
        username = data.get('username')
        address = data.get('address')
        phone = data.get('phone')

        if not username:
            return JsonResponse({'error': '缺少用户名参数'}, status=400)

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return JsonResponse({'error': '用户不存在'}, status=404)

        if address:
            user.address = address
        if phone:
            user.phone = phone

        # 处理密码修改
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        confirm_password = data.get('confirm_password')

        if new_password or confirm_password:
            if not current_password:
                return JsonResponse({'error': '请提供当前密码以修改密码'}, status=400)
            if not user.password == current_password:
                return JsonResponse({'error': '当前密码不正确'}, status=400)
            if new_password != confirm_password:
                return JsonResponse({'error': '新密码与确认密码不一致'}, status=400)
            user.password = new_password  # 注意：建议使用哈希存储密码

        user.save()
        return JsonResponse({'message': '个人信息已更新'}, status=200)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    


from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from .models import Order, OrderItem, Review


def get_order_items(request):
    order_id = request.GET.get('order_id')
    user_id = request.session.get('user_id')
    if not user_id:
        return JsonResponse({'error': '未认证用户'}, status=401)
    
    try:
        user = User.objects.get(user_id=user_id)
        order = Order.objects.get(order_id=order_id, user=user)
        if order.status != 'delivered':
            return JsonResponse({'error': '订单未送达，无法评价'}, status=400)
        
        items = OrderItem.objects.filter(order=order).values('product__product_id', 'product__product_name', 'quantity', 'unit_price')
        return JsonResponse({'items': list(items)}, status=200)
    except Order.DoesNotExist:
        return JsonResponse({'error': '订单不存在'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)



def review_page(request, order_id):
    try:
        order = Order.objects.get(order_id=order_id, user=request.user)
        if order.status != 'delivered':
            return JsonResponse({'error': '订单未送达，无法评价'}, status=400)
        order_items = OrderItem.objects.filter(order=order)
        return render(request, 'review.html', {'order_id': order_id, 'order_items': order_items})
    except Order.DoesNotExist:
        return JsonResponse({'error': '订单不存在'}, status=404)
    

def submit_review(request):
    if request.method != 'POST':
        return JsonResponse({'error': '仅支持POST请求'}, status=405)
    
    try:
        user_id = request.session.get('user_id')
        if not user_id:
            return JsonResponse({'error': '未认证用户'}, status=401)
        
        user = User.objects.get(user_id=user_id)
        
        data = json.loads(request.body)
        order_id = data.get('order_id')
        product_id = data.get('product_id')
        rating = data.get('rating')
        comment = data.get('comment', '')
        
        # 验证必要参数
        if not all([order_id, product_id, rating]):
            return JsonResponse({'error': '缺少必要参数'}, status=400)
        
        # 验证评分范围
        if not (1 <= int(rating) <= 5):
            return JsonResponse({'error': '评分必须在1到5之间'}, status=400)
        
        # 验证订单是否存在且属于当前用户
        try:
            order = Order.objects.get(order_id=order_id, user=user)
        except Order.DoesNotExist:
            return JsonResponse({'error': '订单不存在或不属于当前用户'}, status=404)
        
        # 验证订单状态是否已送达
        if order.status != 'delivered':
            return JsonResponse({'error': '订单未送达，无法评价'}, status=400)
        
        # 验证该订单中是否包含该商品
        try:
            order_item = OrderItem.objects.get(order=order, product_id=product_id)
        except OrderItem.DoesNotExist:
            return JsonResponse({'error': '该订单中不存在该商品'}, status=404)
        
        # 检查用户是否已经评价过该商品
        if Review.objects.filter(user=user, product_id=product_id).exists():
            return JsonResponse({'error': '你已评价过该商品'}, status=400)
        
        # 创建评价
        Review.objects.create(
            user=user,
            product_id=product_id,
            rating=rating,
            comment=comment
        )
        
        return JsonResponse({'message': '评价成功'}, status=201)
    
    except json.JSONDecodeError:
        return JsonResponse({'error': '无效的JSON数据'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    
def get_reviews(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return JsonResponse({'error': '未认证用户'}, status=401)
    
    try:
        user = User.objects.get(user_id=user_id)
        reviews = Review.objects.filter(user=user).select_related('product').order_by('-created_at')
        reviews_data = [
            {
                'product_name': review.product.product_name,
                'rating': review.rating,
                'comment': review.comment,
                'created_at': review.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            }
            for review in reviews
        ]
        return JsonResponse({'reviews': reviews_data}, status=200)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    

