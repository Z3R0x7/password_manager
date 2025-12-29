import os
import mysql.connector
import pandas as pd
from cryptography.fernet import Fernet, InvalidToken
from random import choices
from string import ascii_letters, digits

# Generate a random key for encryption (store it securely)
encryption_key = Fernet.generate_key()
cipher_suite = Fernet(encryption_key)

# Create a MySQL connection
db_connection = mysql.connector.connect(
    host="localhost",
    user="root",
    password="password",
    database="pswd"
)

# Create a MySQL cursor
db_cursor = db_connection.cursor()

# Create a table to store username and encrypted password
db_cursor.execute("""
    CREATE TABLE IF NOT EXISTS passwords (
        username VARCHAR(255) PRIMARY KEY,
        encrypted_password BLOB
    )
""")


def encrypt_password(password, encryption_key):
    return cipher_suite.encrypt(password.encode())


def decrypt_password(encrypted_password, encryption_key):
    return cipher_suite.decrypt(encrypted_password).decode()


def save_password(username, password):
    encrypted_password = encrypt_password(password, encryption_key)
    # Insert or update the password in the database
    db_cursor.execute("""
        INSERT INTO passwords (username, encrypted_password)
        VALUES (%s, %s)
        ON DUPLICATE KEY UPDATE encrypted_password = VALUES(encrypted_password)
    """, (username, encrypted_password))
    db_connection.commit()


def get_password(username):
    db_cursor.execute(
        "SELECT encrypted_password FROM passwords WHERE username = %s", (username,))
    result = db_cursor.fetchone()
    if result:
        encrypted_password = result[0]
        try:
            decrypted_password = decrypt_password(
                encrypted_password, encryption_key)
            return decrypted_password
        except InvalidToken:
            return "Invalid encryption key or corrupted data."
    else:
        return "Username not found."


def generate_password(length=12):
    chars = ascii_letters + digits
    return ''.join(choices(chars, k=length))


def delete_password(username):
    db_cursor.execute(
        "DELETE FROM passwords WHERE username = %s", (username,))
    db_connection.commit()
    print(f"Password for {username} deleted successfully.")


def export_to_excel():
    db_cursor.execute("SELECT * FROM passwords")
    result = db_cursor.fetchall()
    if result:
        data = {'Username': [], 'Password': []}
        for row in result:
            username = row[0]
            encrypted_password = row[1]
            decrypted_password = decrypt_password(
                encrypted_password, encryption_key)
            data['Username'].append(username)
            data['Password'].append(decrypted_password)

        df = pd.DataFrame(data)
        df.to_excel('passwords.xlsx', index=False)
        print("Passwords exported to 'passwords.xlsx'")
    else:
        print("No passwords to export.")


while True:
    print("\n" + "=" * 30)
    print("         PASSWORD MANAGER")
    print("=" * 30)
    print("Options:")
    print("1. Save Password")
    print("2. Get Password")
    print("3. Generate Password")
    print("4. Delete Password")
    print("5. Export Passwords to Excel")
    print("6. Exit")

    choice = input("\nEnter your choice: ")

    if choice == "1":
        username = input("Enter username: ")
        password = input("Enter password: ")
        save_password(username, password)
        print("\nPassword saved successfully.")
    elif choice == "2":
        username = input("Enter username: ")
        password = get_password(username)
        print(f"\nPassword: {password}")
    elif choice == "3":
        username = input("Enter username: ")
        password = generate_password()
        save_password(username, password)
        print(f"\nGenerated Password: {password}")
    elif choice == "4":
        username = input("Enter username to delete password: ")
        delete_password(username)
    elif choice == "5":
        export_to_excel()
    elif choice == "6":
        db_connection.close()
        print("Goodbye!")
        break
    else:
        print("Invalid choice. Please try again.")


