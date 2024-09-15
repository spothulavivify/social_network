# Social Network API

This is a Django Rest Framework-based API for a social networking application.

## Features

- User registration and login
- User search
- Friend requests (send, accept, reject)
- List friends
- List pending friend requests

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/social-network-api.git
   cd social-network-api
   ```

2. Build and run the Docker containers:
   ```
   docker-compose up --build
   ```

3. Apply migrations:
   ```
   docker-compose exec web python manage.py migrate
   ```

4. Create a superuser (optional):
   ```
   docker-compose exec web python manage.py createsuperuser
   ```

5. The API should now be accessible at `http://localhost:8000/`


## Contributing

Please read CONTRIBUTING.md for details on our code of conduct, and the process for submitting pull requests.

## License

This project is licensed under the MIT License - see the LICENSE.md file for details.