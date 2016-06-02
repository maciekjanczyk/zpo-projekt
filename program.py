import cherrypy
import virtualbox
import vboxapi


class WebApp(object):
    def __init__(self):
        self.vbox = virtualbox.VirtualBox()
        #@type self.session: virtualbox.library.ISession
        #self.session = None
        #@type self.machine: virtualbox.library.IMachine
        #self.machine = None
        #@type self.progress: virtualbox.library.IProgress
        #self.progress = None
        #@type self.gsession: virtualbox.library.IGuestSession
        #self.gsession = None

    @cherrypy.expose
    def index(self):
        return "Witam!"

    @cherrypy.expose
    def secret(self):
        return "Secret!"

    @cherrypy.expose
    def witaj(self, imie=''):
        if imie != '':
            return "Witaj " + imie + "!"
        else:
            return "Nie podales imienia!"

    @cherrypy.expose
    def list_vms(self):
        ret = "<b>Machine list:</b><br/><ul>"
        for vm in self.vbox.machines:
            ret += "<li>" + vm.name + "</li>"
        return ret + "</ul>"

    @cherrypy.expose
    def start_vm(self, machine_name=''):
        if machine_name == '':
            return "Type machine name!"
        self.machine = self.vbox.find_machine(machine_name)
        self.session = virtualbox.Session()
        self.progress = self.machine.launch_vm_process(self.session, 'gui', '')
        while not str(self.session.state) == "Locked":
            continue
        return "Ok."

    @cherrypy.expose
    def state(self):
        ret = ''
        ret += str(self.machine.name) + "<br/>"
        ret += "Cpu status: " + str(self.machine.get_cpu_status(0)) + "<br/>"
        ret += "State: " + str(self.session.state) + "<br/>"
        return ret

    @cherrypy.expose
    def execute(self, cmd=''):
        self.gsession = self.session.console.guest.create_session('root', 'centos')
        cmds=cmd.split(' ')
        nap2="\'" + cmd + "\'"
        #p, out, err = self.gsession.execute(cmds[0], cmds[1:])
        cmds2=[]
        cmds2.append("-c")
        for s in cmds:
            cmds2.append(s)
        p, out, err = self.gsession.execute("/bin/bash", cmds2)
        self.gsession.close()
        ret="<html><head></head><body><pre>"
        ret+=str(out)+"</pre></body></html>"
        return ret

    @cherrypy.expose
    def screenshot(self):
        h, w, _, _, _, _ = self.session.console.display.get_screen_resolution(0)
        png = self.session.console.display.take_screen_shot_to_array(0, h, w, virtualbox.library.BitmapFormat.p)
        with open('screenshot.jpg', 'wb') as f:
            f.write(png)
        return '<html><body><img src="screenshot.jpg"></body></html>'

if __name__ == '__main__':
    conf = {
        'server.socket_port': 8081
    }
    cherrypy.config.update(conf)
    cherrypy.quickstart(WebApp())
