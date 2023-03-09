import os
import json
from google.cloud import datastore
from flask import Flask, render_template, request
from datetime import datetime

app = Flask(__name__)
project_id = 'resume-ch'

app = Flask(__name__)
CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "*",
    "Access-Control-Allow-Headers": "*",
    "Access-Control-Max-Age": "3600",
}


def get_client(project_id):
    # Note that if we want to specify a project here, we could do it like this:
    # return datastore.Client('your-project-id')
    # Calling Client() with no argument will access the environment variables
    # for your project - which will be fine for your deployed application.
    return datastore.Client(project_id)


client = get_client(project_id)


@app.route('/index', methods=['OPTIONS'])
def cors_visitor(request):
    if hasattr(request, "method") and request.method == "OPTIONS":
        return ("", 200, CORS_HEADERS)


@app.route('/index', methods=['GET'])
def read_visitor():
    message = "read_visitor running!"
    service = os.environ.get('K_SERVICE', 'Unknown service')
    revision = os.environ.get('K_REVISION', 'Unknown revision')
    key = client.key('Visitors', 'vid')
    visitors = client.get(key)

    if not visitors:
        raise ValueError("vid does not exist.")

    # return str(visitors["v_count"])
    return (json.dumps({"v_count": str(visitors["v_count"]),
                        "page_count": str(visitors["page_count"])}), 200, CORS_HEADERS)


@app.route('/index', methods=['POST'])
def update_visitor():
    tmp = str(request.environ.get('HTTP_X_FORWARDED_FOR'))
    # if "," in tmp:
    #     client_ip, fwd_ip = tmp.split(",")
    # else:
    #     client_ip = ""
    #     fwd_ip = ""

    # query_remote_ip = client.query(kind='Visitors-ip')
    # query_fwd = client.query(kind='Visitors-ip')
    query_client_ip = client.query(kind='Visitors-ip')

    # query_remote_ip = query_remote_ip.add_filter('remote_ip', '=', request.remote_addr)
    # query_fwd = query_fwd.add_filter('forwarded_ip', '=', request.environ.get('HTTP_X_FORWARDED_FOR'))
    query_client_ip = query_client_ip.add_filter('client_ip', '=', client_ip)

    # result_ip = list(query_remote_ip.fetch())
    # result_fwd = list(query_fwd.fetch())
    result_client_ip = list(query_client_ip.fetch())

    # create entry in visitors-ip with client ip
    key_v = client.key('Visitors-ip')
    visitors_ip = datastore.Entity(key_v)
    visitors_ip["remote_ip"] = request.remote_addr
    visitors_ip["forwarded_ip"] = request.environ.get('HTTP_X_FORWARDED_FOR')
    visitors_ip["update_ts"] = datetime.now()
    visitors_ip["client_ip"] = tmp  # client_ip
    client.put(visitors_ip)

    key = client.key('Visitors', 'vid')
    visitors = client.get(key)
    if not visitors:
        raise ValueError("vid does not exist.")
    # client ip
    ip_addr = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
    visitors["update_ts"] = datetime.now()
    visitors["ip_addr"] = ip_addr
    visitors["page_count"] += 1

    # if len(result_ip) == 0 or len(result_fwd) == 0:
    if len(result_client_ip) == 0:
        visitors["v_count"] += 1

    client.put(visitors)

    return (json.dumps({"v_count": str(visitors["v_count"]),
                        "page_count": str(visitors["page_count"])}), 200, CORS_HEADERS)


if __name__ == '__main__':
    server_port = os.environ.get('PORT', '8080')
    app.run(debug=False, port=server_port, host='0.0.0.0')
