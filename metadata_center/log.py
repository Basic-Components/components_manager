"""flask插件形式的log设置组件.

## 基本的使用方法

```python
from log import FlaskSetLog
app = Flask(__name__)
run_aplication = FlaskSetLog(app)
```

或者使用默认的实例:
```python
from log import set_log

app = Flask(__name__)
set_log.init_app(app)
```

## 可以设置flask的了log配置

+ `SET_LOG_FMT:bool` 可以用于设置log的格式,目前支持json和txt
+ `SET_LOG_ERRORLOG:str` 可以设置服务器的log是否要输出到文本.默认为`-`,意为输出到stdout,其他则会写到字符串对应的文件名中.
    输出到文本则使用`TimedRotatingFileHandler`具体设置可以查看[官方文档](https://docs.python.org/3/library/logging.handlers.html#timedrotatingfilehandler)
    其他相关的参数还有:
    + `SET_LOG_ERRORLOG_WHEN:str` 默认'midnight',什么时候更新文件回卷
    + `SET_LOG_ERRORLOG_INTERVAL:int` 默认1,回卷间隔
    + `SET_LOG_ERRORLOG_BACKCOUNT:int` 默认3,保留多少个历史文件
    + `SET_LOG_ERRORLOG_ENCODING:str`: 默认"utf-8",使用什么编码保存
    + `SET_LOG_ERRORLOG_DELAY: 默认False, 是否延迟
    + `SET_LOG_ERRORLOG_UTC: 默认True,log回滚时间是否使用utc时间
    + `SET_LOG_ERRORLOG_ATTIME:str`:默认为None,使用格式"9,10,30"表示9点10分30秒
    + `SET_LOG_ERRORLOG_LOGLEVEL:int`默认"info",server的log等级

+ `SET_LOG_MAIL_LOG:bool`,可以设置app的logger是否要支持发送错误信息到邮箱,相关的其他参数还有:
    + `SET_LOG_MAILHOST:str` 默认为None,设置发送邮箱的地址
    + `SET_LOG_MAILPORT:int` 默认为25,设置发送邮箱的端口
    + `SET_LOG_MAILSSL:bool` 默认为False,设置发送邮箱是否使用ssl加密发送(25端口一般不加密,465端口一般加密)
    + `SET_LOG_MAILUSERNAME:str` 默认为None,设置发送邮箱的用户名
    + `SET_LOG_MAILPASSWORD:str` 默认为None,设置发送邮箱的密码
    + `SET_LOG_MAILFROMADDR:str` 默认为None,设置发送邮箱的地址
    + `SET_LOG_MAILTOADDRS:List[str]` 默认为None,设置要发送去的目标,注意是字符串列表
    + `SET_LOG_MAILSUBJECT:str` 默认为`Application Error`,设置发送去邮件的主题
"""
import sys
import time
import datetime
import logging
import structlog
from logging.handlers import (
    TimedRotatingFileHandler,
    SMTPHandler
)

from flask import request
from flask.logging import default_handler
import werkzeug._internal as _internal
logging.Formatter.converter = time.gmtime

class RequestFormatter(logging.Formatter):
    def format(self, record):
        record.request = '{0} {1}'.format(request.method, request.url)
        record.host = request.host
        return super().format(record)


Formatters = {
    "access_json": RequestFormatter(** {
        "fmt": '''{"time":"%(asctime)s","name":"metadata_center.server", "level":"%(levelname)s","host":"%(host)s","request":"%(request)s",%(message)s}''',
        "datefmt": "%Y-%m-%dT%H:%M:%S Z"
    }),
    "werkzeug_json": logging.Formatter(**{
        "fmt": '''{"timestamp":"%(asctime)s","logger":"werkzeug.server", "level":"%(levelname)s","msg":"%(message)s"}''',
        "datefmt": "%Y-%m-%dT%H:%M:%S Z"
    })
}


def emit(self, record):
    try:
        import smtplib
        from email.message import EmailMessage
        import email.utils

        port = self.mailport
        if not port:
            port = smtplib.SMTP_PORT
        smtp = smtplib.SMTP_SSL(self.mailhost, port, timeout=self.timeout)
        msg = EmailMessage()
        msg['From'] = self.fromaddr
        msg['To'] = ','.join(self.toaddrs)
        msg['Subject'] = self.getSubject(record)
        msg['Date'] = email.utils.localtime()
        msg.set_content(self.format(record))
        if self.username:
            if self.secure is not None:
                smtp.ehlo()
                smtp.starttls(*self.secure)
                smtp.ehlo()
            smtp.login(self.username, self.password)
        smtp.send_message(msg)
        smtp.quit()
    except Exception:
        self.handleError(record)


def _init_logger(
        app,
        errorlog="-",
        errorlog_when='midnight',
        errorlog_interval=1,
        errorlog_backupcount=3,
        errorlog_encoding="utf-8",
        errorlog_delay=False,
        errorlog_utc=True,
        errorlog_attime=None,
        flask_log_level=logging.INFO,
        werkzeug_log_level=logging.INFO,
        mail_log=False,
        mailhost=None,
        mailport=25,
        mailusername=None,
        mailpassword=None,
        mailssl=False,
        mailfromaddr=None,
        mailtoaddrs=None,
        mailsubject="Application Error"):
    """为flask项目设置logger.

    Args:
        app ([type]): flask的app对象
    """
    formatter = Formatters.get("access_json")
    default_handler.setFormatter(formatter)
    handler = logging.StreamHandler(sys.stdout)
    flask_app_logger = logging.getLogger("flask.app")
    flask_app_logger.addHandler(handler)
    flask_app_logger.setLevel(flask_log_level)  # 设置最低log等级
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,  # 判断是否接受某个level的log消息
            structlog.stdlib.add_logger_name,  # 增加字段logger
            structlog.stdlib.add_log_level,  # 增加字段level
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),  # 增加字段timestamp且使用iso格式输出
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,  # 捕获异常的栈信息
            structlog.processors.StackInfoRenderer(),  # 详细栈信息
            structlog.processors.JSONRenderer()  # json格式输出,第一个参数会被放入event字段
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    log = structlog.get_logger("flask.app")
    app.logger = log
    if errorlog == "-":
        werkzeug_handler = logging.StreamHandler()
    else:
        werkzeug_handler = TimedRotatingFileHandler(**{
            "filename": errorlog,
            "when": errorlog_when,
            "interval": errorlog_interval,
            "backupCount": errorlog_backupcount,
            "encoding": errorlog_encoding,
            "delay": errorlog_delay,
            "utc": errorlog_utc,
            "atTime": None if not errorlog_attime else datetime.time(*[int(i) for i in errorlog_attime.split(",")])
        })
    werkzeug_handler.setFormatter(Formatters.get("werkzeug_json"))
    werkzeug_logger = logging.getLogger("werkzeug")
    werkzeug_logger.handlers = []
    werkzeug_logger.addHandler(werkzeug_handler)
    werkzeug_logger.setLevel(werkzeug_log_level)  # 设置最低log等级

    if mail_log is True:
        if mailport:
            mailhost = (mailhost, mailport)
        if mailssl:
            SMTPHandler.emit = emit
        if mailusername:
            if mailpassword:
                credentials = (mailusername, mailpassword)
            else:
                credentials = (mailusername,)
            mail_handler = SMTPHandler(
                mailhost=mailhost,
                fromaddr=mailfromaddr,
                toaddrs=mailtoaddrs,
                credentials=credentials,
                subject=mailsubject
            )
        else:
            mail_handler = SMTPHandler(
                mailhost=mailhost,
                fromaddr=mailfromaddr,
                toaddrs=mailtoaddrs,
                subject=mailsubject
            )
        mail_handler.setLevel("ERROR")
        mail_handler.setFormatter(formatter)
        if not app.debug:
            flask_app_logger.addHandler(mail_handler)


class FlaskSetLog:
    """可以通过配置`SET_LOG_xxxx`来设置参数."""

    def __init__(self, app=None):
        if app:
            self.init_app(app)

    def init_app(self, app):
        self.app = app
        if not hasattr(app, 'extensions'):
            app.extensions = {}
        app.extensions['setlog'] = self
        log_config = (app.config.get_namespace('SET_LOG_'))
        _init_logger(app=self.app, **log_config)


set_log = FlaskSetLog()
__all__ = ["FlaskSetLog", "set_log"]