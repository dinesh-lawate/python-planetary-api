from flask import Flask, jsonify, Response, request, json
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, Float
import os
from flask_marshmallow import Marshmallow
from flask_jwt_extended import JWTManager, jwt_required, create_access_token
from flask_mail import Mail, Message

app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'planets.db')
app.config['JWT_SECRET_KEY'] = 'super-secret'
app.config['MAIL_SERVER'] = 'smtp.mailtrap.io'
app.config['MAIL_PORT'] = 2525
app.config['MAIL_USERNAME'] = os.environ['MAIL_USERNAME']
app.config['MAIL_PASSWORD'] = os.environ['MAIL_PASSWORD']
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False

db = SQLAlchemy(app)
ma = Marshmallow(app)
jwt = JWTManager(app)
mail = Mail(app)


@app.cli.command('db_create')
def db_create():
    db.create_all()
    print('Database created!')


@app.cli.command('db_drop')
def db_drop():
    db.drop_all()
    print('Database dropped!')


@app.cli.command('db_seed')
def db_seed():
    mercury = Planet(planet_name='Mercury',
                     planet_type='Class D',
                     home_star='Sol',
                     mass=3.258e23,
                     radius=1516,
                     distance=35.98e6)

    venus = Planet(planet_name='Venus',
                   planet_type='Class k',
                   home_star='Sol',
                   mass=4.258e23,
                   radius=3516,
                   distance=67.98e6)

    earth = Planet(planet_name='Earth',
                   planet_type='Class M',
                   home_star='Sol',
                   mass=5.258e23,
                   radius=3916,
                   distance=92.98e6)

    db.session.add(mercury)
    db.session.add(venus)
    db.session.add(earth)

    test_user = User(first_name='Dinesh',
                     last_name='Lawate',
                     email='test@test.com',
                     password='P@ssw0rd')

    db.session.add(test_user)
    db.session.commit()
    print('Database seeded!')


@app.route('/')
def hello_world():
    return 'Hello World!'


@app.route('/super_simple')
def super_simple():
    return jsonify({'key': 1})


@app.route('/raw_response')
def raw_response():
    res = Response(json.dumps({'key': 1}), 200)
    return res


@app.route('/parameters')
def parameters():
    name = request.args.get('name')
    age = int(request.args.get('age'))
    return json.dumps({'name': name, 'age': age}), 200


@app.route('/url_variables/<string:name>/<int:age>')
def url_variables(name: str, age: int):
    return json.dumps({'name': name, 'age': age}), 200


@app.route('/planets', methods=['GET'])
def get_planets():
    planet_lists = Planet.query.all()
    result = planets_schema.dump(planet_lists)
    return jsonify(result)


@app.route('/register', methods=['POST'])
def register():
    email = request.form['email']
    test = User.query.filter_by(email=email).first()
    if test:
        return jsonify(message='That email already exists'), 409
    else:
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        password = request.form['password']
        user = User(first_name=first_name, last_name=last_name, email=email, password=password)
        db.session.add(user)
        db.session.commit()
        return jsonify(message='User created successfully!'), 201


@app.route('/login', methods=['POST'])
def login():
    if request.is_json:
        email = request.json['email']
        password = request.json['password']
    else:
        email = request.form['email']
        password = request.form['password']

    test = User.query.filter_by(email=email, password=password).first()

    if test:
        access_token = create_access_token(identity=email)
        return jsonify(message='Login succeeded!', access_token=access_token)
    else:
        return jsonify(message='Invalid email or password'), 401


@app.route('/retrieve_password/<string:email>', methods=['GET'])
def retrieve_password(email: str):
    user = User.query.filter_by(email=email).first()
    if user:
        msg = Message(f'Your planetary API password is {user.password}',
                      sender='admin@planetary-api.com',
                      recipients=[email])
        mail.send(msg)
        return jsonify(message=f'Password sent to {email}')
    else:
        return jsonify(message=f"That email doesn't exists"), 401


@app.route('/planet_details/<int:planet_id>', methods=['GET'])
def planet_details(planet_id: int):
    planet = Planet.query.filter_by(planet_id=planet_id).first()
    if planet:
        result = planet_schema.dumps(planet)
        return jsonify(result)
    else:
        return jsonify('That planet does not exits'), 404


@app.route('/add_planet', methods=['POST'])
@jwt_required()
def add_planet():
    planet_name = request.json['planet_name']
    test = Planet.query.filter_by(planet_name=planet_name).first()
    if test:
        return jsonify('That planet already exists'), 409
    else:
        planet_type = request.json['planet_type']
        home_star = request.json['home_star']
        mass = float(request.json['mass'])
        radius = float(request.json['radius'])
        distance = float(request.json['distance'])

        new_planet = Planet(planet_name=planet_name,
                            planet_type=planet_type,
                            home_star=home_star,
                            mass=mass,
                            radius=radius,
                            distance=distance)
        db.session.add(new_planet)
        db.session.commit()
        return jsonify(message='You added a planet!'), 201


# database models
class User(db.Model):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    first_name = Column(String)
    last_name = Column(String)
    email = Column(String, unique=True)
    password = Column(String)


class Planet(db.Model):
    __tablename__ = 'planets'
    planet_id = Column(Integer, primary_key=True)
    planet_name = Column(String)
    planet_type = Column(String)
    home_star = Column(String)
    mass = Column(Float)
    radius = Column(Float)
    distance = Column(Float)


class PlanetSchema(ma.Schema):
    class Meta:
        # Fields to expose
        fields = ("planet_id", "planet_name", "planet_type", "home_star", "mass", "radius", "distance")


planet_schema = PlanetSchema()
planets_schema = PlanetSchema(many=True)

if __name__ == '__main__':
    app.run(debug=True)
