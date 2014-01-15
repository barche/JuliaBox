import docker
import calendar
import time
import sys
import os

dckr = docker.Client()

f = open("conf/tornado.conf")
cfg = eval(f.read())
f.close()

if os.path.isfile("conf/tornado.user"):
    f = open("conf/tornado.user")
    ucfg = eval(f.read())
    f.close()
    
    cfg.update(ucfg)


def esc_sessname(s):
    return s.replace("@", "_at_").replace(".", "_")

cfg["admin_sessnames"]=[]
for ad in cfg["admin_users"]:
    cfg["admin_sessnames"].append(esc_sessname(ad))

cfg["protected_docknames"]=[]
for ps in cfg["protected_sessions"]:
    cfg["protected_docknames"].append("/" + esc_sessname(ps))


# Track the last ping time of active sessions
map_dockname_ping = {}



def kill_and_remove_id(Id):
    c = dckr.inspect_container(id)
    dckr.kill(Id)
    dckr.remove_container(Id)

    if ("Name" in c) and (c["Name"] != None):
        map_dockname_ping.pop(c["Name"], None)
    
    
def kill_and_remove(c):
    dckr.kill(c["Id"])
    dckr.remove_container(c["Id"])
    
    if ("Names" in c) and (c["Names"] != None):
        map_dockname_ping.pop(c["Names"][0], None)
    
    

def get_num_active_containers():
    return len(dckr.containers(all=False))



def isactive(c):
    if ("Names" not in c) or (c["Names"] == None) or ("Ports" not in c) or (c["Ports"] == None):
        return False
    else:
        return True

# remove container if 
# inactive and greater than inactive timeout(if found) or expiry time
# active, not protected and inactive for more than inactive timeout 
# active, not protected and running for more than expiry time
# active and protected, leave as is.
# If active, but not in active_docknames, drop it.


def terminate_expired_containers():
    tnow = calendar.timegm(time.gmtime())
    if cfg["expire"] == 0:
        # nobody is expired
        expire_before = 0
    else:
        expire_before = tnow - cfg["expire"]
        
    jsonobj = dckr.containers(all=True)
    for c in jsonobj:
        if isactive(c):
            cn = c["Names"][0]
            if cn in cfg["protected_docknames"]:
                continue
            
            elif cn not in map_dockname_ping:
                kill_and_remove(c)
                
            elif (c["Created"] < expire_before):
                kill_and_remove(c)
                
            elif (cn in map_dockname_ping) and (map_dockname_ping[cn] < (tnow - cfg["inactivity_timeout"])):
                kill_and_remove(c)
        else:
            if ("Names" in c) and (c["Names"] != None):
                kill_and_remove(c)
            
            elif (c["Created"] < expire_before) :
                kill_and_remove(c)
                 

def record_active_containers():
    for c in dckr.containers(all=True):
        if isactive(c):
            map_dockname_ping[c["Names"][0]] = calendar.timegm(time.gmtime())

def is_container(name, all=True):
    nname = "/" + unicode(name)
    
    for c in dckr.containers(all=all):
        if ("Names" in c) and (c["Names"] != None) and (c["Names"][0] == nname) :
            return True, c
        
    return False, None


def launch_container(name, clear_old_sess, c):
    if c == None:
        iscont, c = is_container(name)
    else:
        iscont = True
        
    id = ""
    
    # kill the container 
    # if it exists and clear_old_sess
    # if it exists and is not in a running state
    
    if iscont and (("Ports" not in c) or (c["Ports"] == None)):
        clear_old_sess = True
    
    if (iscont and clear_old_sess):
        kill_and_remove(c)
    
    if ((not iscont) or clear_old_sess) :
        id = create_new_container(name)
    else:
        id = c["Id"]
    
    uplport, ipnbport = get_container_ports_by_id(id)
    if ipnbport == None :
      return None, None, None
    
    return id, uplport, ipnbport

def get_container_id(name):
    iscont, c = is_container(name)
    if iscont:
        return c.Id, c
    else:
        return None, None


def get_container_ports_by_id(id):
    jsonobj = dckr.inspect_container(id)
    
    # get the mapped ports
    return jsonobj["NetworkSettings"]["Ports"]["8000/tcp"][0]["HostPort"], jsonobj["NetworkSettings"]["Ports"]["8998/tcp"][0]["HostPort"]

def create_new_container(name):
    jsonobj = dckr.create_container("ijulia", detach=True, mem_limit=cfg["mem_limit"], ports=[8998, 8000], name=name)
    id = jsonobj["Id"]
    dckr.start(id, port_bindings={8998: None, 8000: None})
    map_dockname_ping["/" + name] = calendar.timegm(time.gmtime())
    
    return id


def get_container_ports_by_name(name):
    iscont, c = is_container(name)
    
    if not iscont:
        raise Exception ("ERROR: Could not find session : " + name)
    
    return get_container_ports_by_id(c["Id"])


