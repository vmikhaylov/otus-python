#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Нужно реализовать простое HTTP API сервиса скоринга. Шаблон уже есть в api.py, тесты в test.py.
# API необычно тем, что польщователи дергают методы POST запросами. Чтобы получить результат
# пользователь отправляет в POST запросе валидный JSON определенного формата на локейшн /method

# Структура json-запроса:

# {"account": "<имя компании партнера>", "login": "<имя пользователя>", "method": "<имя метода>",
#  "token": "<аутентификационный токен>", "arguments": {<словарь с аргументами вызываемого метода>}}

# account - строка, опционально, может быть пустым
# login - строка, обязательно, может быть пустым
# method - строка, обязательно, может быть пустым
# token - строка, обязательно, может быть пустым
# arguments - словарь (объект в терминах json), обязательно, может быть пустым

# Валидация:
# запрос валиден, если валидны все поля по отдельности

# Структура ответа:
# {"code": <числовой код>, "response": {<ответ вызываемого метода>}}
# {"code": <числовой код>, "error": {<сообщение об ошибке>}}

# Аутентификация:
# смотри check_auth в шаблоне. В случае если не пройдена, нужно возвращать
# {"code": 403, "error": "Forbidden"}

# Метод online_score.
# Аргументы:
# phone - строка или число, длиной 11, начинается с 7, опционально, может быть пустым
# email - строка, в которой есть @, опционально, может быть пустым
# first_name - строка, опционально, может быть пустым
# last_name - строка, опционально, может быть пустым
# birthday - дата в формате DD.MM.YYYY, с которой прошло не больше 70 лет, опционально, может быть пустым
# gender - число 0, 1 или 2, опционально, может быть пустым

# Валидация аругементов:
# аргументы валидны, если валидны все поля по отдельности и если присутсвует хоть одна пара
# phone-email, first name-last name, gender-birthday с непустыми значениями.

# Контекст
# в словарь контекста должна прописываться запись  "has" - список полей,
# которые были не пустые для данного запроса

# Ответ:
# в ответ выдается произвольное число, которое больше или равно 0
# {"score": <число>}
# или если запрос пришел от валидного пользователя admin
# {"score": 42}
# или если произошла ошибка валидации
# {"code": 422, "error": "<сообщение о том какое поле невалидно>"}


# $ curl -X POST  -H "Content-Type: application/json" -d '{"account": "horns&hoofs", "login": "h&f", "method": "online_score", "token": "55cc9ce545bcd144300fe9efc28e65d415b923ebb6be1e19d2750a2c03e80dd209a27954dca045e5bb12418e7d89b6d718a9e35af34e14e1d5bcd5a08f21fc95", "arguments": {"phone": "79175002040", "email": "stupnikov@otus.ru", "first_name": "Стансилав", "last_name": "Ступников", "birthday": "01.01.1990", "gender": 1}}' http://127.0.0.1:8080/method/
# -> {"code": 200, "response": {"score": 5.0}}

# Метод clients_interests.
# Аргументы:
# client_ids - массив числе, обязательно, не пустое
# date - дата в формате DD.MM.YYYY, опционально, может быть пустым

# Валидация аругементов:
# аргументы валидны, если валидны все поля по отдельности.

# Контекст
# в словарь контекста должна прописываться запись  "nclients" - количество id'шников,
# переденанных в запрос


# Ответ:
# в ответ выдается словарь <id клиента>:<список интересов>. Список генерировать произвольно.
# {"client_id1": ["interest1", "interest2" ...], "client2": [...] ...}
# или если произошла ошибка валидации
# {"code": 422, "error": "<сообщение о том какое поле невалидно>"}

# $ curl -X POST  -H "Content-Type: application/json" -d '{"account": "horns&hoofs", "login": "admin", "method": "clients_interests", "token": "d3573aff1555cd67dccf21b95fe8c4dc8732f33fd4e32461b7fe6a71d83c947688515e36774c00fb630b039fe2223c991f045f13f24091386050205c324687a0", "arguments": {"client_ids": [1,2,3,4], "date": "20.07.2017"}}' http://127.0.0.1:8080/method/
# -> {"code": 200, "response": {"1": ["books", "hi-tech"], "2": ["pets", "tv"], "3": ["travel", "music"], "4": ["cinema", "geek"]}}

# Требование: в результате в git должно быть только два(2!) файлика: api.py, test.py.
# Deadline: следующее занятие

import abc
import json
import inspect
import random
import datetime
import logging
import hashlib
import uuid
import numbers
import string
from dateutil.relativedelta import relativedelta
from optparse import OptionParser
from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler

SALT = "Otus"
ADMIN_LOGIN = "admin"
ADMIN_SALT = "42"
OK = 200
BAD_REQUEST = 400
FORBIDDEN = 403
NOT_FOUND = 404
INVALID_REQUEST = 422
INTERNAL_ERROR = 500
ERRORS = {
    BAD_REQUEST: "Bad Request",
    FORBIDDEN: "Forbidden",
    NOT_FOUND: "Not Found",
    INVALID_REQUEST: "Invalid Request",
    INTERNAL_ERROR: "Internal Server Error",
}
UNKNOWN = 0
MALE = 1
FEMALE = 2
GENDERS = {
    UNKNOWN: "unknown",
    MALE: "male",
    FEMALE: "female",
}


class InvalidRequest(BaseException):
    """Raise if request is invalid (422)"""


class InvalidField(BaseException):
    """Raise if invalid value for field is provided"""


class VerifiableField(object):
    def __init__(self, required, nullable=False):
        self.required = required
        self.nullable = nullable

    def verify(self, value):
        return (
            (not self.required or value is not None) and
            (self.nullable or value)
        )

    def __get__(self, obj, objtype=None):
        return self.value

    def __set__(self, obj, value):
        if not self.verify(value):
            raise InvalidField()
        self.value = value


class CharField(VerifiableField):
    def verify(self, value):
        if value is None:
            return not self.required
        return (
            super(CharField, self).verify(value) and
            isinstance(value, basestring)
        )


class ArgumentsField(VerifiableField):
    def verify(self, value):
        return (
            super(ArgumentsField, self).verify(value) and
            isinstance(value, dict)
        )


class EmailField(CharField):
    def verify(self, value):
        if value is None:
            return not self.required
        return (
            super(EmailField, self).verify(value) and
            (not value or '@' in value)
        )


class PhoneField(VerifiableField):
    def verify(self, value):
        if value is None:
            return not self.required
        if (
            super(PhoneField, self).verify(value) and
            isinstance(value, (basestring, numbers.Number))
        ):
            field = str(value)
            return len(field) == 11 and field[0] == '7'
        else:
            return False


class DateField(VerifiableField):
    def verify(self, value):
        if not super(DateField, self).verify(value):
            return False
        if value is None:
            return not self.required
        try:
            datetime.datetime.strptime(value, '%d.%m.%Y')
            return True
        except ValueError:
            return False


class BirthDayField(VerifiableField):
    def verify(self, value):
        if super(BirthDayField, self).verify(value):
            if value is None:
                return not self.required
            try:
                parsed_date = datetime.datetime.strptime(
                    value, '%d.%m.%Y')
                return (
                    parsed_date + relativedelta(years=70) >=
                    datetime.datetime.today()
                )
            except ValueError:
                return False
        else:
            return False


class GenderField(VerifiableField):
    def verify(self, value):
        if value is None:
            return not self.required
        return (
            super(GenderField, self).verify(value) and value in [0, 1, 2]
        )


class ClientIDsField(VerifiableField):
    def verify(self, value):
        return (
            super(ClientIDsField, self).verify(value) and
            isinstance(value, (list, tuple)) and
            all(isinstance(i, numbers.Number) for i in value)
        )


class Request(object):
    def __init__(self, arguments):
        for name, attr in self.__class__.__dict__.iteritems():
            if isinstance(attr, VerifiableField):
                if (
                    (attr.required and name not in arguments) or
                    (not attr.nullable and not arguments.get(name))
                ):
                    raise InvalidRequest()
                else:
                    try:
                        setattr(self, name, arguments.get(name))
                    except InvalidField as e:
                        raise InvalidRequest(
                            '{} field contains invalid value: {!r}'.format(
                                name, arguments.get(name))
                        )

    def verify(self):
        raise NotImplementedError()

    def response(self, ctx):
        raise NotImplementedError()


class ClientsInterestsRequest(Request):
    client_ids = ClientIDsField(required=True)
    date = DateField(required=False, nullable=True)

    def response(self, ctx):
        ctx['nclients'] = len(self.client_ids)
        interests = {
            client_id: [
                ''.join(
                    random.choice(string.ascii_letters + string.digits)
                    for n in xrange(random.randint(3, 10))
                )
                for _ in xrange(random.randint(3, 10))
            ]
            for client_id in self.client_ids
        }
        return interests, OK


class OnlineScoreRequest(Request):
    first_name = CharField(required=False, nullable=True)
    last_name = CharField(required=False, nullable=True)
    email = EmailField(required=False, nullable=True)
    phone = PhoneField(required=False, nullable=True)
    birthday = BirthDayField(required=False, nullable=True)
    gender = GenderField(required=False, nullable=True)

    def __init__(self, arguments, is_admin=False):
        super(OnlineScoreRequest, self).__init__(arguments)
        self.is_admin = is_admin

    def verify(self):
        return (
            self.phone and self.email or
            self.first_name and self.last_name or
            self.gender is not None and self.birthday
        )

    def response(self, ctx):
        ctx['has'] = [
            name
            for name, attr
            in self.__class__.__dict__.iteritems()
            if isinstance(attr, VerifiableField) and
            getattr(self, name) or getattr(self, name) == 0
        ]
        if not self.verify():
            return ERRORS[INVALID_REQUEST], INVALID_REQUEST
        elif self.is_admin:
            return {'score': 42}, OK
        else:
            return {'score': random.randint(0, 100)}, OK


class MethodRequest(Request):
    account = CharField(required=False, nullable=True)
    login = CharField(required=True, nullable=True)
    token = CharField(required=True, nullable=True)
    arguments = ArgumentsField(required=True, nullable=True)
    method = CharField(required=True, nullable=False)

    @property
    def is_admin(self):
        return self.login == ADMIN_LOGIN

    def response(self, ctx):
        if not check_auth(self):
            return ERRORS[FORBIDDEN], FORBIDDEN
        elif self.method == 'clients_interests':
            return ClientsInterestsRequest(self.arguments).response(ctx)
        elif self.method == 'online_score':
            return OnlineScoreRequest(
                self.arguments, self.is_admin).response(ctx)


def check_auth(request):
    if request.login == ADMIN_LOGIN:
        digest = hashlib.sha512(datetime.datetime.now().strftime("%Y%m%d%H") + ADMIN_SALT).hexdigest()
    else:
        digest = hashlib.sha512(request.account + request.login + SALT).hexdigest()
    if digest == request.token:
        return True
    return False


def method_handler(request, ctx):
    try:
        request = MethodRequest(request['body'])
        response, code = request.response(ctx)
    except InvalidRequest:
        response, code = ERRORS[INVALID_REQUEST], INVALID_REQUEST
    return response, code


class MainHTTPHandler(BaseHTTPRequestHandler):
    router = {
        "method": method_handler
    }

    def get_request_id(self, headers):
        return headers.get('HTTP_X_REQUEST_ID', uuid.uuid4().hex)

    def do_POST(self):
        response, code = {}, OK
        context = {"request_id": self.get_request_id(self.headers)}
        request = None
        try:
            data_string = self.rfile.read(int(self.headers['Content-Length']))
            request = json.loads(data_string)
        except:
            code = BAD_REQUEST

        if request:
            path = self.path.strip("/")
            logging.info("%s: %s %s" % (self.path, data_string, context["request_id"]))
            if path in self.router:
                try:
                    response, code = self.router[path]({"body": request, "headers": self.headers}, context)
                except Exception, e:
                    logging.exception("Unexpected error: %s" % e)
                    code = INTERNAL_ERROR
            else:
                code = NOT_FOUND

        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        if code not in ERRORS:
            r = {"response": response, "code": code}
        else:
            r = {"error": response or ERRORS.get(code, "Unknown Error"), "code": code}
        context.update(r)
        logging.info(context)
        self.wfile.write(json.dumps(r))
        return

if __name__ == "__main__":
    op = OptionParser()
    op.add_option("-p", "--port", action="store", type=int, default=8080)
    op.add_option("-l", "--log", action="store", default=None)
    (opts, args) = op.parse_args()
    logging.basicConfig(filename=opts.log, level=logging.INFO,
                        format='[%(asctime)s] %(levelname).1s %(message)s', datefmt='%Y.%m.%d %H:%M:%S')
    server = HTTPServer(("localhost", opts.port), MainHTTPHandler)
    logging.info("Starting server at %s" % opts.port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    server.server_close()
