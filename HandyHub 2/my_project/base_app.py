from flask import Flask, render_template,request,redirect, url_for, flash, jsonify,session
from flask_bootstrap import Bootstrap # type: ignore
from app_model import db, Customer, Admin, ServiceProfessional, Service, ServiceRequest
from datetime import datetime
from werkzeug.utils import secure_filename
import os
import uuid




app = Flask(__name__)
app.secret_key = 'model.secret-key'

# Directory to save uploaded files
UPLOAD_FOLDER = 'uploads/documents'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chinnu_bomb.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    db.create_all()



def seed_services():
    """Seed the services table with default values if it's empty."""
    services = ["Plumbing", "Electrician", "Carpentry", "Cleaning"]

    # Check if the services table is empty
    if Service.query.count() == 0:
        print("Seeding services...")
        for service_name in services:
            db.session.add(Service(name=service_name))
        try:
            db.session.commit()
            print("Services seeded successfully.")
        except Exception as e:
            db.session.rollback()
            print(f"Error seeding services: {e}")
    else:
        print("Services already seeded. Skipping.")













@app.route("/") #this is called decorator
def user():
    return render_template("users.html")



@app.route("/admin_login", methods=["GET", "POST"])
def admin_login():
    # Hardcoded admin credentials
    admin_username = "chinnu@dhana"
    admin_password = "dhana@chinnu"

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        # Check if entered credentials match the hardcoded ones
        if username == admin_username and password == admin_password:
            return redirect(url_for('admin_dashboard'))  # Redirect to admin dashboard
        else:
            flash("Invalid username or password!", "danger")

    return render_template('admin_login.html')


@app.route("/admin_dashboard", methods=["GET", "POST"])
def admin_dashboard():


    customers = Customer.query.all()
    professionals = ServiceProfessional.query.all()


    return render_template('admin_dashboard.html', customers=customers, professionals=professionals)

# Block customer
@app.route('/block_customer/<int:customer_id>')
def block_customer(customer_id):
    customer = Customer.query.get(customer_id)
    if customer:
        db.session.delete(customer)
        db.session.commit()
        flash("Customer blocked successfully!", "success")
    else:
        flash("Customer not found!", "danger")
    return redirect(url_for('admin_dashboard'))



# Block professional
@app.route('/block_professional/<int:professional_id>')
def block_professional(professional_id):
    professional = ServiceProfessional.query.get(professional_id)
    if professional:
        db.session.delete(professional)
        db.session.commit()
        flash("Professional blocked successfully!", "success")
    else:
        flash("Professional not found!", "danger")
    return redirect(url_for('admin_dashboard'))














@app.route("/customer_login", methods=["GET", "POST"])
def customer_login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        # Query the database for the customer
        customer = Customer.query.filter_by(email=email).first()

        if customer and customer.password == password:
            # Store customer_id in session
            session['customer_id'] = customer.id
            session['customer_details'] = customer.fullname
            flash("Login successful!", "success")
            return redirect(url_for("customer_dashboard"))  # Redirect to dashboard
        else:
            flash("Invalid email or password. Please try again.", "danger")

    return render_template("customer_login.html")




@app.route("/customer_signup", methods=["GET", "POST"])
def customer_signup():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        fullname = request.form.get("fullname")
        address = request.form.get("address")
        pincode = request.form.get("pincode")

        # Check if the email already exists
        existing_customer = Customer.query.filter_by(email=email).first()
        if existing_customer:
            flash("Email already registered. Please log in.", "danger")
            return redirect(url_for("customer_signup"))

        # Create a new customer instance
        new_customer = Customer(
            email=email,
            password=password,
            fullname=fullname,
            address=address,
            pincode=pincode,
        )
        db.session.add(new_customer)
        db.session.commit()

        flash("Account created successfully! Please log in.", "success")
        return redirect(url_for("customer_login"))

    return render_template("customer_signup.html")




@app.route("/customer_dashboard", methods=["GET", "POST"] )
def customer_dashboard():
    name = session.get('customer_details')
    return render_template('customer_dashboard.html', cust_name = name)


# Happening in customer dashboard
from datetime import datetime

@app.route('/send_request', methods=['POST'])
def send_request():
    # Assuming the service_id is passed in the session and professional_id is part of the form
    service_id = request.form.get('service_id')  # Retrieved from the form
    customer_id = session.get('customer_id')  # Retrieved from the session
    professional_id = request.form.get('professional_id')  # Retrieved from the form
    date = request.form.get('date')  # Retrieved from the form

    # Debugging: Check the values being passed
    print("##### service_id:", service_id, "professional_id:", professional_id, "customer_id:", customer_id, date)

    # Convert the string date into a datetime.date object
    if date:
        try:
            date_of_request = datetime.strptime(date, '%Y-%m-%d').date()  # Convert string to date object
        except ValueError:
            flash("Invalid date format. Please try again.", "danger")
            return redirect(url_for('customer_dashboard'))

    # Create a new service request
    new_request = ServiceRequest(
        service_id=service_id,  # Service ID from the form
        customer_id=customer_id,  # Customer ID from session
        professional_id=professional_id,  # Professional ID, if provided
        date_of_request=date_of_request,
        date_of_completion=None,  # Completion date is None for a pending request
        service_status="Pending",
        is_request_edited=True
    )
    
    # Add to the session and commit
    db.session.add(new_request)
    try:
        db.session.commit()
        flash("Request has been added successfully!", "success")  # Updated success message
    except Exception as e:
        db.session.rollback()
        flash("Failed to send service request. Please try again.", "danger")
        print(f"Error: {e}")

    return redirect(url_for('customer_dashboard'))


@app.route('/edit_request', methods=['POST'])
def edit_request():
    request_id = request.form['request_id']
    date_of_request = datetime.now()
    # Update the request in the database
    service_request = ServiceRequest.query.filter_by(id=request_id).first()
    payload = dict()
    if service_request:
        payload['service_id'] = request_id
        payload['date_of_request'] = date_of_request
        service_request.date_of_request = date_of_request
        db.session.commit()


    flash("Service request updated successfully.", "success")
    print(payload, 'Renee')
    # return redirect(url_for('customer_dashboard', payload = payload))
    return render_template("customer_dashboard.html", payload = payload)


@app.route('/close_request', methods=['POST'])
def close_request():
    request_id = request.form['close_request_id']
    # Add code to handle closing an existing service request
    return redirect(url_for('customer_dashboard'))

@app.route('/search_services', methods=['POST'])
def search_services():
    pincode = request.form.get('pincode')

    # Query the database for professionals with the matching pincode
    professionals = ServiceProfessional.query.filter_by(pincode=pincode).all()

    results = []
    if professionals:
        for professional in professionals:
            # Fetch related service and service request data
            service = Service.query.filter_by(id=professional.service_id).first()
            service_request = ServiceRequest.query.filter_by(professional_id=professional.id).first()

            # Append results with default handling for missing data
            results.append({
                "id": professional.id,
                "fullname": professional.fullname,
                "service_id": professional.service_id,
                "service_name": service.name if service else "N/A",
                "experience": professional.experience,
                "address": professional.address,
                "pincode": professional.pincode,
                "date_of_request": service_request.date_of_request if service_request else False,
                "requested": service_request.is_request_edited if service_request else False,
                "requested": service_request.is_request_edited if service_request else False,
                "service_status": service_request.service_status if service_request else False,
            })

    # Render the same dashboard template with search results
    return render_template("customer_dashboard.html", search_results=results, search_pincode=pincode)


@app.route('/rate_professional', methods=['POST'])
def rate_professional():
    professional_id = request.form.get('professional_id')
    rating = int(request.form.get('rating'))

    # Validate the rating
    if rating < 1 or rating > 5:
        flash("Invalid rating. Please select a value between 1 and 5.", "danger")
        return redirect(url_for('customer_dashboard'))

    # Fetch the professional and update their rating
    professional = ServiceProfessional.query.get(professional_id)
    if professional:
        professional.rating = rating
        db.session.commit()
        flash("Rating submitted successfully!", "success")
    else:
        flash("Professional not found.", "danger")
    
    return redirect(url_for('customer_dashboard'))



@app.route("/professional_login", methods=["GET", "POST"])
def professional_login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

    

        # Query the database for the user
        professional = ServiceProfessional.query.filter_by(email=email).first()
        if professional:
            session['professional_id'] = professional.id
            session['professional_details'] = professional.fullname

        # Check if the user exists and validate the password
        if professional:
            print("Stored Password:", professional.password)
            print("Entered Password:", password)
            if professional.password == password:
                session['professional_id'] = professional.id
                flash("Login successful!", "success")
                return redirect(url_for("professional_dashboard"))
            else:
                print("Password mismatch")
        else:
            print("User not found")

        # Flash error for invalid credentials
        flash("Invalid email or password. Please try again.", "danger")
        return redirect(url_for("professional_login"))

    return render_template("professional_login.html")






@app.route('/professional_signup', methods=['GET', 'POST'])
def professional_signup():
    if request.method == 'POST':
        # Get form data
        service_id = request.form.get('service_id')
        if not service_id:
            flash("Please select a valid service.", "danger")
            return redirect(url_for('professional_signup'))

        try:
            # Convert service_id to integer
            service_id = int(service_id)
        except ValueError:
            flash("Invalid service ID provided.", "danger")
            return redirect(url_for('professional_signup'))

        # Fetch the corresponding Service object
        service = Service.query.get(service_id)
        if not service:
            flash("Selected service is invalid. Please try again.", "danger")
            return redirect(url_for('professional_signup'))

        # Debugging outputs
        print("Service ID from form:", service_id)
        print("Service fetched from DB:", service)

        # Other form fields
        email = request.form.get('email')
        password = request.form.get('password')
        fullname = request.form.get('fullname')
        experience = request.form.get('experience')
        address = request.form.get('address')
        pincode = request.form.get('pincode')

        # Handle file upload
        document = request.files.get('document')
        if document and document.filename.endswith('.pdf'):
            # Generate a unique filename to avoid collisions
            unique_filename = secure_filename(f"{uuid.uuid4()}_{document.filename}")
            upload_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            
            # Save the document
            document.save(upload_path)
        else:
            flash("Invalid document format or no document uploaded. Please upload a valid PDF.", "danger")
            return redirect(url_for('professional_signup'))

        # Save to the database
        new_professional = ServiceProfessional(
            email=email,
            password=password,
            fullname=fullname,
            service_id=service_id,
            experience=int(experience),
            document=upload_path,  # Save the file path
            address=address,
            pincode=pincode
        )
        db.session.add(new_professional)
        db.session.commit()

        return redirect(url_for('professional_login'))

    # Populate services for the dropdown
    services = Service.query.all()
    return render_template('professional_signup.html', services=services)




@app.route("/professional_dashboard", methods=['GET','POST'])
def professional_dashboard():
    # Example data for service requests
    professional_id = session.get('professional_id')  # Retrieved from the session
    pro_name = session.get('professional_details')

    serviceRequest = ServiceRequest.query.filter_by(professional_id=professional_id).all()
    results = []
    if serviceRequest:
        results = [
        {
            "id": service_request.id,
            "fullname": Customer.query.filter_by(id=service_request.customer_id).first().fullname,
            "service": service_request.service_id,
            "service_name": Service.query.filter_by(id=service_request.service_id).first().name,
            "experience": ServiceProfessional.query.filter_by(id=service_request.professional_id).first().experience,
            "address": ServiceProfessional.query.filter_by(id=service_request.professional_id).first().address,
            "pincode": ServiceProfessional.query.filter_by(id=service_request.professional_id).first().pincode,
            "status": service_request.service_status,
            "date": service_request.date_of_request,
        }
        for service_request in serviceRequest
        ]
    else:
        results = []

    print(results, "results")
    return render_template("professional_dashboard.html", service_requests=results, pro_name=pro_name)

@app.route("/update_request_date", methods=["POST"])
def update_request_date():
    service_id = request.form.get("service_id")
    customer_id = session.get('customer_id')  # Retrieved from the session
    professional_id = request.form.get('professional_id')  # Retrieved from the form
    date = request.form.get('date_of_request')  # Retrieved from the form
    service_request = ServiceRequest.query.filter_by(service_id=service_id, customer_id=customer_id, professional_id=professional_id).first()
    cust_date = datetime.strptime(date, "%Y-%m-%d")
    service_request.date_of_request = cust_date 
    # db.session.commit()

    try:
        db.session.commit()
        flash(f"Request {service_id} has been updated!", "success")
    except Exception as e:
        db.session.rollback()
        flash("Failed to update request status. Please try again.", "danger")
        print(f"Error: {e}")
    # Update the request status in the database based on the action
    # For now, just flash the action for demonstration

    print(service_id)
    flash(f"Request {service_id} has been updated!", "success")
    return redirect(url_for("customer_dashboard"))

@app.route("/update_request_status", methods=["POST"])
def update_request_status():
    # service_id = request.form.get("service_id")
    request_id = request.form.get("request_id")
    # customer_id = session.get('customer_id')  # Retrieved from the session
    # professional_id = request.form.get('professional_id')  # Retrieved from the form
    service_status = request.form.get('service_status')  # Retrieved from the form
    service_request = ServiceRequest.query.filter_by(id=request_id).first()
    # cust_date = datetime.strptime(date, "%Y-%m-%d")
    # print("service_request", service_id, customer_id, professional_id)
    service_request.service_status = service_status 
    # db.session.commit()

    try:
        db.session.commit()
        flash(f"Request {service_status} has been updated!", "success")
    except Exception as e:
        db.session.rollback()
        flash("Failed to update request status. Please try again.", "danger")
        print(f"Error: {e}")
    # Update the request status in the database based on the action
    # For now, just flash the action for demonstration

    # print(service_id)
    flash(f"Request {request_id} has been updated!", "success")
    return redirect(url_for("professional_dashboard"))



if __name__ == "__main__":
     with app.app_context():
        db.create_all()  # Ensure tables are created
        seed_services()  # Automatically seed services if needed
     app.run(debug=True, port=5000)