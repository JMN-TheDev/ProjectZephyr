# Stockroom — item inventory management

A Flask and MySQL inventory and ordering app with an administrator dashboard and customer storefront. Admins can add, edit, hide, and restock products and update order status. Customers can register, browse/search products, keep a basket, place orders, and review order history. Passwords are stored as hashes; the app never stores card information or takes payments.

## Requirements

- Python 3.10 or newer
- MySQL Server 8.0 or newer, running on the same computer or reachable over the network
- A modern web browser

## Run on Windows

1. Install Python and MySQL Server. During MySQL setup, note the root password (or create a dedicated MySQL user).
2. Open PowerShell in this folder and create a virtual environment:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

   If PowerShell blocks activation, use `\.venv\Scripts\python.exe` in place of `python` in the commands below, or run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` for that PowerShell window.

3. Create the database tables. From a MySQL command prompt, run:

   ```text
   Get-Content schema.sql | mysql -u root -p
   ```

   Or open `schema.sql` in MySQL Workbench and execute it. This creates the `item_inventory` database and all required tables.

4. Copy `.env.example` to `.env`, then set `DB_USER` and `DB_PASSWORD` to your MySQL credentials. Replace `SECRET_KEY` with a long random secret. For example, generate one with:

   ```powershell
   python -c "import secrets; print(secrets.token_hex(32))"
   ```

   Keep `.env` private. Do not put it on a public website or commit it to source control.

5. Create the first administrator:

   ```powershell
   python create_admin.py
   ```

   Enter an admin name, email, and password when prompted. Customers can create accounts from the site.

6. Start the local development server:

   ```powershell
   python app.py
   ```

   Open <http://127.0.0.1:5000>. Stop it with Ctrl+C. For a production process on Windows, use Waitress:

   ```powershell
   waitress-serve --host=0.0.0.0 --port=5000 app:app
   ```

## Use it from another device on your local network

Start the app with Waitress as above, find the host computer's private IP address with `ipconfig`, then open `http://HOST-IP:5000` on the other device. Allow inbound TCP port 5000 in the host computer's firewall only on a trusted private network. This is for local network access; it does not make the app public on the internet.

## Put it on a USB drive and run it on another computer

The USB drive carries the project files; Python and MySQL still need to be installed and running on the new computer. A database is not included in this folder, so export/import it separately if you need to move existing products, customers, and orders.

1. Copy the whole project folder to the USB drive. Include `app.py`, `create_admin.py`, `schema.sql`, `requirements.txt`, `templates/`, and `static/`. Do not share the private `.env` file unless you deliberately want to transfer its credentials; configure a new `.env` on the destination computer.
2. On the destination computer, install Python and MySQL Server, then copy the folder from the USB drive onto that computer (for example, `C:\Stockroom`). Avoid running long-term from the USB drive because drive letters and write performance can vary.
3. Follow the Windows setup steps above to create a virtual environment and install dependencies, import `schema.sql`, and configure `.env` with that computer's MySQL settings.
4. Create an admin account using `python create_admin.py`, then run `python app.py` and open <http://127.0.0.1:5000>.

To move existing data, export the source database on the old computer and import it on the new one. For example, with MySQL command-line tools:

```text
mysqldump -u root -p item_inventory > item_inventory_backup.sql
mysql -u root -p < item_inventory_backup.sql
```

Copy that backup to the USB drive and import it on the destination after MySQL is installed. Treat it as private customer data and remove the USB copy when no longer needed. Reuse the existing admin account after importing; do not create a second one with the same email.

## Deploy the web app on Render

The repository includes `render.yaml` for the Flask web service. Render runs the app with Gunicorn and creates a random `SECRET_KEY`. The app uses MySQL, so you must first provision a reachable MySQL 8 database with a provider that allows connections from Render. Render's managed relational database product is PostgreSQL; it does not provide a managed MySQL database. Keep the database credentials private.

1. Push this project to a GitHub repository and create a MySQL 8 database with a provider that permits external connections. Note its host, port, database name, username, and password. Keep the database empty for now.
2. In Render, choose **New > Blueprint**, connect the repository, and apply the `render.yaml` blueprint. For the prompted values, enter `DB_HOST`, `DB_NAME`, `DB_USER`, and `DB_PASSWORD` from the MySQL provider. Render generates `SECRET_KEY` and sets `DB_PORT` to `3306`; change that value if your provider uses another port.
3. In the MySQL provider's SQL console or client, select the provisioned database and run `schema-hosted.sql`. This creates the tables without trying to create a database on the provider's behalf.
4. Create the first administrator from a trusted computer using the hosted DB credentials in a local, uncommitted `.env` file. Then run `python create_admin.py`. Remove those temporary credentials from `.env` when finished. Alternatively, run the script from a Render shell if your service plan provides one.
5. Wait for the Render deploy to finish and open the service's `onrender.com` URL. Pushes to the connected branch deploy automatically.

The Render service cannot be fully deployed from this project folder alone: it needs a Git repository connected in your Render account, and the database host and credentials must come from your chosen MySQL provider.

## Host on a public domain

This project runs the Flask application, but a public domain name must be registered separately and pointed to a server with a public IP. For a real deployment, use a Linux VPS or managed Python host, install Python/MySQL there, transfer the project, configure its private environment variables, import `schema.sql`, create an admin, and run the app behind a production WSGI server such as Waitress or Gunicorn. Point the domain's DNS A/AAAA record to the server, configure a reverse proxy such as Nginx to forward HTTPS requests to the WSGI server, and enable a TLS certificate. Keep MySQL bound to localhost or a private network, use a dedicated database user, use a unique `SECRET_KEY`, and keep `FLASK_DEBUG=0`. Do not expose Flask's built-in development server directly to the public internet.

The included app listens on `0.0.0.0` and defaults to port 5000. For a domain deployment, the hosting platform/reverse proxy should expose ports 80/443 and forward requests to the configured WSGI process. Domain registration, DNS, server provisioning, and TLS are managed by your chosen provider; they cannot be performed from the project itself.

## Project files

- `app.py` — routes and inventory/order logic
- `templates/` and `static/style.css` — responsive storefront, account pages, and admin dashboard
- `schema.sql` — MySQL database and tables
- `create_admin.py` — securely prompt for the first admin account
- `.env.example` — configuration template
