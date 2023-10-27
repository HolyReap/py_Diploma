from django.conf import settings
from django.dispatch import receiver, Signal
from backend.models import ConfirmEmailToken, User
from django_rest_passwordreset.signals import reset_password_token_created
from django.core.mail import send_mail


def new_user_registered_mail(user):
    """Отправка письма с подтверждением регистрации"""

    token, _ = ConfirmEmailToken.objects.get_or_create(user=user)

    send_mail(
        subject="Подтверждение регистрации пользователя",
        message=f"Ключ для подтверждения регистрации - {token.key}",
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[user.email],
        fail_silently=False,
    )


def new_order_created_mail(user):
    """Отправка письма с подтверждением заказа"""

    send_mail(
        subject="Спасибо за заказ",
        message="С вами свяжется специалист. Детали заказа Вы можете посмотреть в личном кабинете магазина",
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[user.email],
        fail_silently=False,
    )
    
def new_order_notify(user, order, sum):
    """Отправка письма о заказе админу"""

    send_mail(
        subject="Пользователь разместил заказ",
        message=f"Пользователь {user.email} разместил заказ ID = {order.id} на сумму {sum} руб. c доставкой по адресу {order.contact}",
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[settings.EMAIL_HOST_USER],
        fail_silently=False,
    )