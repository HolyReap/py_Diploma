
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Sum, F

from rest_framework import status
from requests import get
from rest_framework.authtoken.models import Token
from rest_framework.generics import ListAPIView, RetrieveUpdateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from yaml import load as load_yaml, Loader
import yaml

from backend.models import User, Shop, Category, Product, ProductInfo, Parameter, ProductParameter,\
    ConfirmEmailToken, Contact, Order, OrderItem

from backend.serializers import NewAccountSerializer, AccountConfirmationSerializer, \
    AccountLoginSerializer, AccountContactSerializer, AccountSerializer, PartnerUpdateSerializer, \
    PartnerStateSerialiser, CategorySerializer, ShopSerializer, ProductInfoSerializer, \
    OrderSerializer, OrderConfirmationSerializer
from backend.filters import ProductFilter
from backend.permissions import UserIsOwner, UserIsShop
from backend.signals import new_user_registered_mail, new_order_created_mail, new_order_notify


class RegisterAccountView(APIView):
    """
    POST для создания пользователя. 
    """
    queryset = User.objects.all()
    serializer_class = NewAccountSerializer

    def post(self, request, *args, **kwargs):
        serializer = NewAccountSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            new_user_registered_mail(user)
            token, _ = ConfirmEmailToken.objects.get_or_create(user_id=user.id)
            response = {
                "status": "Success",
                "message": "Учетная запись создана. На Вашу почту отправлено письмо с токеном.",
                "token": {token.key},
            }
            return Response(response, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ConfirmAccountView(APIView):
    """
    Класс для подтверждения почтового адреса
    """
    serializer_class = AccountConfirmationSerializer
    # Регистрация методом POST
    def post(self, request, *args, **kwargs):
        serializer = AccountConfirmationSerializer(data=request.data)
        # проверяем обязательные аргументы
        if serializer.is_valid():
            token = serializer.validated_data
            token.user.is_active = True
            token.user.save()
            token.delete()
            response = {
                "status": "Success", 
                "message": "Учетная запись успешно подтверждена",
                }
            return Response(response, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginAccountView(APIView):
    """
    Класс для авторизации пользователей
    """
    serializer_class = AccountLoginSerializer

    def post(self, request):
        serializer = AccountLoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data
            token, _ = Token.objects.get_or_create(user=user)
            return Response(
                {"status": "Success", "token": token.key}, status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_401_UNAUTHORIZED)
    
    
class ContactView(ModelViewSet):
    """
    Класс для работы с контактами покупателей
    """
    queryset = Contact.objects.prefetch_related()
    serializer_class = AccountContactSerializer
    permission_classes = [IsAuthenticated, UserIsOwner]
    
    
class AccountDetails(APIView):
    """
    Класс для работы данными пользователя
    """
    queryset = User.objects.prefetch_related()
    serializer_class = AccountSerializer
    permission_classes = [IsAuthenticated, UserIsOwner]

    def get(self, request):
        user = request.user
        serializer = self.serializer_class(instance=user)
        return Response(serializer.data)

    def patch(self, request):
        serializer = self.serializer_class(
            instance=request.user, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    
class PartnerUpdateURL(APIView):
    permission_classes = [IsAuthenticated, UserIsShop]
    serializer_class = PartnerUpdateSerializer
    """
    Класс для обновления прайса от поставщика по ссылке
    """
    def post(self, request, *args, **kwargs):
        serializer = PartnerUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        url = serializer.validated_data.get("url")
        try:
            stream = get(url).content
            data = load_yaml(stream, Loader=Loader)
        except yaml.YAMLError as exc:
                print(exc)
                return Response(
                        {"status": "Failure", "error": "Ошибка загрузки по ссылке"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                
        shop, _ = Shop.objects.get_or_create(name=data["shop"], user_id=request.user.id)

        for category in data["categories"]:
            category_object, _ = Category.objects.get_or_create(
                id=category["id"], name=category["name"]
            )
            category_object.shops.add(shop.id)
            category_object.save()

        ProductInfo.objects.filter(shop_id=shop.id).delete()

        for item in data["goods"]:
            product, _ = Product.objects.get_or_create(name=item["name"], category_id=item["category"])
            product_info = ProductInfo.objects.create(
                                                      product_id=product.id,external_id=item["id"],
                                                      model=item["model"], price=item["price"],
                                                      price_rrc=item["price_rrc"],
                                                      quantity=item["quantity"], shop_id=shop.id,
                                                      )
            for name, value in item["parameters"].items():
                parameter_object, _ = Parameter.objects.get_or_create(name=name)
                ProductParameter.objects.create(
                                                product_info_id=product_info.id,
                                                parameter_id=parameter_object.id,
                                                value=value,
                                                )
        return Response(
            {"status": "Success", "message": "Данные загружены"},
            status=status.HTTP_200_OK,
        )

class PartnerUpdateFILE(APIView):
    permission_classes = [IsAuthenticated, UserIsShop]
    """
    Класс для обновления прайса от поставщика из файла
    """
    def post(self, request, *args, **kwargs):
        with open("./data/shop.yaml", "r", encoding="utf-8") as stream:
            try:
                data = yaml.safe_load(stream)
            except yaml.YAMLError as exc:
                print(exc)
                return Response(
                        {"status": "Failure", "error": "Ошибка загрузки файла"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

        shop, _ = Shop.objects.get_or_create(name=data["shop"], user_id=request.user.id)

        for category in data["categories"]:
            category_object, _ = Category.objects.get_or_create(
                id=category["id"], name=category["name"]
            )
            category_object.shops.add(shop.id)
            category_object.save()

        ProductInfo.objects.filter(shop_id=shop.id).delete()

        for item in data["goods"]:
            product, _ = Product.objects.get_or_create(name=item["name"], category_id=item["category"])
            product_info = ProductInfo.objects.create(
                                                      product_id=product.id,external_id=item["id"],
                                                      model=item["model"], price=item["price"],
                                                      price_rrc=item["price_rrc"],
                                                      quantity=item["quantity"], shop_id=shop.id,
                                                      )
            for name, value in item["parameters"].items():
                parameter_object, _ = Parameter.objects.get_or_create(name=name)
                ProductParameter.objects.create(
                                                product_info_id=product_info.id,
                                                parameter_id=parameter_object.id,
                                                value=value,
                                                )
        return Response(
            {"status": "Success", "message": "Данные загружены"},
            status=status.HTTP_200_OK,
        )


class PartnerState(RetrieveUpdateAPIView):
    """
    Класс для работы со статусом поставщика
    """
    queryset = Shop.objects.all()
    serializer_class = PartnerStateSerialiser
    permission_classes = [IsAuthenticated, UserIsShop, UserIsOwner]
 
    
class CategoryView(ListAPIView):
    """
    Класс для просмотра категорий
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class ShopView(ListAPIView):
    """
    Класс для просмотра списка магазинов
    """
    queryset = Shop.objects.filter(state=True)
    serializer_class = ShopSerializer
  
    
class ProductInfoView(ListAPIView):
    """
    Класс для поиска товаров
    """
    queryset = (
        ProductInfo.objects.select_related("shop", "product__category")
        .prefetch_related("product_parameters__parameter")
        .distinct()
    )
    
    serializer_class = ProductInfoSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = ProductFilter
    
class ProductInfoViewID(ModelViewSet):
    """
    Класс для поиска товаров
    """
    queryset = (
        ProductInfo.objects.select_related("shop", "product__category")
        .prefetch_related("product_parameters__parameter")
        .distinct()
    )
    
    serializer_class = ProductInfoSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = ProductFilter
    
class BasketView(APIView):
    """
    Класс для работы с корзиной пользователя
    """
    
    permission_classes = [IsAuthenticated]
    queryset = Order.objects.filter(state=True)
    serializer_class = OrderSerializer

    # получить корзину
    def get(self, request, *args, **kwargs):
        basket = (Order.objects.filter(user=self.request.user, state="basket")
                    .prefetch_related("ordered_items")
                    .annotate(total_sum=Sum(F("ordered_items__quantity") * F("ordered_items__product_info__price"))
                             ).first()
                 )
        serializer = OrderSerializer(basket)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # добавить позиции в корзину
    def post(self, request, *args, **kwargs):
        serializer = OrderSerializer(data=request.data, context={"request": request})
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(
                {"status": "Success", "message": "Товар добавлен в корзину"},
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # удалить товары из корзины
    def delete(self, request):
        order = Order.objects.filter(user=request.user, state="basket").first()
        if not order:
            return Response(
                {"status": "Failure", "error": "Корзина уже пуста"},
                status=status.HTTP_404_NOT_FOUND,
            )
        order.delete()
        return Response(
            {"status": "Success", "message": "Товары удалены из корзины"},
            status=status.HTTP_200_OK,
        )

    # редактировать корзину
    def put(self, request, *args, **kwargs):
        serializer = OrderSerializer(data=request.data, context={"request": request})
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(
                {"status": "Success", "message": "Товары в корзине изменены"},
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class OrderView(APIView):
    """
    Класс для получения заказов пользователями
    """
    permission_classes = [IsAuthenticated]
    serializer_class = OrderSerializer
    
    # получить мои заказы
    def get(self, request, *args, **kwargs):
        order = Order.objects.filter(user_id=request.user.id).exclude(state='basket').prefetch_related(
            'ordered_items__product_info__product__category',
            'ordered_items__product_info__product_parameters__parameter').select_related('contact').annotate(
            total_sum=Sum(F('ordered_items__quantity') * F('ordered_items__product_info__price'))).distinct()
        serializer = OrderSerializer(order, many=True)
        return Response(serializer.data)


class OrderViewConfirm(APIView):
    """
    Класс для размешения заказов пользователями
    """
    # разместить заказ из корзины
    permission_classes = [IsAuthenticated]
    serializer_class = OrderConfirmationSerializer
    
    def post(self, request, *args, **kwargs):
        serializer = OrderConfirmationSerializer(data=request.data, context={"request": request})
        if serializer.is_valid(raise_exception=True):
            basket = (Order.objects.filter(user=self.request.user, state="basket")
                    .prefetch_related("ordered_items")
                    .annotate(total_sum=Sum(F("ordered_items__quantity") * F("ordered_items__product_info__price"))
                             ).first()
                 )
            response = OrderSerializer(basket)
            user = request.user
            order = serializer.validated_data
            order.state = "new"
            order.save()
            new_order_created_mail(user)
            new_order_notify(user, order, response.data["total_sum"])
            return Response(
                {"status": "Success", "message": "Спасибо за заказ"},
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    
class PartnerOrders(APIView):
    """
    Класс для получения заказов поставщиками
    """
 
    permission_classes = [IsAuthenticated, UserIsShop]
    serializer_class = OrderSerializer

    def get(self, request, *args, **kwargs):
        order = Order.objects.filter(ordered_items__product_info__shop__user_id=request.user.id
                            ).exclude(state='basket'
                            ).prefetch_related(
                                    'ordered_items__product_info__product__category',
                                    'ordered_items__product_info__product_parameters__parameter'
                            ).select_related('contact'
                            ).annotate(total_sum=Sum(
                                                     F('ordered_items__quantity') * 
                                                     F('ordered_items__product_info__price')
                                                     )
                            ).distinct()
        serializer = OrderSerializer(order, many=True)
        return Response(serializer.data)
