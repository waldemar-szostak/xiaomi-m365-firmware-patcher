import flask
import traceback
import sys
import os
import time
sys.path.append('..')
from patcher import FirmwarePatcher

app = flask.Flask(__name__)


@app.errorhandler(Exception)
def handle_bad_request(e):
    return 'Exception occured:\n{}'.format(traceback.format_exc()), \
            400, {'Content-Type': 'text/plain'}

# http://flask.pocoo.org/snippets/40/
@app.context_processor
def override_url_for():
    return dict(url_for=dated_url_for)

def dated_url_for(endpoint, **values):
    if endpoint == 'static':
        filename = values.get('filename', None)
        if filename:
            file_path = os.path.join(app.root_path,
                                     endpoint, filename)
            values['q'] = int(os.stat(file_path).st_mtime)
    return flask.url_for(endpoint, **values)


@app.route('/')
def home():
    return flask.render_template('home.html')

@app.route('/cfw')
def patch_firmware():
    version = flask.request.args.get('version', None)
    if version not in ['DRV130', 'DRV134', 'DRV138', 'DRV140', 'DRV141', 'DRV142', 'DRV143']:
        return 'Invalid firmware version.', 400

    with open('../bins/{}.bin'.format(version), 'rb') as fp:
        patcher = FirmwarePatcher(fp.read())

    filename = version + '-' + str(int(time.time()))
    iversion = int(version[3:])

    kers_min_speed = flask.request.args.get('kers_min_speed', None)
    if kers_min_speed is not None:
        kers_min_speed = float(kers_min_speed)
        assert kers_min_speed >= 0 and kers_min_speed <= 100
        patcher.kers_min_speed(kers_min_speed)

    normal_max_speed = flask.request.args.get('normal_max_speed', None)
    if normal_max_speed is not None:
        normal_max_speed = int(normal_max_speed)
        assert normal_max_speed >= 0 and normal_max_speed <= 100
        patcher.normal_max_speed(normal_max_speed)

    eco_max_speed = flask.request.args.get('eco_max_speed', None)
    if eco_max_speed is not None:
        eco_max_speed = int(eco_max_speed)
        assert eco_max_speed >= 0 and eco_max_speed <= 100
        patcher.eco_max_speed(eco_max_speed)

    motor_start_speed = flask.request.args.get('motor_start_speed', None)
    if motor_start_speed is not None:
        motor_start_speed = float(motor_start_speed)
        assert motor_start_speed >= 0 and motor_start_speed <= 100
        patcher.motor_start_speed(motor_start_speed)

    motor_power_constant = flask.request.args.get('motor_power_constant', None)
    if motor_power_constant is not None:
        motor_power_constant = int(motor_power_constant)
        assert motor_power_constant >= 25787 and motor_power_constant <= 65535
        patcher.motor_power_constant(motor_power_constant)

    cruise_control_delay = flask.request.args.get('cruise_control_delay', None)
    if cruise_control_delay is not None:
        cruise_control_delay = float(cruise_control_delay)
        assert cruise_control_delay >= 0.1 and cruise_control_delay <= 20.0
        patcher.cruise_control_delay(cruise_control_delay)

    instant_eco_switch = flask.request.args.get('instant_eco_switch', None)
    if instant_eco_switch:
        patcher.instant_eco_switch()

    boot_with_eco = flask.request.args.get('boot_with_eco', None)
    if boot_with_eco:
        patcher.boot_with_eco()

    voltage_limit = flask.request.args.get('voltage_limit', None)
    if voltage_limit is not None:
        voltage_limit = float(voltage_limit)
        assert voltage_limit >= 43.01 and voltage_limit <= 63.00
        patcher.voltage_limit(voltage_limit)

    russian_throttle = flask.request.args.get('russian_throttle', None)
    if russian_throttle:
        patcher.russian_throttle()

    remove_hard_speed_limit = flask.request.args.get('remove_hard_speed_limit', None)
    if remove_hard_speed_limit:
        patcher.remove_hard_speed_limit()

    remove_charging_mode = flask.request.args.get('remove_charging_mode', None)
    if remove_charging_mode:
        patcher.remove_charging_mode()

    bms_uart_76800 = flask.request.args.get('bms_uart_76800', None)
    if bms_uart_76800:
        patcher.bms_uart_76800()

    encrypt = flask.request.args.get('encrypt', None)
    if encrypt:
        assert iversion >= 140, 'Flashing encrypted 1.3.x firmware is not supported. Downgrade to 1.4.0 first.'
        patcher.encrypt()
        filename += '.encrypted'

    filename += '.bin'

    resp = flask.Response(patcher.data)
    resp.headers['Content-Type'] = 'application/octet-stream'
    resp.headers['Content-Disposition'] = 'inline; filename="{0}"'.format(filename)
    resp.headers['Content-Length'] = len(patcher.data)

    return resp

if __name__ == '__main__':
    app.run('0.0.0.0')
