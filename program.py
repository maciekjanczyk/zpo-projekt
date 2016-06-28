import cherrypy
import virtualbox
import os
import json
import sqlite3
import hashlib

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
            # cherrypy.session['machine'] = self.vbox.find_machine(machine_name)
            machine = self.vbox.find_machine(machine_name)
            # cherrypy.session['session'] = virtualbox.Session()
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
        with open('./public/screenshot.png', 'wb') as f:
            f.write(png)
        return json.dumps({'furl': '/static/screenshot.png'})

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
    def state(self):
        try:
            if not bool(cherrypy.session['logged']):
                return json.dumps({'status': 'You are not logged in.'})
        except KeyError:
            return json.dumps({'status': 'You are not logged in.'})
        machine = cherrypy.session['machine']
        session = cherrypy.session['session']
        return {"name": str(machine.name), "cpu": str(machine.get_cpu_status(0)), "state": str(session.state)}

    @cherrypy.expose
    def new_machine(self, distribution, name):
        try:
            if not bool(cherrypy.session['logged']):
                return json.dumps({'status': 'You are not logged in.'})
        except KeyError:
            return json.dumps({'status': 'You are not logged in.'})
        try:
            new_machine = self.vbox.create_machine('', name, [], "Linux", '')
            src_machine = self.vbox.find_machine(distribution)
            src_machine.clone_to(new_machine, virtualbox.library.CloneMode(1), [])
            self.vbox.register_machine(new_machine)
        except Exception:
            return json.dumps({'state': 'Failure.'})
        return json.dumps({'state': 'Ok.'})

    @cherrypy.expose
    def shutdown_vm(self, name):
        try:
            if not bool(cherrypy.session['logged']):
                return json.dumps({'status': 'You are not logged in.'})
        except KeyError:
            return json.dumps({'status': 'You are not logged in.'})
        kv = self.return_mach_sess_by_name(cherrypy.session['logged'], name)
        if kv == None:
            return json.dumps({'state': 'Failure.'})
        sess = kv['session']
        try:
            sess.console.power_down()
        except virtualbox.library.VBoxErrorInvalidVmState:
            return json.dumps({'state': 'Failure.'})
        self.machines[cherrypy.session['logged']].remove(kv)
        return json.dumps({'state': 'Ok.'})

    @cherrypy.expose
    def delete_machine(self, name):
        try:
            if not bool(cherrypy.session['logged']):
                return json.dumps({'status': 'You are not logged in.'})
        except KeyError:
            return json.dumps({'status': 'You are not logged in.'})
        machine = None
        for m in self.vbox.machines:
            if m.name == name:
                machine = m
                break
        try:
            machine.remove(True)
        except Exception:
            return json.dumps({'state': 'Failure.'})
        return json.dumps({'state': 'Ok.'})


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
                           'tools.encode.on': False}}
    cherrypy.quickstart(WebApp(), '', conf2)
