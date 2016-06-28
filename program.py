import cherrypy
import requests
import mimetypes
import virtualbox
import os
import json
import sqlite3
import hashlib
import datetime
import time
from subprocess import call

hashadd = "HAAASH"


class WebApp(object):
    def __init__(self):
        self.api = RestAPI()

    def _cp_dispatch(self, vpath):
        if len(vpath) == 1:
            return self
        elif vpath[1] == 'api':
            return self.api
        else:
            return vpath

    @cherrypy.expose
    def index(self):
        try:
            if not bool(cherrypy.session['logged']):
                raise cherrypy.HTTPRedirect("/login")
        except KeyError:
            raise cherrypy.HTTPRedirect("/login")
        return {'msg': "Witam!"}

    @cherrypy.expose
    def login(self):
        return {'msg': "Witam!"}

    @cherrypy.expose
    def list_vms(self):
        return "WSTAW TU"

    @cherrypy.expose
    def new_machine(self, distribution, name):
        return "Ok."

    @cherrypy.expose
    def start_vm(self, machine_name=''):
        return {"status": "Ok"}

    @cherrypy.expose
    def state(self):
        return {"name": "ssss", "cpu": "cccc", "state": "ssss"}

    @cherrypy.expose
    def execute(self, cmd=''):
        return "EEEE"

    @cherrypy.expose
    def screenshot(self):
        return {'fname': '/static/screenshot.png'}

    @cherrypy.expose
    def terminal(self):
        return {'msg': ''}


class RestAPI(object):
    def __init__(self):
        self.vbox = virtualbox.VirtualBox()
        self.dbconnection = sqlite3.connect('./db/db.sqlite3', check_same_thread=False)
        self.machines = {}

    @cherrypy.expose
    def new_user(self, name, passwd):
        cursor = self.dbconnection.execute("SELECT login FROM Users")
        for row in cursor:
            if row[0] == name:
                return json.dumps({'status': 'Failed - user exists in DB.'})
        hash = hashlib.md5(hashadd + passwd).hexdigest()
        self.dbconnection.execute("INSERT INTO Users VALUES (\'{0}\', \'{1}\')".format(name, hash))
        self.dbconnection.commit()
        return json.dumps({'status': 'Ok.'})

    @cherrypy.expose
    def login(self, name, passwd):
        try:
            if bool(cherrypy.session['logged']):
                return json.dumps({'status': 'Logged as {0}.'.format(cherrypy.session['logged'])})
        except KeyError:
            None
        cursor = self.dbconnection.execute("SELECT * FROM Users")
        userExists = False
        dbpass = ""
        for row in cursor:
            if row[0] == name:
                userExists = True
                dbpass = row[1]
                break
        if not userExists:
            return json.dumps({'status': 'Failed - user not exists in DB.'})
        hash = hashlib.md5(hashadd + passwd).hexdigest()
        if hash != dbpass:
            return json.dumps({'status': 'Failed - incorrect password.'})
        cherrypy.session['logged'] = name
        return json.dumps({'status': 'Ok.'})

    @cherrypy.expose
    def logout(self):
        cherrypy.session['logged'] = ''
        return json.dumps({'status': 'Ok.'})

    @cherrypy.expose
    def index(self):
        return "API"

    @cherrypy.expose
    def start_vm(self, machine_name=''):
        try:
            if not bool(cherrypy.session['logged']):
                return json.dumps({'status': 'You are not logged in.'})
        except KeyError:
            return json.dumps({'status': 'You are not logged in.'})
        if machine_name == '':
            return json.dumps({"status": "Invalid machine name"})
        try:
            mach_tmp = self.machines[cherrypy.session['logged']]
        except KeyError:
            self.machines[cherrypy.session['logged']] = []
        try:
            machine = self.vbox.find_machine(machine_name)
            if not ('/' + cherrypy.session['logged']) in machine.groups:
                return json.dumps({"status": "Invalid machine name"})
            session = virtualbox.Session()
            self.machines[cherrypy.session['logged']].append({'machine': machine, 'session': session})
            cherrypy.session['progress'] = machine.launch_vm_process(session, 'gui', '')
            while not str(session.state) == "Locked":
                continue
        except Exception:
            return json.dumps({"status": "Failure"})
        return json.dumps({"status": "Ok"})

    def return_machine_by_name(self, login, name):
        try:
            for kv in self.machines[login]:
                if kv['machine'].name == name:
                    return kv['machine']
            return None
        except KeyError:
            return None

    def return_session_by_name(self, login, name):
        try:
            for kv in self.machines[login]:
                if kv['machine'].name == name:
                    return kv['session']
            return None
        except KeyError:
            return None

    def return_mach_sess_by_name(self, login, name):
        try:
            for kv in self.machines[login]:
                if kv['machine'].name == name:
                    return kv
            return None
        except KeyError:
            return None

    @cherrypy.expose
    def screenshot(self, name):
        try:
            if not bool(cherrypy.session['logged']):
                return json.dumps({'status': 'You are not logged in.'})
        except KeyError:
            return json.dumps({'status': 'You are not logged in.'})
        sess = self.return_session_by_name(cherrypy.session['logged'], name)
        if sess == None:
            return json.dumps({'furl': '', 'status': 'Failure - invalid machine name.'})
        h, w, _, _, _, _ = sess.console.display.get_screen_resolution(0)
        png = sess.console.display.take_screen_shot_to_array(0, h, w, virtualbox.library.BitmapFormat.png)
        fname = 'screenshot-{0}-{1}.png'.format(name, cherrypy.session['logged'])
        with open('./public/{0}'.format(fname), 'wb') as f:
            f.write(png)
        return json.dumps({'furl': '/static/{0}'.format(fname)})

    @cherrypy.expose
    def videocap(self, name, time_s):
        try:
            if not bool(cherrypy.session['logged']):
                return json.dumps({'status': 'You are not logged in.'})
        except KeyError:
            return json.dumps({'status': 'You are not logged in.'})
        session = self.return_session_by_name(cherrypy.session['logged'], name)
        if session == None:
            return json.dumps({'furl': '', 'status': 'Failure - invalid machine name.'})
        fname = 'videocap-{0}-{1}.webm'.format(name, cherrypy.session['logged'])
        try:
            session.machine.video_capture_file = os.path.abspath("./public/{0}".format(fname))
            session.machine.video_capture_enabled = True
            time.sleep(int(time_s))
            session.machine.video_capture_enabled = False
        except Exception:
            return json.dumps({'status': 'Failure: graphics drivers not ready yet.'})
        return json.dumps({'furl': '/static/{0}'.format(fname)})

    @cherrypy.expose
    def execute(self, name, cmd=''):
        try:
            if not bool(cherrypy.session['logged']):
                return json.dumps({'status': 'You are not logged in.'})
        except KeyError:
            return json.dumps({'status': 'You are not logged in.'})
        sess = self.return_session_by_name(cherrypy.session['logged'], name)
        if sess == None:
            return json.dumps({'out': '', 'err': '', 'status': 'Failure - invalid machine name.'})
        gsession = sess.console.guest.create_session('root', 'centos')
        cmds2 = ["-c", cmd]
        p, out, err = gsession.execute("/bin/bash", cmds2)
        gsession.close()
        return json.dumps({'out': str(out), 'err': str(err)})

    @cherrypy.expose
    def list_vms(self):
        try:
            if not bool(cherrypy.session['logged']):
                return json.dumps({'status': 'You are not logged in.'})
        except KeyError:
            return json.dumps({'status': 'You are not logged in.'})
        ret = ""
        for vm in self.vbox.machines:
            if ('/' + cherrypy.session['logged']) in vm.groups:
                ret += vm.name + ";"
        return json.dumps({'list': ret})

    @cherrypy.expose
    def list_working_vms(self):
        try:
            if not bool(cherrypy.session['logged']):
                return json.dumps({'status': 'You are not logged in.'})
        except KeyError:
            return json.dumps({'status': 'You are not logged in.'})
        ret = ""
        try:
            for kv in self.machines[cherrypy.session['logged']]:
                ret += kv['machine'].name + ";"
        except KeyError:
            None
        return json.dumps({'list': ret})

    @cherrypy.expose
    def state(self, name):
        try:
            if not bool(cherrypy.session['logged']):
                return json.dumps({'status': 'You are not logged in.'})
        except KeyError:
            return json.dumps({'status': 'You are not logged in.'})
        kv = self.return_mach_sess_by_name(cherrypy.session['logged'], name)
        machine = kv['machine']
        session = kv['session']
        return json.dumps({"name": str(machine.name), "cpu": str(machine.get_cpu_status(0)), "state": str(session.state)})

    @cherrypy.expose
    def new_machine(self, distribution, name):
        try:
            if not bool(cherrypy.session['logged']):
                return json.dumps({'status': 'You are not logged in.'})
        except KeyError:
            return json.dumps({'status': 'You are not logged in.'})
        try:
            new_machine = self.vbox.create_machine(settings_file='', name=name, groups=[], os_type_id="Linux",
                                                   flags='')
            src_machine = self.vbox.find_machine(distribution)
            src_machine.clone_to(new_machine, virtualbox.library.CloneMode(1), [])
            self.vbox.register_machine(new_machine)
            ch_gr_cmd = ["C:\\Program Files\\Oracle\\VirtualBox\\VBoxManage.exe", "modifyvm", name, "--groups",
                         '/' + cherrypy.session['logged']]
            a = call(ch_gr_cmd, shell=True)
        except Exception:
            return json.dumps({'status': 'Failure.'})
        except cherrypy.TimeoutError:
            None
        return json.dumps({'status': 'Ok.'})

    @cherrypy.expose
    def shutdown_vm(self, name):
        try:
            if not bool(cherrypy.session['logged']):
                return json.dumps({'status': 'You are not logged in.'})
        except KeyError:
            return json.dumps({'status': 'You are not logged in.'})
        kv = self.return_mach_sess_by_name(cherrypy.session['logged'], name)
        if kv == None:
            return json.dumps({'status': 'Failure.'})
        sess = kv['session']
        try:
            sess.console.power_down()
        except virtualbox.library.VBoxErrorInvalidVmState:
            return json.dumps({'status': 'Failure.'})
        self.machines[cherrypy.session['logged']].remove(kv)
        return json.dumps({'status': 'Ok.'})

    @cherrypy.expose
    def delete_machine(self, name):
        try:
            if not bool(cherrypy.session['logged']):
                return json.dumps({'status': 'You are not logged in.'})
        except KeyError:
            return json.dumps({'status': 'You are not logged in.'})
        machine = None
        for m in self.vbox.machines:
            if m.name == name and ('/' + cherrypy.session['logged']) in m.groups:
                machine = m
                break
        try:
            machine.remove(True)
        except Exception:
            return json.dumps({'status': 'Failure.'})
        return json.dumps({'status': 'Ok.'})

    @cherrypy.expose
    def rename_machine(self, old_name, new_name):
        try:
            if not bool(cherrypy.session['logged']):
                return json.dumps({'status': 'You are not logged in.'})
        except KeyError:
            return json.dumps({'status': 'You are not logged in.'})
        machine = None
        for m in self.vbox.machines:
            if m.name == old_name and ('/' + cherrypy.session['logged']) in m.groups:
                machine = m
                break
        try:
            session = machine.create_session()
            session.machine.name = new_name
            session.machine.save_settings()
            session.unlock_machine()
        except Exception:
            return json.dumps({'status': 'Failure.'})
        return json.dumps({'status': 'Ok.'})

    @cherrypy.expose
    def av_distros(self):
        machs = self.vbox.get_machines_by_groups(['/distros'])
        ret = ""
        for m in machs:
            ret += m.name + ";"
        return json.dumps({'list': ret})


if __name__ == '__main__':
    conf = {
        'server.socket_port': 8081
    }
    cherrypy.config.update(conf)

    from jinja2 import Environment, FileSystemLoader
    from plugins.jinja2plugin import Jinja2TemplatePlugin

    env = Environment(loader=FileSystemLoader('.'))
    Jinja2TemplatePlugin(cherrypy.engine, env=env).subscribe()
    from tools.jinja2tool import Jinja2Tool

    cherrypy.tools.template = Jinja2Tool()
    conf2 = {'/': {'tools.template.on': True,
                   'tools.sessions.on': True,
                   'tools.staticdir.root': os.path.abspath(os.getcwd()),
                   'tools.template.template': 'views/index.html',
                   'tools.encode.on': False},
             '/static': {'tools.staticdir.on': True,
                         'tools.staticdir.dir': './public'},
             '/execute': {'tools.template.on': True,
                          'tools.template.template': 'views/execute.html',
                          'tools.encode.on': False},
             '/state': {'tools.template.on': True,
                        'tools.template.template': 'views/state.html',
                        'tools.encode.on': False},
             '/screenshot': {'tools.template.on': True,
                             'tools.template.template': 'views/screenshot.html',
                             'tools.encode.on': False},
             '/terminal': {'tools.template.on': True,
                           'tools.template.template': 'views/terminal.html',
                           'tools.encode.on': False},
             '/start_vm': {'tools.template.on': True,
                           'tools.template.template': 'views/start_vm.html',
                           'tools.encode.on': False},
             '/login': {'tools.template.on': True,
                        'tools.template.template': 'views/login.html',
                        'tools.encode.on': False}}

    cherrypy.quickstart(WebApp(), '', conf2)
