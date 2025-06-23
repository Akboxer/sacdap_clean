from flask import render_template, request, redirect, url_for, flash
from app_instance import app
from forms import EnrollmentForm, ContactForm
from data import courses_data, add_enrollment, add_contact, get_course_by_id, get_all_courses_for_search, get_connection 
import logging
from flask import jsonify
from datetime import datetime


@app.route('/')
def home():
    """Homepage showing all course categories"""
    search_courses = get_all_courses_for_search()
    return render_template('home.html', courses_data=courses_data, search_courses=search_courses)

@app.route('/stock-market')
def stock_market():
    """Stock market courses page"""
    search_courses = get_all_courses_for_search()
    return render_template('stock_market.html', 
                         courses=courses_data['stock_market'], 
                         search_courses=search_courses)

@app.route('/it-courses')
def it_courses():
    """IT courses page"""
    search_courses = get_all_courses_for_search()
    return render_template('it_courses.html', 
                         courses=courses_data['it'], 
                         search_courses=search_courses)

@app.route('/accounts')
def accounts():
    """Accounts courses page"""
    search_courses = get_all_courses_for_search()
    return render_template('accounts.html', 
                         courses=courses_data['accounting'], 
                         search_courses=search_courses)

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    """Contact page with form"""
    search_courses = get_all_courses_for_search()
    form = ContactForm()
    
    if form.validate_on_submit():
        try:
            contact_data = {
                'name': form.name.data,
                'email': form.email.data,
                'subject': form.subject.data,
                'message': form.message.data
            }
            
            contact_id = add_contact(contact_data)
            logging.info(f"New contact message received: {contact_id}")
            
            flash('Thank you for your message! We will get back to you soon.', 'success')
            return redirect(url_for('contact'))
            
        except Exception as e:
            logging.error(f"Error processing contact form: {str(e)}")
            flash('There was an error processing your message. Please try again.', 'error')
    
    return render_template('contact.html', form=form, search_courses=search_courses)

@app.route('/enroll', methods=['GET', 'POST'])
def enroll():
    """Common enrollment page for all courses"""
    search_courses = get_all_courses_for_search()
    form = EnrollmentForm()
    
    # Pre-select course if coming from a specific course page
    course_id = request.args.get('course')
    if course_id and request.method == 'GET':
        form.course_interested.data = course_id
    
    if form.validate_on_submit():
        try:
            enrollment_data = {
                'name': form.name.data,
                'email': form.email.data,
                'phone': form.phone.data,
                'course_interested': form.course_interested.data,
                'message': form.message.data
            }
            
            enrollment_id = add_enrollment(enrollment_data)
            logging.info(f"New enrollment received: {enrollment_id}")
            
            # Get course details for success page
            course = get_course_by_id(form.course_interested.data)
            course_name = course['name'] if course else 'Selected Course'
            
            return render_template('success.html', 
                                 course_name=course_name,
                                 student_name=form.name.data,
                                 search_courses=search_courses)
            
        except Exception as e:
            logging.error(f"Error processing enrollment: {str(e)}")
            flash('There was an error processing your enrollment. Please try again.', 'error')
    
    return render_template('enrollment.html', form=form, search_courses=search_courses)

@app.route('/search')
def search_course():
    """Handle course search from dropdown"""
    course_id = request.args.get('course')
    if not course_id:
        flash('Please select a course to search.', 'warning')
        return redirect(url_for('home'))
    
    # Redirect to enrollment page with pre-selected course
    return redirect(url_for('enroll', course=course_id))

@app.errorhandler(404)
def page_not_found(e):
    """Handle 404 errors"""
    search_courses = get_all_courses_for_search()
    return render_template('base.html', search_courses=search_courses), 404

@app.errorhandler(500)
def internal_server_error(e):
    """Handle 500 errors"""
    search_courses = get_all_courses_for_search()
    return render_template('base.html', search_courses=search_courses), 500




# routes for handeling admin portal
from flask import render_template


# updating the admin enrollment with a password protection 
ADMIN_PASSWORD = "admin123"  # use the same global password

@app.route('/admin/enrollments', methods=['GET', 'POST'])
def view_enrollments():
    if request.method == 'POST':
        password = request.form.get('password')
        if password == ADMIN_PASSWORD:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("""
                SELECT id, name, email, phone, course_interested, message 
                FROM enrollments 
                ORDER BY id DESC
            """)
            enrollments = cur.fetchall()
            cur.close()
            conn.close()
            return render_template('admin_enrollments.html', enrollments=enrollments)
        else:
            return render_template('admin_password.html', error="Incorrect password")
    
    # GET request — show password form
    return render_template('admin_password.html')





@app.route('/admin/contacts', methods=['GET', 'POST'])
def view_contacts():
    if request.method == 'POST':
        password = request.form.get('password')
        if password == ADMIN_PASSWORD:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("""
                SELECT id, name, email, subject, message, created_at
                FROM contacts
                ORDER BY id DESC
            """)
            contacts = cur.fetchall()
            cur.close()
            conn.close()
            return render_template('admin_contacts.html', contacts=contacts)
        else:
            return render_template('admin_password.html', error="Incorrect password")
    
    return render_template('admin_password.html')




@app.route('/submit-popup', methods=['POST'])
def submit_popup():
    try:
        data = request.get_json()
        name = data['name']
        phone = data['phone']
        course = data['course']
        created_at = datetime.now()

        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO visitors (name, phone, course, created_at)
            VALUES (%s, %s, %s, %s)
        """, (name, phone, course, created_at))
        conn.commit()
        cur.close()
        conn.close()

        return jsonify({'status': 'success', 'message': 'Thank you for registering!'}), 200

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500



# for pop up section

@app.route('/admin/visitors', methods=['GET', 'POST'])
def view_visitors():
    if request.method == 'POST':
        password = request.form.get('password')
        if password == ADMIN_PASSWORD:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("""
                SELECT id, name, phone, course, created_at 
                FROM visitors 
                ORDER BY id DESC
            """)
            visitors = cur.fetchall()
            cur.close()
            conn.close()
            return render_template('admin_visitors.html', visitors=visitors)
        else:
            return render_template('admin_password.html', error="Incorrect password")
    
    return render_template('admin_password.html')




#  ADDED PASSWORD TO ADMIN PAGE 
from flask import render_template, request

ADMIN_PASSWORD = "admin123"  #  admin password

@app.route('/admin', methods=['GET', 'POST'])
def admin_dashboard():
    if request.method == 'POST':
        password = request.form.get('password')
        if password == ADMIN_PASSWORD:
            return render_template('admin_dashboard.html')
        else:
            return render_template('admin_password.html', error="Incorrect password")
    return render_template('admin_password.html')


# adding three new tables in system
# making their routes and pages 

@app.route('/admin/enrollments/archive', methods=['POST'])
def archive_enrollments():
    selected_ids = request.form.getlist('selected_ids')
    if not selected_ids:
        flash('No records selected.', 'warning')
        return redirect(url_for('view_enrollments'))

    conn = get_connection()
    cur = conn.cursor()

    try:
        # Copy to archive
        cur.execute(f"""
            INSERT INTO archived_enrollments (name, email, phone, course_interested, message)
            SELECT name, email, phone, course_interested, message
            FROM enrollments
            WHERE id IN %s
        """, (tuple(selected_ids),))

        # Delete from original
        cur.execute("DELETE FROM enrollments WHERE id IN %s", (tuple(selected_ids),))
        conn.commit()
        flash('Selected enrollments archived.', 'success')

    except Exception as e:
        conn.rollback()
        flash(f'Error: {str(e)}', 'danger')

    finally:
        cur.close()
        conn.close()

    return redirect(url_for('view_enrollments'))






@app.route('/admin/visitors/archive', methods=['POST'])
def archive_visitors():
    selected_ids = request.form.getlist('selected_ids')
    if not selected_ids:
        flash('No records selected.', 'warning')
        return redirect(url_for('view_visitors'))

    conn = get_connection()
    cur = conn.cursor()

    try:
        # Insert into archived_visitors
        cur.execute("""
            INSERT INTO archived_visitors (name, phone, course, created_at)
            SELECT name, phone, course, created_at
            FROM visitors
            WHERE id IN %s
        """, (tuple(selected_ids),))

        # Delete from original
        cur.execute("DELETE FROM visitors WHERE id IN %s", (tuple(selected_ids),))
        conn.commit()
        flash('Selected visitors archived successfully!', 'success')

    except Exception as e:
        conn.rollback()
        flash(f'Error: {e}', 'danger')

    finally:
        cur.close()
        conn.close()

    return redirect(url_for('view_visitors'))






@app.route('/admin/contacts/archive', methods=['POST'])
def archive_contacts():
    selected_ids = request.form.getlist('selected_ids')
    if not selected_ids:
        flash('No records selected.', 'warning')
        return redirect(url_for('view_contacts'))

    conn = get_connection()
    cur = conn.cursor()

    try:
        # Insert selected records into archived_contacts
        cur.execute("""
            INSERT INTO archived_contacts (name, email, subject, message, created_at)
            SELECT name, email, subject, message, created_at
            FROM contacts
            WHERE id IN %s
        """, (tuple(selected_ids),))

        # Remove them from contacts
        cur.execute("DELETE FROM contacts WHERE id IN %s", (tuple(selected_ids),))
        conn.commit()
        flash('Selected contact submissions archived successfully.', 'success')

    except Exception as e:
        conn.rollback()
        flash(f'Error: {e}', 'danger')

    finally:
        cur.close()
        conn.close()

    return redirect(url_for('view_contacts'))
