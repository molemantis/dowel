from app import create_app, db
from app.models import Category

app = create_app()

with app.app_context():
    db.create_all()
    if Category.query.count() == 0:
        categories = [
            Category(name='Power Tools', icon='⚡'),
            Category(name='Hand Tools', icon='🔨'),
            Category(name='Garden & Outdoor', icon='🌿'),
            Category(name='Measuring & Layout', icon='📐'),
            Category(name='Plumbing', icon='🚿'),
            Category(name='Electrical', icon='💡'),
            Category(name='Automotive', icon='🚗'),
            Category(name='Ladders & Scaffolding', icon='🪜'),
            Category(name='Cleaning & Maintenance', icon='🧹'),
            Category(name='Other', icon='🔧'),
        ]
        db.session.add_all(categories)
        db.session.commit()
        print("Seeded categories.")

if __name__ == '__main__':
    app.run(debug=True, port=5002)
