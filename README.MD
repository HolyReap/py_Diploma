# Дипломная работа к профессии Python-разработчик «API Сервис заказа товаров для розничных сетей».
## Версия 26.10.2023

## Описание

Приложение предназначено для автоматизации закупок в розничной сети. Пользователи сервиса — покупатель (менеджер торговой сети, который закупает товары для продажи в магазине) и поставщик товаров.

### Настройки проекта:
         - settings.py (переменные тянутся из .env)
         - Dockerfile
         - docker-compose.yml (переменные БД тянутся из .env)
         - .env (содержит SECRET_KEY, DEBUG, переменные настроек БД и почты)
         - /nginx/orders.conf (настройки nginx)
         - gunicorn.py (параметры gunicorn)

### Для запуска сервера выполнить следующие команды:
         1) cd orders 
         2) docker-compose up -d --build
         3) docker-compose exec orders python manage.py migrate

### Для очистки БД выполнить команду:
         docker-compose exec orders python manage.py flush --no-input

### Для остановки сервера выполнить команду:
         docker-compose down

## Запросы для проверки работоспособности API в файле requests.http
### **запросы по порядку отработки сценария**
         - создание пользователя (на почту, указанную при регистрации отправляется токен для подтверждения)
         - подтверждение (принимает логин-почту и токен для подтверждения)
         - авторизация (принимает логин и пароль, возвращает токен для авторизации)
         - создание и редактирование контакта (требует авторизации пользователя - токен)
         - редактирование пользователя (требует авторизации пользователя - токен)
         - загрузка прайса (требует авторизации пользователя - только для пользователя - магазина)
         - просмотр товаров, магазинов, категорий (не требует авторизации пользователя)
         - формирование и редактирование корзины (требует авторизации пользователя)
         - подтверждение заказа с указанием адреса (требует авторизации пользователя)
         - просмотр заказов продавцом (требует авторизации пользователя - магазина)
### в запросах часть данных (токены и id) прокинуты через переменные (для тестирования - редактировать в файле)

**Клиент (покупатель):**

- Менеджер закупок через API делает ежедневные закупки по каталогу, в котором
  представлены товары от нескольких поставщиков.
- В одном заказе можно указать товары от разных поставщиков — это
  повлияет на стоимость доставки.
- Пользователь может авторизироваться, регистрироваться и восстанавливать пароль через API.
    
**Поставщик:**

- Через API информирует сервис об обновлении прайса.
- Может включать и отключать прием заказов.
- Может получать список оформленных заказов (с товарами из его прайса).


### Задача

Необходимо разработать backend-часть (Django) сервиса заказа товаров для розничных сетей.

**Базовая часть:**
* Разработка сервиса под готовую спецификацию (API); (API готов)
* Возможность добавления настраиваемых полей (характеристик) товаров; (реализовано через загрузку прайса)
* Импорт товаров; (реализовано через загрузку прайса)
* Отправка накладной на email администратора (для исполнения заказа); (отправляется письмо с ID заказа, суммой и адресом доставки - signals.new_order_notify)
* Отправка заказа на email клиента (подтверждение приема заказа). (отправляется информационное письмо)

**Продвинутая часть:**
* Экспорт товаров;
* Админка заказов (проставление статуса заказа и уведомление клиента);
* Выделение медленных методов в отдельные процессы (email, импорт, экспорт).

## Этапы разработки

Разработку Backend рекомендуется разделить на следующие этапы:


### Этап 1. Создание и настройка проекта

Критерии достижения:

1. Вы имеете актуальный код данного репозитория на рабочем компьютере; - готово
2. У вас создан django-проект и он запускается без ошибок. - готово
      #### для запуска сервера выполнить команды:
         1) docker-compose up -d --build
         2) docker-compose exec orders python manage.py flush --no-input (только если нужно запустить с чистой базой)
         3) docker-compose exec orders python manage.py migrate

### Этап 2. Проработка моделей данных

Критерии достижения:

1. Созданы модели и их дополнительные методы. - готово


### Этап 3. Реализация импорта товаров

Критерии достижения:

1. Созданы функции загрузки товаров из приложенных файлов в модели Django.
         POST partner/update/url для загрузки по ссылке (работает корректно)
         POST partner/update/file для загрузки из файла (работает корректно)
2. Загружены товары из всех файлов для импорта. - корректно загружаются из файла и по ссылке


### Этап 4. Реализация forms и views

Критерии достижения:

1. Реализованы API Views для основных страниц:
   - Вход - готово - авторизация пользователя
   - Регистрация - готово регистрация + подтверждение через почту
   - Список товаров - готово
   - Карточка товара - готово
   - Корзина - готово
   - Подтверждение заказа - готово
   - Спасибо за заказ - Успешное выполнение POST /order выдает этот результат
   - Заказы - готово
   - Заказ - готово

### Этап 5. Полностью готовый backend

Критерии достижения:

1. Полностью работающие API Endpoint
2. Корректно отрабатывает следующий сценарий:
   - пользователь может авторизироваться; - готово
   - есть возможность отправки данных для регистрации и получения email с подтверждением регистрации; - email-ы корретно отправляются
   - пользователь может добавлять в корзину товары от разных магазинов; - готово. нет ограничения по магазину
   - пользователь может подтверждать заказ с вводом адреса доставки; - готово
   - пользователь получает email с подтверждением после ввода адреса доставки; - готово
   - Пользователь может переходить на страницу "Заказы" и открывать созданный заказ. - готово


## Продвинутая часть 

### Этап 6. Реализация API views админки склада

Критерии достижения:

1. Реализованы API views для [страниц админки]


### Этап 7. Вынос медленных методов в задачи Celery

Критерии достижения:

1. Создано Celery-приложение c методами:
   - send_email
   - do_import
2. Создан view для запуска Celery-задачи do_import из админки.



### Этап 8. Создание docker-файла для приложения 
1. Создать docker-файл для сборки приложения. - готово
2. Предоставить инструкцию для сборки docker-образа. - готово
3. Создать docker-compose файл для развертывания приложения локально (с БД и необходимыми сервисами) - готово