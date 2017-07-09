#!/usr/bin/env python
# -*- coding: utf-8 -*-


# log_format ui_short '$remote_addr $remote_user $http_x_real_ip [$time_local] "$request" '
#                     '$status $body_bytes_sent "$http_referer" '
#                     '"$http_user_agent" "$http_x_forwarded_for" "$http_X_REQUEST_ID" "$http_X_RB_USER" '
#                     '$request_time';

import os
import argparse
import gzip
import json
import re
import operator
import math
import datetime
import collections


LOG_REGEXP = 'nginx-access-ui.log-([0-9]+)[.]gz$'

config = {
    "REPORT_SIZE": 1000,
    "REPORT_DIR": "./reports",
    "REPORT_TEMPLATE": "./report.html",
    "LOG_DIR": "./log"
}


def process(fin):
    urls_times = collections.defaultdict(list)
    num_logs = 0
    total_time = 0
    for log_line in fin:
        num_logs += 1
        split_line = log_line.split('"')

        request, request_time = (split_line[1], float(split_line[-1]))
        split_request = request.split()
        if len(split_request) > 1:
            url = request.split()[1]
            urls_times[url].append(request_time)
            total_time += request_time

    urls_stat = calc_urls_stat(urls_times, num_logs, total_time)
    json_stat = json.dumps(urls_stat[:config['REPORT_SIZE']])

    return json_stat


def calc_urls_stat(urls_times, num_logs, total_time):
    urls_stat = []

    for url, times in urls_times.iteritems():
        times = sorted(times)
        count = len(times)
        time_sum = sum(times)
        url_stat = {
            'url': url,
            'count': count,
            'count_perc': round(count * 100.0 / num_logs, 3),
            'time_max': max(times),
            'time_p50': calc_perc(times, 50),
            'time_p95': calc_perc(times, 95),
            'time_p99': calc_perc(times, 99),
            'time_perc': round(time_sum * 100.0 / total_time, 3),
            'time_sum': round(time_sum, 3),
        }
        urls_stat.append(url_stat)

    urls_stat = sorted(
        urls_stat,
        key=operator.itemgetter('time_perc', 'time_sum'),
        reverse=True
    )

    return urls_stat


def calc_perc(sorted_values, perc):
    position = int(math.ceil(len(sorted_values) / 100.0 * perc)) - 1
    return sorted_values[position]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--log_path',
        help='log file to process',
        required=False
    )
    parser.add_argument(
        '--json',
        action='store_true'
    )
    args = parser.parse_args()

    if args.log_path:
        log_path = args.log_path
    else:
        log_filenames = os.listdir(config['LOG_DIR'])
        if not log_filenames:
            return
        last_log_filename = sorted(log_filenames)[-1]
        log_path = '{}/{}'.format(config['LOG_DIR'], last_log_filename)

    date_str = re.sub(LOG_REGEXP, r'\1', os.path.basename(log_path))
    last_log_date = datetime.datetime.strptime(date_str, '%Y%m%d')

    format = 'json' if args.json else 'html'
    report_path = '{}/report-{}.{}'.format(
        config['REPORT_DIR'],
        last_log_date.strftime('%Y.%m.%d'),
        format
    )

    if os.path.exists(report_path):
        print 'report already exists'
        return
    if not os.path.exists(os.path.dirname(report_path)):
        os.makedirs(os.path.dirname(report_path))

    if log_path.endswith('gz'):
        with gzip.open(log_path, 'rb') as fin:
            table_json = process(fin)
    else:
        with open(log_path, 'rb') as fin:
            table_json = process(fin)

    try:
        with open(report_path, 'wb') as report_file:
            if args.json:
                report_file.write(table_json)
            else:
                with open(config['REPORT_TEMPLATE'], 'rb') as report_template:
                    for line in report_template:
                        line = line.replace('$table_json', table_json)
                        report_file.write(line)
    except:
        os.remove(report_path)


if __name__ == "__main__":
    main()
