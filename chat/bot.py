from datetime import datetime
from io import StringIO
import requests
import csv
import django_rq
from django.conf import settings


def execute_command(command):
    created = datetime.now()
    response = {
        'author': 'Bot',
        'created_date': created.strftime('%Y-%m-%d'),
        'created_time': created.strftime('%H:%M'),
    }
    command_data = command.split("=")
    if len(command_data) != 2:
        response['status'] = 'error'
        response['message'] = 'Error: Command not understood'
    else:
        if command_data[0] == 'stock':
            try:
                queue = django_rq.get_queue(settings.REDIS_SETTING)
                job = queue.enqueue(get_stock, parameter=command_data[1])
                response['job_id'] = str(job.key)[:-1].split(':')[2]
                response['status'] = 'queued'
                response['message'] = 'Command {} started and will return the result shortly'.format(command_data[0])
            except:
                response['status'] = 'error'
                response['message'] = 'Error: Something goes wrong'
        else:
            response['status'] = 'error'
            response['message'] = 'Error: Command {} doesn\'t exists'.format(command_data[0])
    return response


def command_status(job_id):
    response = {}
    queue = django_rq.get_queue(settings.REDIS_SETTING)
    job = queue.fetch_job(job_id)
    response['author'] = 'Bot'
    created = datetime.now()
    response['created_date'] = created.strftime('%Y-%m-%d')
    response['created_time'] = created.strftime('%H:%M')
    if job.is_finished:
        response['status'] = 'done'
        response['message'] = job.return_value
    elif job.is_failed:
        response['status'] = 'error'
        response['message'] = 'Error: Failed fetching stock data'
    else:
        response['status'] = 'working'
    return response


def get_stock(parameter):
    r = requests.get('https://stooq.com/q/l/?s={}&f=sd2t2ohlcv&h&e=csv%E2%80%8B'.format(parameter))
    f = StringIO(r.text)
    cr = csv.DictReader(f)
    row = next(cr)
    return '{} quote is {} per share'.format(row['Symbol'], row['Close'])
