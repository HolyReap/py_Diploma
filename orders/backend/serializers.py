from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.db.models import Q
from rest_framework import serializers

from backend.models import User, ConfirmEmailToken, Contact, Shop, Category, Product, ProductInfo,\
    ProductParameter, Order, OrderItem

class NewAccountSerializer(serializers.ModelSerializer):
    password_confirmation = serializers.CharField(write_only=True, required=True)
    type = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = (
            "id", "first_name", "last_name", "email", "company", "position",
            "password", "password_confirmation", "type",
        )
        read_only_fields = ("id",)

    def validate(self, data):
        """
        Проверка пароля.
        """
        password = data["password"]
        password_confirmation = data.pop("password_confirmation")
        try:
            if password != password_confirmation:
                raise ValueError(
                    "Введенные пароли не совпадают."
                )
            validate_password(password)
        except Exception as error:
            raise serializers.ValidationError({"status": "Failure", "error": error})
        return data

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user
    
    
class AccountConfirmationSerializer(serializers.Serializer):
    email = serializers.CharField(required=True)
    token = serializers.CharField(max_length=64, write_only=True, required=True)

    def validate(self, data):
        email_request = data["email"]
        token_request = data["token"]
        
        token = ConfirmEmailToken.objects.filter(user__email=email_request, key=token_request).first()
        if token is None:
            raise serializers.ValidationError(
                {
                    "status": "Failure",
                    "error": "Неправильно указан токен или email",
                }
            )
        return token
    
    
class AccountLoginSerializer(serializers.Serializer):
    email = serializers.CharField(required=True)
    password = serializers.CharField(max_length=64, write_only=True, required=True)

    def validate(self, data):
        password = data["password"]
        email = data["email"]
        user = authenticate(username=email, password=password)
        if user is None or not user.is_active:
            raise serializers.ValidationError(
                {"status": "Failure", "error": "Ошибка в имени пользователя или пароле"}
            )
        return user


class AccountContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = ('id', 'city', 'street', 'house', 'structure', 'building', 'floor', 'apartment', 'user', 'phone')
        read_only_fields = ('id',)
        extra_kwargs = {
            'user': {'write_only': True}
        }
    
    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().update(instance, validated_data)
    
    
class AccountSerializer(serializers.ModelSerializer):
    contacts = AccountContactSerializer(read_only=True, many=True)
    class Meta:
        model = User
        fields = ("id", "first_name", "last_name", "email", "company",
                  "position", "type","contacts",)
        read_only_fields = ("id",)
        

class PartnerUpdateSerializer(serializers.Serializer):
    url = serializers.URLField(write_only=True, required=True)
    

class PartnerStateSerialiser(serializers.ModelSerializer):
    name = serializers.CharField(max_length=50, required=False)
    url = serializers.URLField(required=False)
    filename = serializers.CharField(max_length=50, required=False)
    state = serializers.BooleanField(default=True)
    
    class Meta:
        model = Shop
        fields = ("id", "name", "url", "filename", "state",)
        read_only_fields = ("id",)
        
        
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'name',)
        read_only_fields = ('id',)


class ShopSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shop
        fields = ('id', 'name', 'state',)
        read_only_fields = ('id',)

class ProductSerializer(serializers.ModelSerializer):
    category = serializers.StringRelatedField()

    class Meta:
        model = Product
        fields = ('name', 'category',)


class ProductParameterSerializer(serializers.ModelSerializer):
    parameter = serializers.StringRelatedField()

    class Meta:
        model = ProductParameter
        fields = ('parameter', 'value',)
        
        
class ProductInfoSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_parameters = ProductParameterSerializer(read_only=True, many=True)

    class Meta:
        model = ProductInfo
        fields = ('id', 'model', 'product', 'shop', 'quantity', 'price', 'price_rrc', 'product_parameters',)
        read_only_fields = ('id',)


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ('id', 'product_info', 'quantity', 'order',)
        read_only_fields = ('id',)
        extra_kwargs = {
            'order': {'write_only': True}
        }


class OrderSerializer(serializers.ModelSerializer):
    ordered_items = OrderItemSerializer(read_only=True, many=True)
    items = OrderItemSerializer(write_only=True, many=True)
    total_sum = serializers.IntegerField(read_only=True)
    contact = AccountContactSerializer(read_only=True)
    state = serializers.CharField(required=False)

    class Meta:
        model = Order
        fields = ('id', 'ordered_items', 'state', 'dt', 'total_sum', 'contact', 'items')
        read_only_fields = ('id',)
        
    def validate(self, data):
        items = data["items"]
        for item in items:
            product_info = item.get("product_info")
            quantity = item.get("quantity")

            product = ProductInfo.objects.filter(id=product_info.id).first()
            if not product:
                raise serializers.ValidationError(
                    {"status": "Failure", "error": "Нет такого продукта"}
                )
            if quantity > product.quantity:
                raise serializers.ValidationError(
                    {"status": "Failure",
                     "error": "В наличии не достаточно продуктов для добавления в корзину"}
                )
            if quantity <= 0:
                raise serializers.ValidationError(
                    {"status": "Failure", "error": "Нет продукта в наличии"}
                )
        return data
    
    def create(self, validated_data):
        user = self.context["request"].user
        items = validated_data.pop("items")

        order, _ = Order.objects.get_or_create(**validated_data, user_id=user.id, state="basket")
        for item in items:
            product_id = item.get("product_info")
            quantity = item.get("quantity", 1)
            OrderItem.objects.update_or_create(
                order=order, product_info=product_id, defaults={"quantity": quantity}
            )
        return order   
    
    def update(self, instance, validated_data):
        instance.ordered_items.all().delete()
        instance = super().create(**validated_data)
        return instance
    
    
class OrderConfirmationSerializer(serializers.Serializer):
    id = serializers.IntegerField(write_only=True)
    contact = serializers.IntegerField(write_only=True)

    class Meta:
        model = Order
        fields = ("id", "contact")

    def validate(self, data):
        order_id = data.get("id")
        contact_id = data.get("contact")
        user = self.context["request"].user
        contact = Contact.objects.filter(Q(user_id=user.id) & Q(id=contact_id)).first()
        order = Order.objects.filter(Q(id=order_id) & Q(user_id=user.id)).first()
        state = order.state

        if not state == 'basket':
            raise serializers.ValidationError(
                {
                    "status": "Failure",
                    "error": "Не корректный статус заказа",
                }
            )
        if not contact:
            raise serializers.ValidationError(
                {
                    "status": "Failure",
                    "error": "Указан не корректный контакт",
                }
            )
        if not order:
            raise serializers.ValidationError(
                {"status": "Failure", "error": "Указан не корректный заказ"}
            )
        return order