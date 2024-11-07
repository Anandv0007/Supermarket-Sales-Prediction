from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from datetime import date
import pickle
import xgboost




app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sales_management.db'  # SQLite database
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

app.secret_key = 'salesmanagementsystem'

# login_manager = LoginManager()
# login_manager.init_app(app)

# Define the Outlets model
class Outlet(db.Model):
    outlet_id = db.Column(db.String(50), primary_key=True)  # Primary Key
    outlet_location_type = db.Column(db.String(100), nullable=False)
    outlet_size = db.Column(db.String(50), nullable=False)
    outlet_type = db.Column(db.String(50), nullable=False)
    outlet_year = db.Column(db.Integer, nullable=False)  # Year the outlet was established


# Define the Members model
class Member(db.Model):
    username = db.Column(db.String(50), primary_key=True)  # Primary Key
    password = db.Column(db.String(200), nullable=False)
    outlet_id = db.Column(db.Integer, db.ForeignKey('outlet.outlet_id'), nullable=False)  # Foreign Key referencing Outlets
    kind = db.Column(db.String(20), nullable=False)  # Membership type or other info

    

# Define the Sale model
class Sale(db.Model):
    sales_id = db.Column(db.Integer, primary_key=True)  # Primary Key
    item_id = db.Column(db.Integer, nullable=False)  # Item ID related to the sale
    outlet_id = db.Column(db.Integer, db.ForeignKey('outlet.outlet_id'), nullable=False)  # Foreign Key referencing Outlets
    date = db.Column(db.Date, nullable=False, default=date.today)  # Date of the sale
    sales = db.Column(db.Float, nullable=False)  # Amount of sales

fat_mapping = {
        'Low Fat': 0,
        'Regular':1,

    }
item_type_mapping = {
        'Baking Goods':0,
        'Bread':1,
        'Breakfast':2,
        'Canned':3,
        'Diary':4,
        'Frozen Foods':5,
        'Fruits And Vegetables':6,
        'Hard Drinks':7,
        'Health And Hygine':8,
        'Households':9,
        'Meat':10,
        'Others':11,
        'Seafood':12,
        'Snack Foods':13,
        'Soft Drinks':14,
        'Starchy Foods':15
    }

outlet_size_mapping = {
        'High':0,
        'Medium':1,
        'Small':2

    }
outlet_location_type_mapping = {
        'Tier 1':0,
        'Tier 2':1,
        'Tier 3':2
    }
outlet_type_mapping = {
        'Grocery Store':0,
        'Supermarket Type1':1,
        'Supermarket Type2':2,
        'Supermarket Type3':3,
    }
# Create the database tables
with app.app_context():
    db.create_all()

with open('model.pkl','rb') as model_file:
    model = pickle.load(model_file)

    # # Save model using the current version of XGBoost
    # model.save_model('xgboost_model.json')

    # # Later, load it back
    # model = xgboost.Booster()
    # model.load_model('xgboost_model.json')


#@login_manager.user_loader
def load_user(user_id):
    return Member.query.get(int(user_id))  # Assuming 'Member' is your User model

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/admin')
def admin():
    if 'username' in session and Member.query.filter_by(username=session['username']).first().kind == 'manager':
        return render_template('admin.html')  # Render the admin page
    else:
        return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Get the form data
        username = request.form['username']
        password = request.form['password']
        
        # Query the database for the member
        member = Member.query.filter_by(username=username, password=password).first()
        
        if member:
            # Check the kind of the member
            session['username'] = username
            if member.kind == 'manager':
                
                # Redirect to the admin page if they are a manager
                # session['username'] = member.username  # Set session
                return redirect(url_for('admin'))
            else:
                # Redirect to the salesperson page or other dashboard
                #   # Set session
                return redirect(url_for('salesperson_dashboard'))  # Change this to your salesperson page
        else:
            # Invalid login
            flash('Invalid username or password', 'danger')
    
    return render_template('login.html')


    #return render_template('login.html')




# @app.route('/promotion_list')
# def promotion_list():
#     return render_template('promotion_list.html')

# @app.route('/history')
# def history():
#     return render_template('history.html')

@app.route('/history', methods=['GET', 'POST'])
def history():
    # Ensure the user is logged in and is a manager
    if 'username' not in session:
        return redirect(url_for('login'))
    
    # Get the logged-in user's username
    username = session['username']
    
    # Fetch the manager's details
    manager = Member.query.filter_by(username=username).first()
    
    if not manager or manager.kind != 'manager':
        return redirect(url_for('login'))  # Redirect if not a manager

    # Fetch item_ids for the manager's outlet
    outlet_id = manager.outlet_id
    item_ids = Sale.query.with_entities(Sale.item_id).filter_by(outlet_id=outlet_id).distinct().all()

    selected_item_id = None
    sales_history = None

    if request.method == 'POST':
        # Get the selected item_id from the form
        selected_item_id = request.form.get('item_id')
        
        # Fetch all sales for the selected item_id at the manager's outlet
        sales_history = Sale.query.filter_by(outlet_id=outlet_id, item_id=selected_item_id).all()
    
    return render_template('history.html', item_ids=item_ids, sales_history=sales_history, selected_item_id=selected_item_id)



@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))


# @app.route('/add_salesperson', methods=['GET', 'POST'])
# def add_salesperson():
#     if request.method == 'POST':
#         # Get the form data
#         username = request.form['username']
#         password = request.form['password']
#         outlet_id = request.form['outlet_id']
        
#         # Create a new member (kind will be 'salesperson')
#         new_member = Member(username=username, password=password, outlet_id=outlet_id, kind='salesperson')
        
#         # Add to the database
#         db.session.add(new_member)
#         db.session.commit()
        
#         flash('Salesperson added successfully!', 'success')
#         return redirect(url_for('admin'))
    
#     # Fetch all outlets from the database for the dropdown
#     outlets = Outlet.query.all()
#     return render_template('add_salesperson.html', outlets=outlets)

@app.route('/add_salesperson', methods=['GET', 'POST'])
def add_salesperson():
    # Ensure the user is logged in and is a manager
    if 'username' not in session:
        return redirect(url_for('login'))
    
    # Get the logged-in user's username
    username = session['username']
    
    # Fetch the manager's details
    member = Member.query.filter_by(username=username).first()
    
    if not member or member.kind != 'manager':
        return redirect(url_for('login'))  # Redirect if not a manager
    
    if request.method == 'POST':
        # Get the form data
        username = request.form['username']
        password = request.form['password']
        
        # Auto-fill outlet_id from the logged-in manager
        outlet_id = member.outlet_id
        
        # Create a new member (kind will be 'salesperson')
        new_member = Member(username=username, password=password, outlet_id=outlet_id, kind='salesperson')
        
        # Add to the database
        db.session.add(new_member)
        db.session.commit()
        
        flash('Salesperson added successfully!', 'success')
        return redirect(url_for('admin'))
    
    # Fetch the manager's outlet_id for the form
    return render_template('add_salesperson.html', outlet_id=member.outlet_id)



@app.route('/predict_sales', methods=['GET', 'POST'])
def predict_sales():
    if request.method == 'POST':
        # Collect all form data
        form_data = {
            'date': request.form['date'],
            'item_id': request.form['item_id'],
            'item_weight': request.form['item_weight'],
            'item_fat_content': request.form['item_fat_content'],
            'item_visibility': request.form['item_visibility'],
            'item_type': request.form['item_type'],
            'item_mrp': request.form['item_mrp'],
            'outlet_id': request.form['outlet_id'],
            'outlet_year': request.form['outlet_year'],
            'outlet_size': request.form['outlet_size'],
            'outlet_location_type': request.form['outlet_location_type'],
            'outlet_type': request.form['outlet_type']
        }
        
        # Redirect to the 'result' page, passing all form data as query parameters
        return redirect(url_for('prediction', **form_data))
    # Get the currently logged in user's outlet_id
    username = session.get('username')
    user = Member.query.filter_by(username=username).first()
    
    if user:
        outlet = Outlet.query.filter_by(outlet_id=user.outlet_id).first()
    
    if outlet:
        return render_template('predict_sales.html', 
                            manager_outlet_id=outlet.outlet_id,
                            outlet_year=outlet.outlet_year,
                            outlet_size=outlet.outlet_size,
                            outlet_location_type=outlet.outlet_location_type,
                            outlet_type=outlet.outlet_type,
                            current_date=date.today().isoformat(),item_type_mapping=item_type_mapping)
    
    return redirect(url_for('login'))  # Redirect to login if not authenticated
    

# @app.route('/result', methods=['GET','POST'])
# def prediction():
    
#     item_weight = request.args.get('item_weight')
#     item_fat= request.args.get('item_fat_content')
#     item_visibility = request.args.get('item_visibility')
#     item_type = request.args.get('item_type')
#     item_mrp = request.args.get('item_mrp')
#     # outlet_id = request.args.get('outlet_id')
#     outlet_est_year = request.args.get('outlet_year')
#     outlet_size = request.args.get('outlet_size')
#     outlet_location_type = request.args.get('outlet_location_type')
#     outlet_type = request.args.get('outlet_type')
    
#     item_fat = fat_mapping.get(item_fat)
#     item_type = item_type_mapping.get(item_type)
#     outlet_size = outlet_size_mapping.get(outlet_size)
#     outlet_location_type = outlet_location_type_mapping.get(outlet_location_type)
#     outlet_type = outlet_type_mapping.get(outlet_type)

#     model_input = [[item_weight,item_fat,item_visibility,item_type,item_mrp,outlet_est_year,outlet_size,outlet_location_type,outlet_type]]

#     prediction = model.predict(model_input)
#     rounded_prediction = round(prediction[0],2)

#     item_id = request.args.get('item_id')
#     pred_date = date.today()
#     outlet_id = request.args.get('outlet_id')
#     new_sales = Sale(item_id=item_id,outlet_id=outlet_id,date=pred_date,sales=rounded_prediction)

#     db.session.add(new_sales)
#     db.session.commit()

#     return render_template('result.html',  predicted_sales=rounded_prediction, item_mrp=item_mrp)


@app.route('/result', methods=['GET', 'POST'])
def prediction():
    item_weight = request.args.get('item_weight')
    item_fat = request.args.get('item_fat_content')
    item_visibility = request.args.get('item_visibility')
    item_type = request.args.get('item_type')
    item_mrp = request.args.get('item_mrp')
    outlet_est_year = request.args.get('outlet_year')
    outlet_size = request.args.get('outlet_size')
    outlet_location_type = request.args.get('outlet_location_type')
    outlet_type = request.args.get('outlet_type')

    # Mapping input values
    item_fat = fat_mapping.get(item_fat)
    item_type = item_type_mapping.get(item_type)
    outlet_size = outlet_size_mapping.get(outlet_size)
    outlet_location_type = outlet_location_type_mapping.get(outlet_location_type)
    outlet_type = outlet_type_mapping.get(outlet_type)

    # Preparing the input for the model
    model_input = [[item_weight, item_fat, item_visibility, item_type, item_mrp, outlet_est_year, outlet_size, outlet_location_type, outlet_type]]

    # Get prediction from model
    prediction = model.predict(model_input)
    rounded_prediction = round(prediction[0], 2)

    # If prediction is negative, set it to zero
    if rounded_prediction < 0:
        rounded_prediction = 0

    # Store prediction in the database
    item_id = request.args.get('item_id')
    pred_date = date.today()
    outlet_id = request.args.get('outlet_id')
    new_sales = Sale(item_id=item_id, outlet_id=outlet_id, date=pred_date, sales=rounded_prediction)

    db.session.add(new_sales)
    db.session.commit()

    # Render result
    return render_template('result.html', predicted_sales=rounded_prediction, item_mrp=item_mrp)


# @app.route('/promotion_list')
# def promotion_list():
# @app.route('/promotion_list')
# def promotion_list():

#     # Ensure the user is logged in
#     if 'username' not in session:
#         return redirect(url_for('login'))

#     # Fetch all sales with predicted sales value less than 200
#     promotion_sales = db.session.query(Sale).filter(Sale.sales < 200).all()

#     # Create a list of dictionaries to hold the sales data along with the item type and date
#     promotion_data = []
#     for sale in promotion_sales:
#         item_type = Sale.query.with_entities(Sale.item_type).filter_by(item_id=sale.item_id).first()
        
#         # Prepare promotion data (item id, item type, predicted sales, and prediction date)
#         promotion_data.append({
#             'item_id': sale.item_id,
#             'item_type': item_type_mapping.get(item_type[0], 'Unknown'),
#             'predicted_sales': sale.sales,
#             'prediction_date': sale.date
#         })

#     # Render the promotion list with the filtered data
#     return render_template('promotion_list.html', promotions=promotion_data)

@app.route('/promotion_list')
def promotion_list():
    # Ensure the user is logged in
    if 'username' not in session:
        return redirect(url_for('login'))

    # Fetch all sales with predicted sales value less than 200
    promotion_sales = db.session.query(Sale).filter(Sale.sales < 200).all()

    # Create a list of dictionaries to hold the sales data
    promotion_data = []
    for sale in promotion_sales:
        # Prepare promotion data (item id, predicted sales, and prediction date)
        promotion_data.append({
            'item_id': sale.item_id,
            'predicted_sales': sale.sales,
            'prediction_date': sale.date
        })

    # Render the promotion list with the filtered data
    return render_template('promotion_list.html', promotions=promotion_data)

@app.route('/salesperson_dashboard')
def salesperson_dashboard():
    # Ensure the user is logged in
    if 'username' not in session:
        return redirect(url_for('login'))

    # Get the logged-in salesperson's details
    username = session['username']
    salesperson = Member.query.filter_by(username=username).first()

    if salesperson and salesperson.kind == 'salesperson':
        return render_template('salesperson_dashboard.html', salesperson_name=salesperson.username)

    return redirect(url_for('login'))

@app.route('/promotion_list')
def promotion_list_salesperson():
    # Ensure the user is logged in
    if 'username' not in session:
        return redirect(url_for('login'))

    # Get the logged-in user's username and outlet ID
    username = session['username']
    salesperson = Member.query.filter_by(username=username).first()

    if salesperson and salesperson.kind == 'salesperson':
        outlet_id = salesperson.outlet_id

        # Fetch all sales for this outlet with predicted sales value less than 200 (for promotion)
        promotion_sales = Sale.query.filter(Sale.outlet_id == outlet_id, Sale.sales < 1000).all()

        # Prepare the promotion data
        promotion_data = []
        for sale in promotion_sales:
            promotion_data.append({
                'item_id': sale.item_id,
                'predicted_sales': sale.sales,
                'prediction_date': sale.date
            })

        # Render the promotion list with the filtered data for this outlet
        return render_template('promotion_list.html', promotions=promotion_data)

    return redirect(url_for('login'))



# @app.route('/salesperson_dashboard')
# def salesperson_dashboard():
#     # Ensure the user is logged in
#     if 'username' not in session:
#         return redirect(url_for('login'))
    
#     # Get the logged-in user's username
#     username = session['username']
    
#     # Fetch the salesperson's details
#     salesperson = Member.query.filter_by(username=username).first()
    
#     if not salesperson or salesperson.kind != 'salesperson':
#         return redirect(url_for('login'))  # Redirect if not a salesperson
    
#     # Fetch sales for the salesperson's outlet
#     sales = Sale.query.filter_by(outlet_id=salesperson.outlet_id).all()
    
#     return render_template('salesperson_dashboard.html', sales=sales)




    # item_weight = float(request.form['item_weight'])
    # item_fat = request.form['item_fat_content']
    # item_visibility = float(request.form['item_visibility'])
    # item_type = request.form['item_type']
    # item_mrp = float(request.form['item_mrp'])
    # outlet_est_year = float(request.form['outlet_year'])
    # outlet_size = request.form['outlet_size']
    # outlet_location_type = request.form['outlet_location_type']
    # outlet_type = request.form['outlet_type']


    # item_weight = float(request.form['item_weight'])
    # item_fat = request.form['item_fat_content']
    # item_visibility = float(request.form['item_visibility'])
    # item_type = request.form['item_type']
    # item_mrp = float(request.form['item_mrp'])
    # outlet_est_year = float(request.form['outlet_year'])
    # outlet_size = request.form['outlet_size']
    # outlet_location_type = request.form['outlet_location_type']
    # outlet_type = request.form['outlet_type']




if __name__ == '__main__':
    app.run(debug=True)
