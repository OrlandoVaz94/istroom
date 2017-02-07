"""`main` is the top level module for your Bottle application."""

# import the Bottle framework
from bottle import Bottle, debug, get, BaseRequest, run, template, request, post, delete
from google.appengine.ext import ndb

import urllib
import json

# Create the Bottle WSGI application.
bottle = Bottle()
debug(True)

# Note: We don't need to call run() since our application is embedded within
# the App Engine WSGI application server.

class Students(ndb.Model):
    id = ndb.StringProperty()

class Rooms(ndb.Model):
    name = ndb.StringProperty()
    id = ndb.IntegerProperty()

class Check(ndb.Model):
    key_student = ndb.IntegerProperty()
    key_room = ndb.IntegerProperty()


# Open template index.html
@bottle.get('/')
def openpage():
    return template('index.html')


# Open template admin_introd.html
@bottle.get('/adminintro/<user>')
def openpage(user):
    if user == '0':
        return template('admin_introd.html', url = user)
    else:
        return template('No permission: user {{user}}', user = user)


# Open template admin_remove.html
@bottle.get('/adminremove/<user>')
def openpage(user):
    if user == '0':
        return template('admin_remove.html', url = user)
    else:
        return template('No permission: user {{user}}', user = user)


# Open template admin.html
@bottle.get('/admin/<user>')
def openpage(user):
    if user == '0':
        return template('admin.html', url = user)
    else:
        return template('No permission: user {{user}}', user = user)


# Open template checkin.html
@bottle.get('/checkinout/<user>')
def openpage(user):
    student = ndb.Key('Students',eval(user)).get()
    if student:
        return template('checkinout.html', url = user)
    else:
        return template('No permission: user {{user}}', user = user)


# Open template checkin.html
@bottle.get('/searchfriends/<user>')
def openpage(user):
    student = ndb.Key('Students',eval(user)).get()
    if student:
        return template('searchfriends.html', url = user)
    else:
        return template('No permission: user {{user}}', user = user)


# Open template user.html
@bottle.get('/user/<user>')
def openpage(user):
    student = ndb.Key('Students',eval(user)).get()
    if student:
        return template('user.html', url = user)
    else:
        return template('No permission: user {{user}}', user = user)


# Open template login.html
@bottle.get('/login')
def login():
    return template('login.html')	


# When a user wants to login
@bottle.post('/login')
def do_login():
    username = request.forms.get('username')
    if username != '':
        if username == 'admin':
            return template('admin.html', url = '0' )
            
        else:
            students = Students.query()
            for student in students:
                if student.id == username:
                    return template('user.html', url = str(student.key.id()))

            s = Students(id = username)
            key = s.put()
            return template('user.html', url = str(s.key.id()))


# When a user wants to logout
@bottle.route('/logout/<key_student>')
def do_logout(key_student):
    if key_student == '0':
        return template('exit.html')
    else:

        student = ndb.Key('Students',eval(key_student)).get()
        if student:        
            check = Check.query()
            rooms = Rooms.query()
            for c in check:
                # Check if this student had checked in 
                if str(c.key_student) == key_student:
                    c.key.delete()
                    break

            student.key.delete()
	
            return template('exit.html')
        else:
            return template('No permission: user {{user}}', user = key_student)


# Admin adds rooms
@bottle.route('/addroom/<user>/<id_room>')
def add_room(user, id_room):
    if user == '0':
        rooms = Rooms.query()

        for r in rooms:
            if r.id == int(id_room):
                state = 'Room %s whose ID is %s was already added' %(r.name, r.id)
                info = {'state': state}
                return json.dumps(info)

        campus_url = 'https://fenix.tecnico.ulisboa.pt/api/fenix/v1/spaces'
        room_url = campus_url + "/" + id_room
        json_room = urllib.urlopen(room_url)
        data = json.loads(json_room.read())
        id = data['id']
        r = Rooms(name = data['name'], id = int(id))
        key = r.put()
        state = 'The room %s whose ID is %s is now available for the students' %(data['name'], data['id'])
        info = {'state': state}
        return json.dumps(info)

    else:
        return template('No permission: user {{user}}', user = user)


# Admin deletes rooms
@bottle.route('/delroom/<user>/<id_room>')
def delroom(user, id_room):
    if user == '0':
        room = Rooms.query()
        check = Check.query()
        for r in room:
            if r.id == int(id_room):
                for c in check:
                    if c.key_room == r.key.id():
                        c.key.delete()
                r.key.delete()
                state = 'The room whose ID is %s is not available for the students' %(id_room)
                info = {'state': state}
                return json.dumps(info)
        return template('Room not found: room {{id_room}}', id_room = id_room)
    else:
        return template('No permission: user {{user}}', user = user)


# Each user needs to check in to be able to be in a certain room
@bottle.route('/checkin/<key_student>/<id_room>')
def do_checkin(key_student, id_room):
    student = ndb.Key('Students',eval(key_student)).get()
    aux = 0
    if student:
        rooms = Rooms.query()
        for r in rooms:
            if r.id == int(id_room):
                current_room = r
                aux = 1
                break

        if aux == 0:
            state = 'Room whose ID is %s is not available' %(id_room)
            info = {'state': state}
            return json.dumps(info)

        check = Check.query()
        for c in check:
            if str(c.key_student) == key_student:
                room = ndb.Key('Rooms',c.key_room).get()
                if room.id == int(id_room):
                    state = 'You are already checked in room: %s' %(room.name)
                    info = {'state': state}
                else:
                    c.key.delete()
                    newcheck = Check(key_student = int(key_student), key_room = current_room.key.id())
                    key = newcheck.put()
                    state = 'You are now checked in room: %s' %(current_room.name)
                    info = {'state': state}
                return json.dumps(info)

        newcheck = Check(key_student = int(key_student), key_room = current_room.key.id())
        key = newcheck.put()
        state = 'You are now checked in room: %s' %(current_room.name)
        info = {'state': state}
        return json.dumps(info)

    else:
        return template('No permission: user {{user}}', user = key_student)


# A user searches for someone
@bottle.route('/searchperson/<key_student>/<user_to_search>')
def search_person(key_student, user_to_search):
    student = ndb.Key('Students',eval(key_student)).get()
    if student:
        people = Students.query()
        checks = Check.query()

        for s in people:
            if s.id == user_to_search:
                for c in checks:
                    if c.key_student == s.key.id():
                        room = ndb.Key('Rooms',c.key_room).get()
                        state = 'The person whose ID is %s is in room %s' %(user_to_search,room.name)
                        info = {'state': state}
                        return info
        state = 'The person whose ID is %s is not checked in any room' %(user_to_search)
        info = {'state': state}
        return info
    else:
        return template('No permission: user {{user}}', user = key_student)


# Gives back a JSON with all the available rooms
@bottle.route('/availablerooms')
def verify():
    response = []
    room = Rooms.query()
    for r in room:
        response.append({'key_id': str(r.key.id()), 'name' : str(r.name), 'id' : str(r.id)})
    return json.dumps(response)


# Returns the information about the campus
@bottle.get('/campus')
def getcampus():
    campus_url = 'https://fenix.tecnico.ulisboa.pt/api/fenix/v1/spaces'
    json_campus = urllib.urlopen(campus_url)
    return json_campus


# Returns the information about every place in each campus
@bottle.get('/place/<query_building>')
def getplace(query_building):
    campus_url = 'https://fenix.tecnico.ulisboa.pt/api/fenix/v1/spaces'
    place_url = campus_url + "/" + query_building
    json_place = urllib.urlopen(place_url)	
    return json_place


	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	

@bottle.route('/deletestudent')
def delete():
    student = Students.query()
    for s in student:
        s.key.delete()
    return 'Done'


@bottle.route('/deletesalas')
def delete():
    room = Rooms.query()
    for r in room:
        r.key.delete()
    return 'Done'

@bottle.route('/deletechecks')
def delete():
    check = Check.query()
    for c in check:
        c.key.delete()
    return 'Done'

@bottle.route('/verificarstudent')
def verify():
    ret = ""
    student = Students.query()
    for s in student:
        ret += str(s.key.id()) + "     " + str(s.id) + "<br>"
    return ret

@bottle.route('/verificarchecks')
def verify():
    ret = ""
    check = Check.query()
    for c in check:
        ret += str(c.key.id()) + "     " + str(c.key_student) + "     " + str(c.key_room) + "<br>"
    return ret


@bottle.route('/verificarsalastexto')
def verify():
    ret = ""
    room = Rooms.query()
    for r in room:
        ret += str(r.key.id()) + "     " + str(r.name) + "     " + str(r.id) + "<br>"
    return ret


# Define an handler for 404 errors.
@bottle.error(404)
def error_404(error):
    """Return a custom 404 error."""
    return 'Sorry, Nothing at this URL.'
