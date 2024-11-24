## Book store api
Bookstore API is a backend application for managing a bookstore. It allows for the management of books, customers, and adminstrative tasks.
Its built with python, flask, docker, nginx and more

## Key Features
1. Book Management
- Admin can add, update, delete books
- Admin can search for books by title, author, or genre

2. Customer Management
- Customers can create an account and login
- Customers can view and purchase books
- Customers can view their cart and checkout
- Customers can view their purchase history

3. Order Management
- Admin can view and manage orders
- Admin can update the status of orders

4. Payment Processing
- Customers can make payments using credit card or other payment methods

5. User Authentication
- Customers can create an account and login
- Admin can login

6. User Authorization
- Admin can access admin-only routes
- Customers can access customer-only routes

7. Error Handling
- Proper error messages are returned to the user

8. Documentation
- API documentation is available

## Getting Started
1. Clone the repository
```bash
git clone https://github.com/sendi-stev/bookstore-api.git
```
2. Install dependencies
```bash
pip install -r requirements.txt
```
3. Run the application
```bash
python run.py
```
## Setup docker
1. Build the image
```bash
make build
```
2. Run the container
```bash
make up
```
3. Stop the container
```bash
make down
```

## Contributing
1. Fork the repository
2. Create a new branch
3. Make your changes
4. Submit a pull request