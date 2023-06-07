from website import create_app
from website.models import Company, db


app = create_app()

@app.before_request
def create_default_entry():
    # Check if the default entry already exists
    if Company.query.filter_by(company_name='No company assigned').first() is None:
        # Create the default entry
        default_entry = Company(company_name='No company assigned', pbi_source=None, drive_folder=None)
        db.session.add(default_entry)
        db.session.commit()
        print("Default entry created.")

if __name__ == '__main__':
    app.run(debug=True)