import json


def log_output(data):
    with open('output_log.json', 'w') as f:
        json.dump(data, f, indent=4)

    print('✅ Workflow log saved')
