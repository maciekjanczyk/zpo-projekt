import cherrypy
import virtualbox
import os
import json


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
        return { "status": "Ok" }

    @cherrypy.expose
    def state(self):
        return { "name": "ssss", "cpu": "cccc", "state": "ssss" }

    @cherrypy.expose
    def execute(self, cmd=''):
        return "EEEE"

    @cherrypy.expose
    def screenshot(self):
        return { 'fname': '/static/screenshot.png' }

    @cherrypy.expose
    def terminal(self):
        return { 'msg': '' }


class RestAPI(object):
    def __init__(self):
        self.vbox = virtualbox.VirtualBox()

    @cherrypy.expose
    def index(self):
        return "API"

    @cherrypy.expose
    def json_test(self):
        return json.dumps({ "pole1": "ok", "pole2": "ok2" })

    @cherrypy.expose
    def start_vm(self, machine_name=''):
        if machine_name == '':
            return json.dumps({"status": "Invalid machine name"})
        try:
            cherrypy.session['machine'] = self.vbox.find_machine(machine_name)
            cherrypy.session['session'] = virtualbox.Session()
            cherrypy.session['progress'] = cherrypy.session['machine'].launch_vm_process(cherrypy.session['session'], 'gui', '')
            while not str(cherrypy.session['session'].state) == "Locked":
                continue
        except Exception:
            return json.dumps({"status": "Failure"})
        return json.dumps({"status": "Ok"})

    @cherrypy.expose
    def screenshot(self):
        h, w, _, _, _, _ = cherrypy.session['session'].console.display.get_screen_resolution(0)
        png = cherrypy.session['session'].console.display.take_screen_shot_to_array(0, h, w,
                                                                                    virtualbox.library.BitmapFormat.png)
        with open('./public/screenshot.png', 'wb') as f:
            f.write(png)
        return json.dumps({'furl': '/static/screenshot.png'})

    @cherrypy.expose
    def execute(self, cmd=''):
        gsession = cherrypy.session['session'].console.guest.create_session('root', 'centos')
        cmds2 = []
        cmds2.append("-c")
        cmds2.append(cmd)
        p, out, err = gsession.execute("/bin/bash", cmds2)
        gsession.close()
        return json.dumps({'out': str(out), 'err': str(err)})

    @cherrypy.expose
    def list_vms(self):
        ret = ""
        for vm in self.vbox.machines:
            ret += vm.name + ";"
        return json.dumps({'list': ret})

    @cherrypy.expose
    def state(self):
        machine = cherrypy.session['machine']
        session = cherrypy.session['session']
        return {"name": str(machine.name), "cpu": str(machine.get_cpu_status(0)), "state": str(session.state)}

    @cherrypy.expose
    def new_machine(self, distribution, name):
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
        sess = None
        try:
            sess = cherrypy.session['session']
        except Exception:
            return json.dumps({'state': 'Failure.'})
        try:
            sess.console.power_down()
        except virtualbox.library.VBoxErrorInvalidVmState:
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
