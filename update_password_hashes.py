from app.utils import hash_password
from app import db
from werkzeug.security import check_password_hash

def update_password_hashes():
    users = db.users.find({})
    
    for user in users:
        # Skip users that already have pbkdf2 hashes
        if user['password'].startswith('pbkdf2:'):
            continue
            
        # For existing users, you'll need to implement a password reset
        # Mark them for required password change
        db.users.update_one(
            {'_id': user['_id']},
            {'$set': {
                'requires_password_reset': True
            }}
        )

if __name__ == '__main__':
    update_password_hashes()