"""Main module."""
from flask import Flask, request, render_template, jsonify
from flask_sqlalchemy import SQLAlchemy
import os
app = Flask(__name__)


uri = os.getenv("DATABASE_URL")
if uri and uri.startswith("postgres://"):
    uri = uri.replace("postgres://", "postgresql://", 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = uri
else:
    app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://postgres:freezie123@localhost:5432/ecommerce"

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# should create a 1 to many relationship (1 order with different items)
# one
class cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey("items.id"), nullable=False)
    item = db.relationship(
        "Items", backref=db.backref('cart', lazy=True)
    )

    def __repr__(self):
        return f"<cart %d>" % self.id
# db.relationship first argument is the table being referenced, backref(similar to adding another column to the items module) is the self table (ecommerce orders), and lazy defines how the data is loaded.
# many
class Items(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), nullable=False)
    category = db.Column(db.String(30), nullable=False)
    sub_category = db.Column(db.String(30), nullable=False)
    price = db.Column(db.Integer, nullable=False, default=0)
    description = db.Column(db.Text, nullable=False)

    def __repr__(self):
        return f"<item %s price %d  description %s>" % (self.name, self.price, self.description)


db.create_all()

@app.route("/home")
def home():
    return render_template("home.html", Items=Items.query.order_by(Items.name).all())

@app.route("/home/category/<string:section>")
def category(section):
    return render_template("home.html", Items=Items.query.filter_by(category=section).all())

@app.route("/home/item/<string:item>")
def item(item):
    return render_template("home.html", Items=Items.query.filter_by(name=item).all())

@app.route("/home/orders")
def orders():
    order = cart.query.all()
    if not order:
        return jsonify({"message": "you do not have any item in your cart"})
    return render_template("home.html", cart=cart.query.filter_by(cart.id).all())

@app.route("/home/item", methods=["POST"])  # ALL SEt
def create_item():
    item_req = request.get_json()
    for item in item_req:  # in cases of multiple items to be added to DB
        item_data = {"name": item.get("name"),
                     "category": item.get("category"),
                     "sub_category": item.get("sub_category"),
                     "price": item.get("price"),
                     "description": item.get("description")
                     }
        new_item = Items(**item_data)
        db.session.add(new_item)
        db.session.commit()
    return jsonify({"message": "new item successfully added"}), 201

@app.route("/home/orders", methods=["POST"])
def create_order():
    orders_req = request.get_json()
    for order in orders_req:  # in cases of multiple orders to be added to cart!
        order_data = {"item_id": order.get("item_id")}
        new_order = cart(**order_data)
        db.session.add(new_order)
        db.session.commit()
    return jsonify({"message": "new item successfully added to your cart!"}), 201

@app.route("/home/item", methods=["PATCH"])  # ALL SET
def update_item():
    update_req = request.get_json()  # loads the user input
    update_id = update_req.get("id")  # fetch the data in id(because all items have uniques ID) from user input
    update_data = Items.query.get_or_404(update_id, description="The item entered doesn't exist")  # now you either have the item you want to query or you get a 404 error
    for key, value in update_req.items():
        setattr(update_data, key, value)  # fetches an attribute and changes the value
        db.session.commit()
    return jsonify({"message": "item successfully Updated"})

@app.route("/home/orders", methods=["PATCH"])
def update_order():
    order_req = request.get_json()
    order_id = order_req.get("id")
    update_data = cart.query.get_or_404(order_id, description="The item entered doesn't exist")
    for key, value in order_req.items():
        setattr(update_data, key, value)
        db.session.commit()
    return jsonify({"message": "item successfully Updated"})

@app.route("/home/item", methods=["DELETE"])  # ALL SET
def delete_item():
    delete_req = request.get_json()  # loads the user input
    delete_id = delete_req.get("id")  # fetch the data in id from user input
    delete_data = Items.query.get_or_404(delete_id, description="The item entered doesn't exist")
    db.session.delete(delete_data)
    db.session.commit()
    return jsonify({"message": "item successfully deleted"})

@app.route("/home/orders", methods=["DELETE"])
def delete_order():
    order = request.get_json()
    order_id = order.get("id")
    delete_ord = cart.query.get_or_404(order_id, description="You don't have this order in your Cart!")
    db.session.delete(delete_ord)
    db.session.commit()
    return jsonify({"message": "item successfully been removed from your Cart!"})


if __name__ == '__main__':
    app.run(debug=True)
