from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from marshmallow import ValidationError
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from flask_marshmallow import Marshmallow
from sqlalchemy import Table, Column, Integer, String, ForeignKey, Float, UniqueConstraint, select


# Initialization
app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:aRduino2234%21%40%23%24@localhost/ecommerce_api_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['WTF_CSRF_ENABLED'] = False # Disable CSRF protection to stop 403 in postman

# Base Model

class Base(DeclarativeBase):
    include_fk = True

db = SQLAlchemy(model_class=Base)
db.init_app(app)
ma = Marshmallow(app)

# Association Tables

order_product = Table('order_product', Base.metadata,
    Column('order_id', Integer, ForeignKey('order.id'), primary_key=True),
    Column('product_id', Integer, ForeignKey('product.id'), primary_key=True),
    UniqueConstraint('order_id', 'product_id', name='uix_order_product')
)

# Model

class User(Base):
    __tablename__ = 'user'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    address: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    orders: Mapped[list['Order']] = relationship('Order', back_populates='user')
    

class Order(Base):
    __tablename__ = 'order'
    id: Mapped[int] = mapped_column(primary_key=True)
    order_date: Mapped[str] = mapped_column(String(100), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey('user.id'), nullable=False)
    products: Mapped[list['Product']] = relationship('Product', secondary=order_product, back_populates='orders')
    user: Mapped['User'] = relationship('User', back_populates='orders')

class Product(Base):
    __tablename__ = 'product'
    id: Mapped[int] = mapped_column(primary_key=True)
    product_name: Mapped[str] = mapped_column(String(100), nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    orders: Mapped[list['Order']] = relationship('Order', secondary=order_product, back_populates='products')
    

# Schemas

class UserSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = User
        
class UsersSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = User
        many = True

class ProductsSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Product

class OrdersSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Order
        

user_schema = UserSchema()
users_schema = UsersSchema(many=True)
product_schema = ProductsSchema(many=True)
order_schema = OrdersSchema(many=True)


# CRUD Endpoints

#=================User=================

# CREATE

@app.route('/users', methods=['POST'])
def create_user():
    if not request.is_json or request.json is None:
        return jsonify({'error': 'No JSON data provided'}), 400
    try:
        user_data = user_schema.load(request.json)
    except ValidationError as err:
        return jsonify({'error': err.messages}), 400
    
    new_user = User(name=user_data['name'], email=user_data['email'], address=user_data['address'])
    db.session.add(new_user)
    db.session.commit()
    
    return user_schema.jsonify(new_user), 201

# READ

@app.route('/users', methods=['GET'])
def get_users():
    query = select(User)
    users = db.session.execute(query).scalars().all()

    return users_schema.jsonify(users), 200

@app.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    query = select(User).where(User.id == user_id)
    user = db.session.execute(query).scalars().first()
    if not user:
        return jsonify({'error': 'User not found'}), 404

    return user_schema.jsonify(user), 200

# UPDATE
@app.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    user = db.session.get(User, user_id)
    if not request.is_json or request.json is None:
        return jsonify({'error': 'No JSON data provided'}), 400
    if not user:
        return jsonify({"message": "Invalid user id"}), 400
    try:
        user_data = user_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400
    
    user.name = user_data['name']
    user.email = user_data['email']

    db.session.commit()
    return user_schema.jsonify(user), 200

# DELETE

@app.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"message": "Invalid user id"}), 400
    
    db.session.delete(user)
    db.session.commit()
    
    return jsonify({"message": "User deleted successfully"}), 200
    

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True) 