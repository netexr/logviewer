#!/usr/bin/python
# encoding: utf-8

import os.path
import glob
from flask import Flask, render_template, request, send_file
from flask_cas import CAS
from flask_cas import login_required
import tempfile

app = Flask(__name__)
app.secret_key = '*&^TFGIYGBJIUYGHJK/*GBNKHujasdklfds9329ekjsdfj'
cas = CAS(app, '/cas')
app.config['CAS_SERVER'] = '<your-cas-server-here>'

BASE_DIR = '<your-app-path-here>'
LOG_DIR = os.path.join(BASE_DIR, 'logs')  # 日志路径，根据情况修改
TOMCAT_SYSLOG_PATH = os.path.join(LOG_DIR, 'tomcat/sys')  # 系统日志路径，根据情况修改
TOMCAT_APPLOG_PATH = os.path.join(LOG_DIR, 'tomcat/app')  # 应用日志路径，根据情况修改
PAGE_SIZE = 1024 * 1024  # 每页最多展示1M


def get_tomcat_apps():
    apps = glob.glob(os.path.join(BASE_DIR, 'tomcat_*_*_0?'))  # tomcat目录命名规则，根据情况修改
    if len(apps) > 0:
        apps = [os.path.split(i)[-1] for i in apps]
    return apps


def get_tomcat_logs(app_name):
    syslog_list = []

    if os.path.isfile(os.path.join(TOMCAT_SYSLOG_PATH, '{app}/catalina.log'.format(app=app_name))):
        syslog_list.append('catalina.log')
    if os.path.isfile(os.path.join(TOMCAT_SYSLOG_PATH, '{app}/{app}.log'.format(app=app_name))):
        syslog_list.append(app_name + '.log')
    applog_list = glob.glob(os.path.join(TOMCAT_APPLOG_PATH, '{app}/*.log'.format(app=app_name)))
    if applog_list:
        applog_list = [os.path.split(i)[-1] for i in applog_list]

    return syslog_list, applog_list


def search_in_file(content, keyword):
    logs = []
    f = tempfile.TemporaryFile()
    f.write(content.encode('utf-8'))
    f.seek(0)
    for line in f:
        line = line.decode('utf-8')
        if keyword in line:
            logs.append(line)
    f.close()
    return ''.join(logs)


@app.route("/", methods=['GET'])
def index():
    apps = get_tomcat_apps()
    if len(apps) == 0:
        return "No tomcat apps found"
    else:
        return render_template('index.html', apps=apps)


@app.route('/<app_name>/', methods=['GET'])
@login_required
def list_logs(app_name):
    if app_name not in get_tomcat_apps():
        return '出错啦，你输入的应用名在本机不存在。'

    log_list = get_tomcat_logs(app_name)
    data = {
        'app_name': app_name,
        'sys_logs': log_list[0],
        'app_logs': log_list[1]
    }
    return render_template('log_list.html', data=data)


@app.route('/<app_name>/<log_type>/<log_name>/<int:seek_to>', methods=['GET'])
@login_required
def show_log(app_name, log_type, log_name, seek_to=0):
    data = {
        'app_name': app_name,
        'log_type': log_type,
        'log_name': log_name,
        'log_file': os.path.join(BASE_DIR, 'logs/tomcat/{}/{}/{}'.format(log_type, app_name, log_name))
    }
    if app_name not in get_tomcat_apps():
        return '出错啦，你输入的应用名在本机不存在'
    if log_type not in ['app', 'sys']:
        return '日志类型不要乱写哦'
    log_list = get_tomcat_logs(app_name)
    if log_type == 'sys' and log_name not in log_list[0]:
        return 'syslog日志名不要乱写哦'
    if log_type == 'app' and log_name not in log_list[1]:
        return 'applog日志名不要乱写哦'
    if os.path.isfile(data['log_file']):
        data['file_size'] = os.path.getsize(data['log_file'])
        with open(data['log_file'], 'rb') as f:
            if seek_to >= os.path.getsize(data['log_file']):
                if data['file_size'] > PAGE_SIZE:
                    seek_to = data['file_size'] - PAGE_SIZE
                else:
                    seek_to = 0
            f.seek(seek_to)
            content = f.read(PAGE_SIZE)
            content = content.decode('utf-8')

            search_keyword = request.args.get('q', '')
            if search_keyword:
                content = search_in_file(content, search_keyword)

            data['content'] = content.replace('\n', '<br>')
            data['q'] = search_keyword
            data['file_position'] = f.tell()
            data['prev'] = seek_to - PAGE_SIZE
            if data['prev'] < 0:
                data['prev'] = 0

        return render_template('show_log.html', data=data)
    else:
        return 'file not found'


@app.route('/truncate/<app_name>/<log_type>/<log_name>/', methods=['GET'])
@login_required
def truncate(app_name, log_type, log_name):
    if app_name not in get_tomcat_apps():
        return '出错啦，你输入的应用名在本机不存在'
    if log_type not in ['app', 'sys']:
        return '日志类型不要乱写哦'

    log_list = get_tomcat_logs(app_name)
    if log_type == 'sys' and log_name not in log_list[0]:
        return 'syslog日志名不要乱写哦'
    if log_type == 'app' and log_name not in log_list[1]:
        return 'applog日志名不要乱写哦'

    log_file = os.path.join(BASE_DIR, 'logs/tomcat/{}/{}/{}'.format(log_type, app_name, log_name))
    if os.path.isfile(log_file):
        with open(log_file, 'wb') as f:
            f.truncate()
        return 'log file has been truncated.'
    else:
        return 'file not found'


@app.route('/download/<app_name>/<log_type>/<log_name>/', methods=['GET'])
@login_required
def download(app_name, log_type, log_name):
    if app_name not in get_tomcat_apps():
        return '出错啦，你输入的应用名在本机不存在'
    if log_type not in ['app', 'sys']:
        return '日志类型不要乱写哦'

    log_list = get_tomcat_logs(app_name)
    if log_type == 'sys' and log_name not in log_list[0]:
        return 'syslog日志名不要乱写哦'
    if log_type == 'app' and log_name not in log_list[1]:
        return 'applog日志名不要乱写哦'

    log_file = os.path.join(BASE_DIR, 'logs/tomcat/{}/{}/{}'.format(log_type, app_name, log_name))
    return send_file(log_file, as_attachment=True)

