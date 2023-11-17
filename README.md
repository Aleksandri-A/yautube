# Проект Yatube

## _Описание_

Проект представляет собой социальную сеть. Она дает пользователям возможность создать учетную запись, публиковать записи, подписываться на любимых авторов.

## Как запустить проект:

- Клонировать репозиторий и перейти в него в командной строке:

git clone git@github.com:Aleksandri-A/hw05_final.git

- Cоздать и активировать виртуальное окружение:

py -m venv venv

source venv/Scripts/activate

- Установить зависимости из файла requirements.txt:

py -m pip install --upgrade pip

pip install -r requirements.txt

- Выполнить миграции:

py manage.py migrate

- Запустить проект:


py manage.py runserver
