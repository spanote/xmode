from collections import defaultdict
from json import loads
from pprint import pprint

import numpy as np

keyword = 'EVENT: '
collections = defaultdict(list)

def aggregate(event):
    # data has "message", "timestamp" and "ingestionTime"
    message = event["message"].strip()

    if keyword not in message:
        return

    data = loads(message[message.find(keyword) + len(keyword):])

    if data['action'] != 'overall':
        return

    collections[data['workers']].append(data)


def summarize():
    packages = []
    for worker_count, datasets in collections.items():
        package = dict(
            worker_count=worker_count,
            length=len(datasets),
            stat=_get_stat([dataset['elapsed_time'] for dataset in datasets])
            # raw=datasets,
        )
        packages.append(package)

    packages.sort(key=lambda x: x['worker_count'])

    # pprint(packages, indent=2, width=160)

    print(f'| {"Max Worker":<10} | {"Sample Size":<11} | {"Min":<8} | {"Max":<8} | {"Mean":<8} | {"Median":<8} | {"STD":<8} |')
    print(f'| {"-" * 10} | {"-" * 11} | {"-" * 8} | {"-" * 8} | {"-" * 8} | {"-" * 8} | {"-" * 8} |')
    for p in packages:
        s = p['stat']
        print(f'| {p.get("worker_count"):>10d} | {p.get("length"):>11d} | {s.get("min"):>8.4f} | {s.get("max"):>8.4f} | {s.get("mean"):>8.4f} | {s.get("median"):>8.4f} | {s.get("std"):>8.4f} | ')

def _get_stat(series):
    return dict(
        min=np.amin(series),
        max=np.amax(series),
        mean=np.mean(series),
        median=np.median(series),
        std=np.std(series),
    )