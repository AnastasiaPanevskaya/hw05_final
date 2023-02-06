# Yatube - Это социальная сеть и сеть микроблогов, в которой пользователи публикуют сообщения. Личные дневники и сообщества.

Как запустить проект:

## Клонируем репозиторий:
git clone git@github.com:AnastasiaPanevskaya/hw05_final.git

## Заходим в директорию проекта:
cd hw05_final

## Создать и запуспустить виртуальное окружение:
python -m venv venv
source venv/Scripts/activate

## Установить зависимости:
pip install -r requirements.txt

## Выполните миграции:
python manage.py migrate

## Запустить сервер:

python manage.py runserver

## Адрес главной страницы сообщества:
http://127.0.0.1:8000/


