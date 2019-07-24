import hashlib

from django.shortcuts import render
from django.core.paginator import Paginator
from django.http import HttpResponseRedirect

from Store.models import *


# Create your views here.
# 装饰器
def loginValid(fun):
    def inner(request, *args, **kwargs):
        c_user = request.COOKIES.get("username")
        s_user = request.session.get("username")
        if c_user and s_user and c_user == s_user:
            user = Seller.objects.filter(username=c_user).first()
            if user:
                return fun(request, *args, **kwargs)
        return HttpResponseRedirect("/Store/login/")

    return inner

# 加密密码
def set_password(password):
    md5 = hashlib.md5()
    md5.update(password.encode())
    resule = md5.hexdigest()
    return resule

#注册用户
def register(request):
    """
    register注册
    返回注册页面
    进行注册数据保存
    """
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        if username and password:
            seller = Seller()
            seller.username = username
            seller.password = set_password(password)
            seller.nicknaem = username
            seller.save()
            return HttpResponseRedirect("/Store/login/")
    return render(request, "Store/register.html")

#登陆
def login(request):
    """
    登陆功能，如果登陆成功，跳转首页
    如果失败，跳转到登陆页
    """
    response = render(request, "store/login.html")
    response.set_cookie("login_from", "login_page")  # 记录cookie从哪里来的
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        if username and password:
            user = Seller.objects.filter(username=username).first()
            if user:
                web_password = set_password(password)
                cookies = request.COOKIES.get("login_from")
                if user.password == web_password and cookies == "login_page":
                    response = HttpResponseRedirect("/Store/index/")
                    response.set_cookie("username", username)
                    response.set_cookie("user_id", user.id)
                    request.session["username"] = username
                    return response
    return response
    # return render(request,'Store/login.html')


@loginValid
def index(request):
    """首页   添加检查账号是否有店铺的逻辑"""
    # 查询当前用户是谁
    user_id = request.COOKIES.get("user_id")
    if user_id:
        user_id = int(user_id)
    else:
        user_id = 0
    # 通过用户查询店铺是否存在（店铺和用户通过用户的id进行关联）
    store = Store.objects.filter(user_id=user_id).first()
    if store:
        is_store = 1
    else:
        is_store = 0
    return render(request, 'Store/index.html', {"is_store": is_store})


# 店铺页面的前端页
def register_store(request):
    type_list = StoreType.objects.all()
    if request.method == "POST":
        post_data = request.POST  # 接收post数据
        store_name = post_data.get("store_name")
        store_address = post_data.get("store_address")
        store_description = post_data.get("store_description")
        store_phone = post_data.get("store_phone")
        store_money = post_data.get("store_money")
        user_id = int(request.COOKIES.get("user_id"))  # 通过cookie来得到user_id
        type_list = post_data.get("type")  # 通过request.POST得到类型，但是是一个列表

        store_logo = request.FILES.get("store_logo")

        # 保存非多对多数据
        store = Store()
        store.store_name = store_name
        store.store_description = store_description
        store.store_address = store_address
        store.store_phone = store_phone
        store.store_money = store_money
        store.user_id = user_id
        store.store_logo = store_logo  # django1.8之后可以直接保存
        store.save()  # 保存，生成了数据库中的一条数据
        # 在生成的数据中添加多对多字段
        for i in type_list:  # 循环type列表，得到类型
            store_type = StoreType.objects.get(id=i)  # 查询类型数据
            store.type.add(store_type)  # 添加到类型的字段，多对多的映射表
        store.save()  # 保存数据

    return render(request, "store/register_store.html", locals())

# 添加商品
def add_goods(requset):
    """"
    负责添加商品
    """
    if requset.method == "POST":
        #获取post请求
        goods_name = requset.POST.get("goods_name")
        goods_price = requset.POST.get("goods_price")
        goods_number = requset.POST.get("goods_number")
        goods_description = requset.POST.get("goods_description")
        goods_date = requset.POST.get("goods_date")
        goods_safeDate = requset.POST.get("goods_safeDate")
        goods_store = requset.POST.get("goods_store")
        goods_image = requset.FILES.get("goods_image")

        # 开始保存数据
        goods = Goods()
        goods.goods_name = goods_name
        goods.goods_price = goods_price
        goods.goods_number = goods_number
        goods.goods_description = goods_description
        goods.goods_date = goods_date
        goods.goods_safeDate = goods_safeDate
        goods.goods_image = goods_image
        goods.save()
        #保存多对多数据
        goods.store_id.add(
            Store.objects.get(id = int(goods_store))
        )
        goods.save()
        return

    return render(requset,"store/add_goods.html")

#base页面
def base(request):
    return render(request, "store/base.html")

#分页

# 商品列表页
def list_goods(request):
    """
    商品的列表页
    :param request:
    :return:
    """
    #获取两个关键字
    keywords = request.GET.get("keywords","") #查询关键词
    page_num = request.GET.get("page_num",1) #页码
    if keywords: #判断关键词是否存在
        goods_list = Goods.objects.filter(goods_name__contains=keywords)#完成了模糊查询
    else: #如果关键词不存在，查询所有
        goods_list = Goods.objects.all()
    #分页，每页3条
    paginator = Paginator(goods_list,3)
    page = paginator.page(int(page_num))
    page_range = paginator.page_range
    #返回分页数据
    return render(request,"store/goods_list.html",{"page":page,"page_range":page_range,"keywords":keywords})

#商品详情页
def goods(request,goods_id):
    goods_data = Goods.objects.filter(id = goods_id).first()
    return render(request,"store/goods.html",locals())

def update_goods(request,goods_id):
    goods_data = Goods.objects.filter(id=goods_id).first()
    if request.method == "POST":
        #获取post请求
        goods_name = request.POST.get("goods_name")
        goods_price = request.POST.get("goods_price")
        goods_number = request.POST.get("goods_number")
        goods_description = request.POST.get("goods_description")
        goods_date = request.POST.get("goods_date")
        goods_safeDate = request.POST.get("goods_safeDate")
        goods_image = request.FILES.get("goods_image")
        #开始修改数据
        goods = Goods.objects.get(id = int(goods_id))   #获取当前商品
        goods.goods_name = goods_name
        goods.goods_price = goods_price
        goods.goods_number = goods_number
        goods.goods_description = goods_description
        goods.goods_date = goods_date
        goods.goods_safeDate = goods_safeDate
        if goods_image:         #如果有上传图片再发起修改
            goods.goods_image = goods_image
        goods.save()
        return HttpResponseRedirect("/Store/goods/%s/"%goods_id)
        #保存多对多数据
    return render(request,"Store/update_goods.html")

# def CookieTest(request):
# #     #查询拥有指定商品所有商铺
# #     goods = Goods.objects.get(id=1)
# #     store_list = goods.store_id.all()
# #     store_list = goods.store_id.filter()
# #     store_list = goods.store_id.get()
# #     #查询指定店铺拥有的所有商品
# #     store = Store.objects.get(id= 17)
# #     #good是多对多表的名称的小写 set 是固定写法
# #     store.goods_set.get()
# #     store.goods_set.filter()
# #     store.goods_set.all()
# #
# #     response = render(request,"store/Test.html",locals())
# #     response.set_cookie("valid",'')
# #     return response