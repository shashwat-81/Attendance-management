from app import create_app
from app.utils import hash_password
from werkzeug.security import generate_password_hash

app = create_app()

def update_password_hashes():
    with app.app_context():
        from app import mongo
        
        # Get all users
        users = mongo.db.users.find({})
        
        for user in users:
            # Check if password uses scrypt
            if 'scrypt' in user.get('password', ''):
                print(f"Updating password hash for user: {user['username']}")
                
                # Set a temporary password and mark for reset
                temp_password = generate_password_hash('temp123', method='pbkdf2:sha256')
                
                mongo.db.users.update_one(
                    {'_id': user['_id']},
                    {
                        '$set': {
                            'password': temp_password,
                            'requires_password_reset': True
                        }
                    }
                )

if __name__ == '__main__':
    update_password_hashes()