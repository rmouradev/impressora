from flask import Flask, render_template, request, redirect, url_for
import socket
from pysnmp.hlapi import *
import json
import os

app = Flask(__name__)

DESCRIPTIONS_FILE = 'printer_descriptions.json'

def load_descriptions():
    if os.path.exists(DESCRIPTIONS_FILE):
        with open(DESCRIPTIONS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_descriptions(descriptions):
    with open(DESCRIPTIONS_FILE, 'w') as f:
        json.dump(descriptions, f)

printer_descriptions = load_descriptions()

def check_printer_status(ip, port=9100):
    try:
        socket.create_connection((ip, port), timeout=0.1)
        return 'Online'
    except (socket.timeout, socket.error):
        return 'Offline'

def get_printer_info(ip):
    toner_oid = '1.3.6.1.4.1.367.3.2.1.2.24.1.1.5.1'  # OID fornecido para nível do toner
    info = {'toner_level': 'Desconhecido', 'name': 'Desconhecido'}
    try:
        # Buscar nível do toner
        error_indication, error_status, error_index, var_binds = next(
            getCmd(SnmpEngine(),
                   CommunityData('public', mpModel=0),
                   UdpTransportTarget((ip, 161), timeout=0.5),
                   ContextData(),
                   ObjectType(ObjectIdentity(toner_oid)))
        )
        if not error_indication and not error_status:
            for var_bind in var_binds:
                info['toner_level'] = int(var_bind[1])

        # Buscar nome da impressora
        try:
            info['name'] = socket.gethostbyaddr(ip)[0]
        except (socket.herror, socket.gaierror):
            info['name'] = 'Desconhecido'

    except Exception as e:
        pass
    return info

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        ip = request.form['ip']
        description = request.form['description']
        printer_descriptions[ip] = description
        save_descriptions(printer_descriptions)
        return redirect(url_for('index'))

    printers = []
    for i in range(2, 84):
        ip = f'10.42.108.{i}'
        status = check_printer_status(ip)
        if status == 'Online':
            printer_info = get_printer_info(ip)
            toner_level = printer_info['toner_level']
            name = printer_info['name']
        else:
            toner_level = 'N/A'
            name = 'N/A'
        description = printer_descriptions.get(ip, '')
        printers.append({'ip': ip, 'status': status, 'toner_level': toner_level, 'name': name, 'description': description})
    return render_template('index.html', printers=printers)

if __name__ == '__main__':
    app.run(debug=True)
