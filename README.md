# 🤖 AI Data Analyst Agent

An intelligent SQL agent that converts natural language business questions into SQL queries, executes them safely on a database, and returns insights with recommendations - all automatically.

> **Portfolio Project**: Demonstrates LLM integration, database design, SQL agent orchestration, and production safety patterns for AI/ML engineering roles.

---

## 🎯 What This Project Does

**User asks**: _"Which category has the highest repeat customers?"_

**Agent does**:
1. Understands the question
2. Writes SQL query automatically
3. Executes it safely (read-only)
4. Returns results in plain English
5. Provides business recommendations

**Why recruiters care**: This is directly useful in analytics teams and demonstrates SQL safety, LLM integration, and autonomous agents.

---

## 📁 Project Structure

```
AI Data Analyst Agent/
├── data/
│   ├── raw/                      # Original CSV (32.4K orders)
│   └── processed/                # SQLite DB (6.2 MB) + enriched CSV
├── src/
│   ├── database/                 # Database setup & query helpers
│   │   ├── setup_database.py    # Creates normalized star schema
│   │   └── db_helper.py         # Query utilities & verification
│   ├── utils/
│   │   └── data_enrichment.py   # Smart data pipeline
│   └── agent/                    # LLM agent implementation (Phase 2+)
├── config/
│   └── config.yaml              # Centralized configuration
├── README.md                     # Complete project documentation (this file)
├── requirements.txt              # Python dependencies
└── .gitignore                    # Git exclusions
```

---

## 📊 Dataset Overview

### What's in the Database
This is a **real e-commerce dataset** with customer orders from May-July 2023, enriched with transaction details.

| Metric | Value |
|--------|-------|
| **Total Orders** | 32,400 |
| **Unique Customers** | 18,566 |
| **Products** | 18,433 |
| **Brands** | 297 |
| **Business Categories** | 10 (Food, Fashion, Grocery, etc.) |
| **Total Revenue** | ₹249.7M (~$3M USD) |
| **Avg Order Value** | ₹7,708 |
| **Time Period** | May 1 - July 31, 2023 |
| **Channels** | Online (93%) + In-store (7%) |

### Database Schema (Star Schema Design)

```
                    ┌─────────────┐
                    │ categories  │
                    │             │
                    │ category_id │
                    │ name        │
                    │ type        │
                    └──────┬──────┘
                           │
                           │
    ┌──────────┐    ┌─────▼──────┐    ┌─────────────┐
    │  brands  │◄───┤   orders   ├───►│  customers  │
    │          │    │  (FACT)    │    │             │
    │ brand_id │    │            │    │ customer_id │
    │ name     │    │ order_id   │    │ first_order │
    └──────────┘    │ customer   │    │ total_orders│
                    │ product    │    │ total_spent │
                    │ brand      │    └─────────────┘
                    │ category   │
                    │ date       │
    ┌──────────┐    │ quantity   │
    │ products │◄───┤ price      │
    │          │    │ revenue    │
    │product_id│    └────────────┘
    │ name     │
    │ brand    │
    │ category │
    │ avg_price│
    └──────────┘
```

**Tables Explained:**

1. **orders** (Fact Table) - Main transaction records
   - Every order with customer, product, pricing, date
   - 32,400 rows

2. **customers** (Dimension) - Customer profiles
   - Pre-aggregated metrics: total_orders, total_spent, favorite_category
   - 18,566 unique customers

3. **products** (Dimension) - Product catalog
   - Product names, brands, categories, average prices
   - 18,433 products

4. **brands** (Dimension) - Merchant/brand information
   - 297 brands (foodpanda, Daraz, etc.)

5. **categories** (Dimension) - Business categories
   - 10 categories: Food & Restaurants, Fashion, Grocery, etc.

---

## 🚀 How to Run This Project

### Prerequisites
```bash
Python 3.9+
```

### Installation
```bash
# Clone/download the project
cd "AI Data Analyst Agent"

# Install dependencies
pip install -r requirements.txt
```

### Database Setup (Already Done!)
The database is already created. To recreate from scratch:
```bash
python src/utils/data_enrichment.py     # Enriches raw CSV
python src/database/setup_database.py   # Creates SQLite DB
```

### Quick Verification
```python
# Run this to see database overview
python src/database/db_helper.py
```

### Example: Query the Database
```python
from src.database.db_helper import DatabaseHelper

with DatabaseHelper() as db:
    # Example: Top 5 revenue categories
    query = """
        SELECT c.category_name, 
               SUM(o.total_amount) as revenue,
               COUNT(o.order_id) as orders
        FROM orders o
        JOIN categories c ON o.category_id = c.category_id
        GROUP BY c.category_name
        ORDER BY revenue DESC
        LIMIT 5
    """
    result = db.execute_query(query)
    print(result)
```

---

## 🛠️ Implementation Phases

### ✅ Phase 1: Data Setup **[COMPLETED]**

**What was built:**
- ✅ Converted flat CSV to normalized star schema database
- ✅ Enriched data with order amounts, quantities, product names
- ✅ Created 5 properly indexed tables with foreign keys
- ✅ Verified 100% data integrity
- ✅ Added realistic pricing using statistical distributions

**Key accomplishments:**
- 806 lines of production-quality Python code
- Configuration-driven design (no hardcoded values)
- Professional folder structure
- Type hints and docstrings throughout

---

### 🔄 Phase 2: Basic Agent (Next)

**What will be built:**
- LLM integration (OpenAI GPT-4 or local Ollama)
- LangChain SQL agent with database tools
- Natural language → SQL conversion
- Result formatter (SQL output → plain English)
- Basic insight generation

**Example interaction:**
```
User: "Show me top 5 customers by spending"

Agent:
1. Generates: SELECT customer_id, total_spent FROM customers ORDER BY total_spent DESC LIMIT 5
2. Executes query
3. Returns: "The top 5 customers are... Customer #3681746 spent ₹720,314..."
```

---

### 🔄 Phase 3: Safety & Validation

**What will be built:**
- **Query Safety Layer**: Block DELETE/DROP/UPDATE, enforce read-only
- **Row Limit Enforcement**: Prevent full table scans (max 10,000 rows)
- **Schema Validator**: Check if columns/tables exist before executing
- **Self-Correction Loop**: If query fails, agent sees error and rewrites
- **Audit Logging**: Track all queries, especially rejected ones

**Why this matters:**
SQL can be dangerous. Showing you understand LLM safety is crucial for production roles.

---

### 🔄 Phase 4: Polish & Demo

**What will be built:**
- **A/B Comparison**: Baseline GPT vs. your enhanced agent
- **Metrics Dashboard**: Success rate, query safety violations, latency
- **Web UI**: Streamlit/Gradio interface for demos
- **Deployment**: Docker container + HuggingFace Spaces hosting

---

## 🔧 Tech Stack

### Current (Phase 1)
- **Database**: SQLite 3
- **Data Processing**: Pandas, NumPy
- **Configuration**: PyYAML
- **Language**: Python 3.9+

### Upcoming (Phase 2+)
- **LLM**: OpenAI GPT-4 or Ollama (Llama 3)
- **Framework**: LangChain (SQL agent, tools, chains)
- **UI**: Streamlit or Gradio
- **Deployment**: Docker, HuggingFace Spaces

---

## 📈 Sample Business Questions (What the Agent Will Answer)

### Beginner Level
1. How many total customers do we have?
2. What is our total revenue?
3. What is the average order value?
4. How many customers made their first purchase in June?

### Intermediate Level
5. Which category has the highest repeat customers?
6. What's the revenue split between online and in-store?
7. Show monthly revenue trends
8. Who are the top 10 customers by spending?
9. Which brands have the highest average order value?

### Advanced Level
10. What's the month-over-month revenue growth rate?
11. Calculate customer retention rate
12. Find customers who haven't ordered in 30 days but were previously active
13. Identify products with declining sales over the period
14. Which customer segment has highest AOV by category?

The agent will be tested on 30+ such questions to measure accuracy.

---

## 💡 Why This Project Stands Out

### For Recruiters

✅ **Production ML System** - Not a Jupyter notebook demo. Full modular codebase with proper architecture.

✅ **SQL Safety** - Phase 3 will show deep understanding of LLM risks and mitigation strategies.

✅ **Database Skills** - Normalized schema, indexing, query optimization show data engineering competence.

✅ **Agent Orchestration** - LangChain tools, self-correction loops, multi-step reasoning.

✅ **Measurable Results** - A/B testing framework proves your agent is better than baseline.

### Technical Highlights

1. **Star Schema Design**: Dimensional modeling (Kimball methodology) for analytics
2. **Smart Data Enrichment**: Log-normal price distributions, weighted quantities
3. **Configuration Management**: Centralized config.yaml, no hardcoded values
4. **Error Handling**: Proper try-catch, connection management, validators
5. **Scalable Architecture**: Easy to add new tables, questions, LLMs

---

## 🎨 Code Quality Features

### Professional Engineering Practices
- **Modular Design**: Separation of concerns (database / utils / agent)
- **Type Hints**: All functions properly typed
- **Docstrings**: Every class and function documented
- **Configuration-Driven**: Settings in YAML, not code
- **Context Managers**: Proper resource cleanup (database connections)
- **Logging Ready**: Structured for easy debugging

### Data Engineering Best Practices
- **Normalization**: Proper 3NF schema, no redundancy
- **Indexing**: Strategic indexes on foreign keys and filter columns
- **Referential Integrity**: All foreign keys validated
- **Data Quality**: No nulls, no duplicates, consistent formats
- **Reproducibility**: Random seeds for consistent enrichment

---

## 🧪 How to Verify Phase 1 Works

Run this quick test:

```python
from src.database.db_helper import DatabaseHelper

with DatabaseHelper() as db:
    # 1. Check tables exist
    tables = db.list_tables()
    print(f"✓ Found {len(tables)} tables: {tables}")
    
    # 2. Check data quality
    summary = db.get_database_summary()
    print(f"✓ Total rows: {summary['total_rows']:,}")
    
    # 3. Check relationships
    checks = db.verify_relationships()
    print(f"✓ Foreign keys valid: {all(checks.values())}")
    
    # 4. Run sample query
    result = db.execute_query("SELECT COUNT(*) as total FROM orders")
    print(f"✓ Sample query works: {result['total'].iloc[0]:,} orders")
```

Expected output:
```
✓ Found 5 tables: ['brands', 'categories', 'customers', 'orders', 'products']
✓ Total rows: 69,709
✓ Foreign keys valid: True
✓ Sample query works: 32,400 orders
```

---

## 📊 Database Statistics

### Revenue by Category (Top 5)
| Category | Revenue | Orders | Avg Order Value |
|----------|---------|--------|-----------------|
| Market Place | ₹146.0M | 9,746 | ₹14,982 |
| Food & Restaurants | ₹48.5M | 15,609 | ₹3,110 |
| Stores & Grocery | ₹26.2M | 3,259 | ₹8,036 |
| Fashion | ₹18.1M | 1,489 | ₹12,172 |
| Health, Beauty & Gifts | ₹4.1M | 925 | ₹4,388 |

### Customer Insights
- **Repeat Customers**: 5,234 (28.2% of total)
- **One-Time Buyers**: 13,332 (71.8%)
- **Avg Orders per Customer**: 1.75
- **Top Customer Spend**: ₹720,314 (Customer #3681746)

### Temporal Trends
| Month | Orders | Revenue | Avg Order Value |
|-------|--------|---------|-----------------|
| May 2023 | 5,442 | ₹41.1M | ₹7,553 |
| June 2023 | 11,339 | ₹89.8M | ₹7,919 |
| July 2023 | 15,619 | ₹118.8M | ₹7,609 |

**Growth**: 187% order increase from May to July!

---

## 🔐 Configuration

All settings are in `config/config.yaml`:

```yaml
database:
  raw_csv_path: "data/raw/Order_by_Outlet_type.csv"
  processed_db_path: "data/processed/orders.db"

enrichment:
  price_ranges:
    "Food & Restaurants": [200, 3000]
    "Fashion": [800, 12000]
    # ... etc

schema:
  version: "1.0"
```

---

## 📈 Roadmap

- [x] **Phase 1**: Data Setup ✅ **COMPLETED**
- [ ] **Phase 2**: Basic Agent (LLM + LangChain)
- [ ] **Phase 3**: Safety & Validation
- [ ] **Phase 4**: Polish & Demo

---

## 🤝 Contributing / Next Steps

**Phase 1 is production-ready!** 

To proceed to Phase 2:
1. Decide: OpenAI GPT-4 (paid, $5-10 total cost) or Ollama (free, local)
2. Get API key if using OpenAI
3. Ready to build the SQL agent!

---

## 📧 Project Info

**Status**: Phase 1 Complete ✅  
**Last Updated**: January 5, 2026  
**Version**: 1.0.0  

**Dataset**: E-commerce orders (May-July 2023)  
**Database**: SQLite, 6.2 MB, Star Schema  
**Code Quality**: 806 lines, modular, type-hinted, documented
