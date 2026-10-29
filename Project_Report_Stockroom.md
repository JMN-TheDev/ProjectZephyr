# Stockroom: Item Inventory Management System

## Full Project Report

**Project type:** Web-based inventory and order management application  
**Application stack:** Python, Flask, MySQL, HTML, CSS, Jinja templates  
**Report version:** 1.0  
**Prepared:** October 2026

> **Length note:** This report is organized into 40 page-sized sections with explicit page breaks for convenient export. The exact number of printed pages depends on the Markdown renderer, paper size, font, margins, and whether code and tables wrap.

\newpage

## Page 1 — Executive Summary

Stockroom is a small web-based inventory and ordering system implemented with Python and Flask. Its purpose is to give a business a straightforward way to maintain a product catalogue, expose available items to customers, and record customer orders against stock. The application distinguishes administrator and customer roles. Customers can create accounts, browse and search products, prepare a basket, check out, and review their past orders. Administrators can maintain product records, adjust quantities, hide products from the storefront, review a compact set of inventory metrics, and change order status.

The persistence layer is MySQL. The database structure is defined in `schema.sql`; application routes execute parameterized SQL through `mysql-connector-python`. Passwords are stored as Werkzeug-generated hashes. Configuration is loaded from a local `.env` file, which allows database credentials and the session secret to be set outside the source code.

The delivered application is a functional starter system, not a complete commercial platform. It does not process payment, coordinate shipping, send email, upload product photographs, or provide a stock-change audit trail. It has not been deployed to a public domain or verified against a live MySQL installation. The remaining pages describe the design, implementation, operating instructions, limitations, and a practical development roadmap.

\newpage

## Page 2 — Project Background

Many small shops begin inventory tracking with spreadsheets, paper records, or a collection of disconnected tools. These approaches are easy to start with but become difficult when several people need to see the same stock level, customers place orders, or products change frequently. Duplicate records and delayed updates can lead to overselling, missed replenishment, and uncertainty about the current state of orders.

Stockroom addresses this class of problem by putting product information and order records behind a single web application backed by a relational database. A browser is the user interface, Flask routes handle requests, and MySQL stores durable data. This arrangement gives the project a clear path from a local demonstration to a hosted application, while remaining understandable for a student or small development team.

The chosen scope focuses on the essential inventory and order lifecycle. It avoids integrating payment gateways or external fulfilment systems in the initial version. This keeps setup manageable and allows the core account, catalogue, stock, and order concepts to be demonstrated independently. The application is therefore appropriate as an educational project, prototype, or basis for further requirements work. Production use would require the additions and security review described later in this report.

\newpage

## Page 3 — Problem Statement

The project problem is to provide a shared system in which authorized staff can maintain products and stock, while customers can discover available items and place orders. The data must remain available after the web process restarts, and order placement must not silently reduce stock below zero. The interface should make core actions understandable to users who do not work with databases or command-line tools.

The system also needs two access levels. Administrative functions must be kept away from ordinary customers, while customers should only be able to access their own account and order history. Product data needs a representation for name, category, description, price, quantity, active visibility, and creation time. An order needs a customer, total, state, timestamp, and a durable copy of the item names, quantities, and prices at purchase time.

The problem is intentionally bounded. This version records an order but does not represent a payment authorization, shipping address, tax calculation, shipment, refund, or return. These omissions are deliberate scope boundaries and should be addressed before the application is treated as a full ecommerce operation.

\newpage

## Page 4 — Project Aim and Objectives

The aim is to build a clean, responsive inventory management web application using Python, Flask, and MySQL, with distinct customer and administrator workflows. The implementation should be simple to configure on a development computer and transferable to another computer using a USB drive and documented setup steps.

The project objectives are:

1. Define relational tables for users, products, orders, and order items.
2. Provide customer registration and sign-in with hashed passwords.
3. Display active products and allow text search over product name, category, and description.
4. Maintain a session-based basket and create an order during checkout.
5. Recheck stock and update inventory when an order is placed.
6. Provide administrator screens for product maintenance, stock visibility, and order status.
7. Keep credentials and the Flask secret outside source code using environment configuration.
8. Document installation, database setup, local use, USB transfer, and public-hosting prerequisites.

Completion of these objectives establishes the base application. It does not establish compliance, operational readiness, or a production service-level guarantee.

\newpage

## Page 5 — Scope of the Delivered System

Included functionality covers the web application and its database schema. The storefront lists active products and supports a query parameter search. Customer accounts can be created through a form and authenticated with a password hash. The basket is held in the Flask session, so it is associated with the browser session rather than stored as a database cart. Checkout is restricted to signed-in customers.

The administrator dashboard displays aggregate counts, a product table, a product form, and recent orders. Administrators can edit product details, stock, and visibility. Order status values are pending, processing, completed, and cancelled. The `README.md` provides initial setup and transfer instructions; `.env.example` provides the configuration keys.

Excluded functions include payment capture, shipping, email, image management, customer support, discount codes, reports exported to files, audit history, and multiple warehouse locations. The software does not perform domain registration, DNS changes, cloud provisioning, or TLS certificate setup. These exclusions should be considered when deciding whether the current version suits an actual business.

\newpage

## Page 6 — Stakeholders and User Roles

The principal stakeholders are customers, administrators, the business owner, and the person responsible for installing and maintaining the application. Each has different needs. Customers need a readable catalogue, accurate stock indications, a simple basket, and access to their own order records. Administrators need reliable editing controls and an at-a-glance view of products requiring attention. The owner needs confidence that orders and stock are stored consistently. The operator needs a repeatable process for configuration, database backup, and restart.

The code implements two role values: `customer` and `admin`. A newly registered user is always created with the customer role. The initial administrator is created separately by `create_admin.py`, which prompts for a name, email, and password and stores a password hash. This separation prevents the public registration form from offering a self-service administrator option.

Role checks are performed by a route decorator. Routes that require a role redirect unauthenticated users to sign in and reject authenticated users whose role does not match. More granular permissions, such as separate stock manager and order manager roles, are outside the current model.

\newpage

## Page 7 — Functional Requirements

The system's functional requirements describe observable behavior. A customer must be able to register with a name, email, and password meeting the minimum length used by the form and route. Duplicate email addresses must be rejected. A customer must be able to sign in and sign out. The product catalogue must omit hidden products from public browsing. Search must match product name, category, or description.

A visitor can add available items to a session basket. The basket page shows quantities and line totals and allows quantities to be updated or removed. Checkout requires customer authentication. Before recording an order, the application retrieves each product under a database lock and verifies that it remains active and has enough stock. If validation passes, it records the order and order items and reduces product stock in the same transaction.

An administrator must be able to create and edit products, hide and reactivate products, view recent orders, and change order status. The dashboard metrics summarize active products, active units, pending orders, and low-stock products. These are application-level requirements, not independent certification that every edge case has been validated.

\newpage

## Page 8 — Non-Functional Requirements

The interface should be responsive enough to work on common desktop and mobile browser widths. Forms should have visible labels, controls should have clear purposes, and status feedback should appear after actions. The implementation uses semantic HTML elements, a stylesheet, and server-rendered Jinja templates rather than a client-side single-page framework.

The database should enforce primary keys, unique user email addresses, and foreign-key relationships. Application SQL should use placeholders for user-supplied values. Passwords must not be stored in plain text. Configuration should be separated from source code. The app should be deployable behind a production WSGI server rather than the Flask development server.

The current implementation makes a reasonable foundation for these requirements, but it has not undergone a formal accessibility audit, performance test, penetration test, or reliability test. It lacks rate limiting, CSRF protection, structured application logging, centralized error handling, and a migration system. These are important operational concerns before public deployment. Requirements should be reviewed against the actual business, legal, and security environment before use with real customer data.

\newpage

## Page 9 — Use-Case Overview

The primary customer use case begins with catalogue browsing. A visitor may search for an item, add it to the basket, and inspect quantities and prices. When ready, the visitor signs in or registers, then submits checkout. The application validates current product availability and creates an order. Once authenticated, the customer can review order dates, line items, totals, and current status.

The primary administrator use case begins with an administrator signing in. The dashboard summarizes catalogue and stock conditions. The administrator adds a product or edits an existing one, optionally hides it from customers, and later changes its stock quantity. The administrator reviews recent orders and updates their state as work progresses.

Supporting use cases include signing out and recovering from unavailable or invalid form data. The interface displays flash messages after many actions. There is no password reset use case, user deletion process, export process, payment process, or shipment process. Those would require new requirements and corresponding persistence and security decisions.

\newpage

## Page 10 — System Architecture

Stockroom follows a compact server-rendered web architecture. A browser sends an HTTP request to the Flask application. A route function reads request data, applies authentication and role checks where required, executes a database operation, and renders a Jinja template or redirects to another route. HTML is styled by `static/style.css`. The browser receives the rendered result and submits subsequent actions through links or forms.

MySQL is the durable data store. `db_connection()` reads host, port, database, username, and password from environment variables and creates a connector connection. The shared `query()` helper executes SQL with bound parameters, returns rows as dictionaries for read operations, commits writes when requested, and closes connections in a `finally` block.

The Flask session stores identity information and the basket. The application uses Flask's signed cookie session mechanism; it does not store session data in MySQL. A production deployment should use a unique secret, HTTPS, appropriate cookie settings, and a production WSGI server. If a larger workload or deployment requires it, database access and business logic can be separated into dedicated modules and services.

\newpage

## Page 11 — Technology Selection

Python was selected for its readable syntax and broad availability in education and small application development. Flask supplies routing, request handling, templates, and session support without imposing a large application framework. This keeps the route flow visible to a reader who is learning web development.

MySQL provides relational persistence, indexes, transactions, and referential constraints. Inventory and ordering data have clear relationships, making a relational model appropriate. `mysql-connector-python` provides the Python connection layer. Jinja is included with Flask and renders templates on the server. Werkzeug provides password hashing utilities used by Flask's ecosystem. `python-dotenv` loads local configuration from `.env`; Waitress is included as a production-capable WSGI server that can run on Windows.

The frontend uses standard HTML and CSS with Google Fonts loaded by the browser. That external font request may not work in an offline environment; local system fonts remain the fallback. The project does not require Node.js or a JavaScript build step. The only JavaScript is small admin-form behavior embedded in the admin template.

\newpage

## Page 12 — Repository and File Structure

The project is organized so that setup, application, templates, and styling are easy to locate:

| Path | Purpose |
|---|---|
| `app.py` | Flask application, routes, SQL access, and business operations |
| `schema.sql` | Database creation and table definitions |
| `create_admin.py` | Interactive creation of an initial administrator |
| `requirements.txt` | Python package dependencies |
| `.env.example` | Example environment configuration |
| `templates/` | Jinja pages for the storefront, accounts, orders, and admin |
| `static/style.css` | Responsive visual styling |
| `README.md` | Installation, local run, transfer, and deployment guidance |

The `.env` file is intentionally not included as a committed configuration file. It should be created on each computer from `.env.example` and populated with local credentials. The virtual environment `.venv` is also machine-specific and should be recreated on the destination computer rather than copied as a dependable portable runtime.

\newpage

## Page 13 — Database Design Overview

The database is named `item_inventory` and uses `utf8mb4` with a Unicode collation. It contains four tables: `users`, `products`, `orders`, and `order_items`. Each table has an integer auto-increment primary key. Timestamps are generated by MySQL when records are created.

Users have a unique email, display name, password hash, and role. Products hold descriptive catalogue data, price, quantity, a visibility flag, and creation time. Orders link to a user and store a total and status. Order items link to an order and optionally to a current product record while also storing a product name, quantity, and unit price snapshot. The snapshot means a historical order can retain the purchased label and price if the catalogue later changes or the product row is removed.

Foreign keys prevent an order from referring to a nonexistent user and prevent an item from referring to a nonexistent order. Deleting an order cascades to its lines. Deleting a product sets the item's product link to null. The user route does not expose deletion functions, which helps preserve account and order history through the normal interface.

\newpage

## Page 14 — Users Table

The `users` table has an integer `id`, `name`, `email`, `password_hash`, `role`, and `created_at`. Email is unique so two accounts cannot use the same address. Role is an enumeration constrained to `admin` or `customer`, defaulting to customer. Account creation through the public registration route explicitly inserts the customer role. The separate administrator script explicitly inserts the admin role.

Passwords are transformed with `generate_password_hash()` before insertion and checked using `check_password_hash()` during login. The stored value is not the original password. The design therefore avoids the most serious error of keeping readable passwords in the user table. Password length is currently checked at a minimum of eight characters, but there is no password reset, account lockout, breached-password screening, or multi-factor authentication.

The application stores a user's name and email, both of which are personal information. A real deployment should establish a privacy notice, retention policy, backup protection, access controls, and a process for handling account-data requests. The schema is intentionally minimal and does not store addresses or payment details.

\newpage

## Page 15 — Products Table

The `products` table stores a product's name, category, description, unit price, stock count, active flag, and creation time. The active flag is used as a soft visibility switch: inactive products are omitted from public catalogue search but retained in the database and visible to the administrator. This avoids losing order references by hard-deleting a product merely because it should no longer be sold.

Price is a `DECIMAL(10,2)` value, which is more appropriate for currency than a binary floating-point value. Stock is an integer. The admin route validates that the name is present and price and stock are non-negative before writing. The database schema itself does not define explicit `CHECK` constraints for non-negative values, so direct SQL changes could bypass that route validation. A production hardening step should add database constraints where supported and test them against the target MySQL version.

An index on `(active, name)` supports common catalogue filtering and ordering. Category and description are searched with `LIKE`; for a small catalogue this is simple and sufficient. A much larger catalogue may require a full-text index or dedicated search service.

\newpage

## Page 16 — Orders and Order Items

An order is linked to its customer through `user_id` and stores `total`, `status`, and creation time. The allowed statuses are pending, processing, completed, and cancelled. An order item stores its parent order, optional product link, product name snapshot, quantity, and unit price. The line's historical value can be recalculated as quantity multiplied by unit price; the order total is stored separately for convenient display.

Checkout creates the order and its item rows in one database transaction. It also subtracts purchased quantities from product stock before committing. If a product is missing, inactive, or insufficiently stocked, the transaction is rolled back and the user is returned to the basket with a message. The row lock reduces the risk of two concurrent checkouts both selling the final unit.

Cancelling an order restores linked product quantities inside the order-status transaction. Repeating cancellation does not restore them a second time, and a cancelled order cannot be reopened in the current workflow. There is no separate fulfillment event history or staff audit record. A future implementation should record who changed the order and define cancellation rules for orders that have already been processed or completed.

\newpage

## Page 17 — Database Relationships and Integrity

The data model has one-to-many relationships from users to orders, orders to order items, and products to order items. A customer may have many orders. Each order may contain many item rows. A product may appear on many order lines over time. An order line may retain its product snapshot even if the product row is no longer available, because the product foreign key is nullable and uses `ON DELETE SET NULL`.

The database's unique and foreign-key constraints supplement application validation. They protect data from some accidental inconsistencies even if a route has a bug. However, application validation remains necessary for user-friendly messages and business rules such as positive quantities or stock availability.

The current schema does not include a migration framework. Updating a deployed database by editing `schema.sql` and re-running it is not a complete migration strategy because existing installations may need carefully ordered changes or backfills. For ongoing development, adopt a migration tool, keep schema changes in version control, and apply changes to a backup or staging copy before production.

\newpage

## Page 18 — Customer Interface

The storefront is the default home page. It includes branding, navigation, a search field, an introductory banner, product cards, prices, stock quantities, and an add-to-basket control. Product descriptions are truncated visually through fixed card space rather than by changing the database value. If no products match a search, the page presents an empty state and a link to clear the search.

The visual design uses a light background, green accent color, rounded cards, and a responsive grid. On wide displays, product cards appear in multiple columns; on narrow displays, the layout reduces columns and adjusts spacing. The shared base template provides navigation and a basket count, while individual templates extend it for their page content.

The storefront shows dollar symbols directly in the template. There is no configurable currency, locale-aware formatting, tax display, or exchange conversion. Businesses outside a dollar-denominated use case should change currency formatting and define rounding and tax requirements before using the system. Product images are currently typographic placeholders rather than uploaded media.

\newpage

## Page 19 — Customer Registration and Login

Registration collects a name, email, and password. Email is normalized to lowercase and trimmed before duplicate lookup. The route checks for required values and a minimum password length, then hashes the password and inserts a customer. On success, the customer is directed to the login page. There is no email verification, so the address is not proven to belong to the registrant.

Login looks up the user by normalized email and checks the submitted password against the stored hash. On success it clears prior session state, restores the session basket, and sets the user's ID, name, and role. Administrators are redirected to the dashboard; customers return to the storefront. Invalid credentials produce a generic error message.

Sign-out clears the session. The implementation has no password-reset workflow, login throttling, CAPTCHA, account lockout, MFA, or notification of suspicious sign-in. These omissions may be acceptable for a local demonstration but should be prioritized before internet-facing operation. A public account system should also consider session expiration and secure cookie settings.

\newpage

## Page 20 — Basket and Checkout Workflow

The basket is a mapping from product IDs to quantities stored in the signed session cookie. Adding an item checks that the product exists, is active, and has stock. The basket page reads the current product records and calculates line totals. Updating the basket allows a quantity of zero to remove a line. Since the basket is session-based, it is not synchronized across browsers or devices and may be lost when the session cookie is removed or expires.

Checkout is available only to a signed-in customer. The route opens a MySQL transaction, fetches each requested product using `FOR UPDATE`, validates activity and stock, computes the total, inserts the order and order items, reduces inventory, and commits. If availability validation fails, the transaction is rolled back.

This workflow does not take payment and should not be interpreted as a paid order. It does not collect a delivery address. A future version should distinguish order placement from payment and fulfillment states, provide clear customer language, and protect the checkout form from cross-site request forgery.

\newpage

## Page 21 — Administrator Dashboard

The administrator dashboard combines overview metrics with product and order tables. The metric cards show the count of active products, sum of active stock units, pending orders, and products with five or fewer units. The threshold is currently fixed in the SQL and template logic rather than configured by product or business policy.

Product rows show a visual initial, name, category, price, stock, visibility status, and controls. The edit action loads the selected row into the form using small JavaScript functions. The form supports creation and editing. A separate action toggles the active flag, so products can be removed from the storefront without erasing their historical references.

Recent orders include customer name, date, total, current status, and a status selector. The list is limited to eight latest orders. There is no pagination, detailed order view, date filter, export, or search. Dashboard SQL uses subqueries for aggregate metrics; this is reasonable for a small dataset but should be reviewed as volume grows.

\newpage

## Page 22 — Product Management

Administrators can create a product by entering a name, category, description, price, and stock quantity. Category and description are optional. The route parses price as a decimal and stock as an integer and rejects blank names or negative values. Product edits use the same field set and update the matching product ID. The interface can clear the form or load a row for editing.

The price and quantity controls use HTML number inputs, but server-side validation remains the authoritative check. The SQL statements use placeholders for values, which prevents user input from being interpreted as SQL syntax. The product's name and descriptive text are rendered through Jinja's normal escaping behavior.

The current product model has no SKU, barcode, supplier, reorder point, unit of measure, variants, cost basis, or image. It also has no stock adjustment reason or history. For a retail or warehouse setting, those fields may be essential. The next design step should interview users about their product identifiers, replenishment practices, and whether they need multiple locations before expanding the schema.

\newpage

## Page 23 — Order Management

Administrators see recent orders and can assign one of the four defined statuses. The status control submits to an admin-only route that validates the supplied value against an allowlist. This protects the enum update from arbitrary status text and keeps the application's state vocabulary consistent with the schema.

The current interface offers only a limited view of an order. It does not show individual order items on the admin dashboard, customer contact details beyond the name, a shipping address, payment state, staff notes, or a full timeline. The customer order history does show line names, quantities, unit prices, total, date, and status.

Order status currently represents a simple manual lifecycle. A more complete workflow might distinguish payment pending, paid, picking, packed, shipped, delivered, refunded, and cancelled. Such changes should be designed with transition rules rather than allowing any status to be changed to any other status. Cancellation should also define stock restoration and payment refund behavior.

\newpage

## Page 24 — Security Measures Present

Several useful security practices are already present. Passwords are hashed using Werkzeug rather than stored directly. SQL values from forms are passed as connector parameters instead of being concatenated into query text. Administrator routes require the administrator role. Customer order history selects records by the current session user ID. Product registration does not let a customer choose an admin role. Configuration supports environment variables so secrets need not be embedded in source code.

These measures reduce specific risks but do not make the application security-complete. The Flask fallback secret in `app.py` is a development placeholder and must be replaced in `.env` with a random secret before use. `FLASK_DEBUG` must remain disabled for public deployment. The development server is not appropriate as a public production server.

Additional controls should include CSRF tokens for state-changing forms, HTTPS, secure cookie attributes, rate limits on login and registration, logging and monitoring, dependency updates, database least privilege, backup encryption, input-size limits, and a reviewed error-handling strategy. A security assessment should be performed before processing real customer data.

\newpage

## Page 25 — Security Gaps and Risk Treatment

The absence of CSRF protection means a malicious site could attempt to submit a state-changing request using a user's browser session. Flask's default session cookie is signed but is not, by itself, a CSRF defense. The login route has no rate limiting, increasing exposure to password guessing. The application does not configure a production cookie policy or force HTTPS; those responsibilities must be addressed at the application and reverse-proxy layers.

The database connector uses one configured account for all operations. On a deployed system this account should have only the privileges the app requires on `item_inventory`; schema administration should use a separate account. Raw server errors may reveal operational details if not handled carefully. Logging is minimal and does not yet provide an audit trail.

Risk treatment should be staged. Before any public launch: set a strong secret, configure TLS, disable debug, add CSRF protection and login throttling, create a least-privilege database user, review dependencies, configure backups, and test authorization boundaries. Then conduct a security review using the actual deployment topology. This report is a project description, not a penetration-test result.

\newpage

## Page 26 — User Experience and Visual Design

The interface aims for a restrained storefront aesthetic: a pale green hero region, a compact navigation bar, product cards with consistent spacing, and prominent action buttons. The administrator area uses metric cards and data tables suited to scanning. Forms include labels and placeholders. Empty states explain what the user can do next, while flash messages communicate success, warning, or error outcomes.

The stylesheet includes media queries for tablet and mobile widths. Product cards change from four columns on a wide screen to two columns on smaller screens. Navigation wraps, and the dashboard form adapts to fewer columns. The application is server-rendered, so core content is not dependent on a large JavaScript bundle.

Further UX work should include keyboard-only review, screen-reader checks, contrast measurements, focus indicators, form error summaries, and testing with real users. The current CSS includes hover styling but a complete focus design has not been formally assessed. External font loading also introduces an internet dependency for the preferred typography; local font alternatives are present as fallbacks.

\newpage

## Page 27 — Accessibility Considerations

Accessibility matters because customers and administrators may use keyboards, assistive technologies, browser zoom, or different visual settings. The templates use headings, labels, buttons, forms, and tables in recognizable semantic roles. Search input and product controls include some accessible names. This provides a useful starting point, but semantic HTML alone does not prove that an interface conforms to an accessibility standard.

The next review should check color contrast for text and status chips, visible keyboard focus on every interactive element, logical tab order, zoom and reflow at 200 percent, screen-reader announcements for flash messages, and whether the admin edit action communicates its product name. Decorative characters should be hidden from assistive technology where appropriate. Form errors should be associated with their input fields rather than appearing only as transient page-level messages.

The project has not been audited against WCAG 2.2 AA or another formal standard. Any accessibility statement should accurately reflect testing performed. A practical improvement cycle is to run automated checks, perform manual keyboard and screen-reader testing, then validate key flows with users who rely on assistive technology.

\newpage

## Page 28 — Installation and Configuration

The README describes Windows setup. The operator installs Python and MySQL, creates a virtual environment, installs `requirements.txt`, imports `schema.sql`, and creates a `.env` file from `.env.example`. The environment file holds the Flask secret and MySQL connection values. Then `create_admin.py` prompts for the initial administrator, and `app.py` starts a local server for development.

The application defaults to MySQL on localhost, port 3306, database `item_inventory`, user `root`, and an empty password if environment configuration is absent. That fallback is convenient only for a simple local installation and should not be relied upon. Configure explicit credentials before running the app. The `.env.example` is a template, not an active configuration file; it must be copied to `.env` and edited.

The instructions should be followed in order because the admin script and app both connect to the database. The schema must exist first. For a new device, recreate the Python environment and install dependencies rather than assuming an existing virtual environment is portable.

\newpage

## Page 29 — Local Execution and Network Access

For local development, `python app.py` starts Flask on port 5000, and the user opens `http://127.0.0.1:5000`. This development mode is convenient for coding and demonstration. It should not be exposed to the public internet. On Windows, Waitress is included and can serve the WSGI application with `waitress-serve --host=0.0.0.0 --port=5000 app:app`.

To allow another computer on a trusted local network to connect, the host can listen on all network interfaces, and the client can visit the host's private IP address at port 5000. The firewall must permit the connection on an appropriate private network profile. The database should remain accessible only to the application host or a private network segment.

Network access is not the same as public internet hosting. Router port forwarding, public DNS, TLS, server hardening, monitoring, and an operational backup plan are not configured by these local steps. The hosting provider and domain registrar are external services that must be selected and configured separately.

\newpage

## Page 30 — USB Transfer and Portability

The USB workflow transfers source files, not a complete computer environment. Copy the project folder, including Python source, SQL schema, templates, static assets, requirements, and documentation. On the destination computer, install Python and MySQL, copy the folder to a stable local drive, create a new virtual environment, install dependencies, create the database, and write a destination-specific `.env` file.

The Python virtual environment should not be treated as portable because it can contain machine-specific paths and compiled components. A fresh installation from `requirements.txt` is more reliable. MySQL itself is also a service that must be installed and started on the destination or reachable over a trusted network. The application files alone do not contain a running database server.

If existing records are needed, export the database with `mysqldump`, transfer the backup carefully, and import it into MySQL on the destination. The backup contains customer information and must be protected like private data. The report recommends copying to the local drive rather than running from removable media for reliable paths and performance.

\newpage

## Page 31 — Domain and Hosting Model

Flask is the application framework; it does not register a domain or provide a public hosting account. To make Stockroom available under a public domain, an operator needs a domain name, a server or managed hosting service, DNS configuration, TLS, and a process manager. The domain's DNS record must point to the server's public address. A reverse proxy can accept HTTPS on ports 443 and route requests to a WSGI application process bound on a private interface.

The README recommends a Linux VPS or managed Python host and a production WSGI server such as Waitress or Gunicorn. The exact configuration depends on the selected provider and should be documented once that provider is known. MySQL should not be exposed to the entire internet. A production deployment should use a restricted database account and private connectivity.

No domain has been purchased, DNS records changed, server provisioned, or certificate installed as part of this project. The deliverable is deployable application code and general guidance, not a live public service. Hosting selection should consider cost, backups, regional requirements, support, and data protection obligations.

\newpage

## Page 32 — Data Backup and Recovery

The current code does not automate backups. MySQL data will not be preserved by copying only the Flask source folder. Operators should schedule regular database dumps or provider-managed backups and periodically verify that the backups can be restored. Backup cadence should reflect how much recent order and inventory data the business can afford to lose.

A backup plan should specify who owns the process, where encrypted copies are stored, how long they are retained, and how recovery is tested. Copies should not all reside on the same device as the live database. USB backups should be encrypted or otherwise protected when they contain customer records, and lost removable media should be treated as a data incident.

Recovery steps should include restoring MySQL, applying the appropriate schema version, restoring data, rebuilding the Python environment, installing configuration secrets, and validating sign-in and order access. A test restore is more informative than simply checking that a backup file exists. Disaster recovery targets such as recovery time and recovery point objectives have not been defined for this starter project.

\newpage

## Page 33 — Error Handling and Logging

The application uses flash messages to communicate common validation and availability outcomes. The database helper closes the connection in a `finally` block. Checkout explicitly rolls back on an expected stock validation failure and commits only after all order operations succeed. These practices provide basic feedback and transaction cleanup.

There is no centralized error page, structured logging configuration, request ID, monitoring integration, or alerting. Unexpected database failures may surface as a server error. Operational logs should avoid recording passwords, session secrets, or full sensitive request bodies. Useful safe events include application startup, database connectivity failures, order creation identifiers, and administrative state changes, with suitable access controls and retention.

Production readiness requires an agreed error-handling policy. Users should receive a nontechnical message for unexpected errors while operators receive enough diagnostic context to resolve the issue. Health checks can confirm process and database status. Logging and metrics should be introduced with privacy and retention requirements in mind.

\newpage

## Page 34 — Performance and Scalability

For a small demonstration catalogue, the current query patterns are straightforward. Product search uses `LIKE` across three columns, and products are loaded in one query. The admin dashboard runs aggregate subqueries and loads the latest eight orders. The connection helper opens and closes a database connection per operation. This is easy to understand and sufficient for modest usage.

As data and traffic grow, performance should be measured rather than guessed. Potential improvements include connection pooling, pagination for product and order lists, full-text search, query-plan review, caching of stable catalogue data, and background jobs for notifications. A monitoring baseline should include request latency, database connection use, error rates, and slow queries.

The application has no load-test results or stated capacity target. Concurrent checkout behavior should be tested against the target MySQL engine and isolation settings. Scaling Flask processes also requires a suitable session strategy if sessions grow beyond signed cookies or must be revoked centrally. The current version should be described as a small-scale foundation, not a capacity-certified system.

\newpage

## Page 35 — Testing Strategy

No automated test suite is included in the delivered project, and the current project has not been verified against a live MySQL server or through browser-based end-to-end tests. A complete report should be clear about this limitation. The application logic has not been independently certified merely because the routes and templates exist.

A future test plan should include unit tests for input validation and price/quantity calculations, route tests for authentication and role boundaries, database integration tests for constraints and transactions, and end-to-end tests for customer checkout and administrator product management. Tests should verify that concurrent purchases cannot make stock negative, hidden products do not appear publicly, and a customer cannot inspect another customer's order history.

Test data should be isolated from real customer data. Automated tests can use a dedicated test database or controlled containers. Each release should run database migrations and tests in a staging environment before production. Manual usability and accessibility reviews should supplement automated checks rather than be replaced by them.

\newpage

## Page 36 — Known Limitations

The most important functional limitations are the absence of payment processing, shipping, addresses, notifications, product image upload, password reset, user administration, and inventory audit history. The application uses a session basket that is not shared between devices. Search is basic. The admin can review every order and its line items, but there is no dedicated order-detail page or audit timeline.

Order cancellation currently changes the status but does not restore inventory. This must be addressed before staff use cancellation as a final business action. There is no CSRF protection or login throttling. The default Flask secret is a placeholder, and safe deployment depends on operator configuration. The code has no formal migration system, test suite, or operational monitoring.

The checkout records an order without collecting payment, so users must not be led to believe payment was collected. The interface displays prices in dollars and has no tax or currency configuration. These are concrete scope boundaries, not hidden features. Any production proposal should list which limitations are acceptable and who owns each remaining work item.

\newpage

## Page 37 — Future Development Roadmap

**Priority 1: correctness and security.** Add CSRF protection, login rate limiting, secure cookie configuration, database least privilege, central error handling, and basic tests. Make cancellation restock transactionally and only once. Add an audit record for stock and order status changes.

**Priority 2: business essentials.** Add order detail views for administrators, address capture if delivery is required, email notifications, pagination, CSV export, configurable currency, and reorder thresholds. Add password-reset and email-verification workflows if accounts will be used publicly.

**Priority 3: media and operations.** Add validated product image upload with safe storage, schema migrations, scheduled database backups, health checks, structured logs, and deployment automation. Select a hosting provider and document the actual domain, DNS, TLS, and WSGI setup.

**Priority 4: expansion.** Consider supplier records, purchase orders, multiple locations, barcode support, sales reports, role-specific staff permissions, and payment integration. These features should follow user research; adding them without clear workflows can increase complexity without improving daily operations.

\newpage

## Page 38 — Deployment and Operations Checklist

Before a public launch, an operator should confirm that the intended host is selected and that the domain resolves to it. The app should run under a production WSGI server behind a reverse proxy that enforces HTTPS. Debug mode must be off. The Flask secret must be unique and protected. MySQL should use a dedicated account with only required privileges and should be reachable only from trusted hosts.

Operational readiness also requires a documented update and rollback process, database backups, restore testing, logs with retention limits, uptime monitoring, and an owner for security updates. The application should be tested with realistic but non-sensitive sample data in staging. Account and order flows should be verified with both roles. Public forms should receive CSRF and rate-limit protections before launch.

Domain registration and hosting are ongoing services with cost and renewal obligations. TLS renewal and dependency maintenance also need ownership. The app's README provides a deployment outline, but a live operational runbook must be tailored to the actual provider and infrastructure.

\newpage

## Page 39 — Conclusion

Stockroom demonstrates the main components of a Python and MySQL inventory application: account roles, a searchable product catalogue, a basket, transactional order placement, stock reduction, product administration, and order-status updates. It uses server-rendered Flask templates and a relational database with foreign keys. The visual system is responsive and the project includes environment configuration and setup documentation.

The application is best understood as a functional educational starter or prototype. It provides a clear foundation on which to build, but it is not yet a complete ecommerce platform or a deployed internet service. Payment, delivery, cancellation restocking, security hardening, tests, database migrations, backups, and production operations remain significant work.

The project can be moved to another computer by copying the source, installing Python and MySQL there, recreating the virtual environment, configuring `.env`, and importing a database backup when existing records are needed. A domain can be used after separate registration and hosting configuration. These steps keep the roles of application code, database service, and hosting provider clear.

\newpage

## Page 40 — Glossary and References to Project Files

**Administrator:** A signed-in user whose `role` is `admin` and who can manage catalogue visibility, products, stock, and order statuses.  
**Basket:** A session-held mapping of product identifiers to quantities before checkout.  
**Flask:** The Python web framework used for routes, sessions, and templates.  
**Jinja:** The server-side template engine used to render HTML pages.  
**MySQL:** The relational database used to persist account, product, and order records.  
**Order item:** A line in an order with a product-name snapshot, quantity, and unit price.  
**Wsgi:** The Python interface between a web application and a production server.  
**Environment variable:** A configuration value supplied outside application source code.

Project references:

- `app.py` — route and business logic implementation.
- `schema.sql` — database and table definitions.
- `create_admin.py` — initial administrator setup utility.
- `requirements.txt` — Python runtime dependencies.
- `.env.example` — configuration template.
- `README.md` — setup, local run, USB transfer, and hosting guidance.
- `templates/` and `static/style.css` — user interface implementation.

**End of report.**
