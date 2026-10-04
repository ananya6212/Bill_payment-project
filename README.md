# 🧾 BillBook

**A fast, simple web-based billing and inventory management app.**




---

## 📖 About

BillBook helps small businesses create customer invoices, track stock, and keep a clear history of sales, all from one clean dashboard.

## ✨ Features

| Feature | Description |
| --- | --- |
| 📊 **Dashboard** | Quick overview of your business at a glance |
| 📦 **Product Management** | Add, edit, and organize your products |
| 🏬 **Inventory & Stock** | Keep track of stock levels in real time |
| 🧾 **Customer Invoices** | Create invoices for customers in seconds |
| 🧮 **Auto Calculations** | Automatic subtotal, discount, and tax |
| 🕘 **Invoice History** | Browse and revisit past invoices |
| 📄 **PDF Invoices** | Generate and download PDF invoices |
| ⚙️ **Store Settings** | Configure your store details |

## 🛠️ Tech Stack

| Layer | Technology |
| --- | --- |
| **Backend** | Python, FastAPI, SQLAlchemy |
| **Templating** | Jinja2 |
| **Frontend** | HTML, CSS, JavaScript |
| **Database** | SQLite |

## 🚀 Getting Started

### Prerequisites

- Python 3.9 or higher
- pip

### Installation

**1. Clone the repository**

```bash
git clone https://github.com/<your-username>/quickbill.git
cd quickbill
```

**2. Create and activate a virtual environment**

```bash
# macOS / Linux
python -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

**3. Install dependencies**

```bash
pip install -r requirements.txt
```

**4. Run the application**

```bash
uvicorn app.main:app --reload
```

**5. Open in your browser**

```
http://127.0.0.1:8000
```

> 💡 FastAPI also provides interactive API docs at `http://127.0.0.1:8000/docs`.

## 🤝 Contributing

Contributions, issues, and feature requests are welcome! Feel free to open an issue or submit a pull request.


---

<div align="center">

Made with ❤️ using FastAPI

</div>
