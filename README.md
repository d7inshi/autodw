# AutoDW: Data Warehouse Intelligence Agent 🚀
> **Bridge Databases, Data Warehouses, and LLMs with Automated Schema Processing**

AutoDW is an intelligent agent designed to automate interactions between databases, data warehouses, and Large Language Models (LLMs). It provides tools for **parsing sequential SQL into JSON**, **serializing database schemas**, and **generating schema annotations automatically**, supporting SQLite, MySQL, PostgreSQL, and more.

---

## ✨ Key Features
| Feature Category          | Functionality                          | Supported Databases |
|---------------------------|----------------------------------------|---------------------|
| **SQL → JSON Parser**     | Convert sequential SQL to structured JSON | SQLite, MySQL, PostgreSQL |
| **Schema Serialization**  | Extract and serialize database schema metadata | All supported DBs |
| **Auto Schema Annotation**| Generate human-readable schema comments | All supported DBs |
| **Multi-DB Compatibility**| Unified interface for SQLite/MySQL/PostgreSQL | ✅ |

---

## 🚧 Function Roadmap
| Implemented Features                      | Planned Features |
|-------------------------------------------|------------------|
| SQL → JSON conversion                      | **LLM-based query optimization** |
| Schema metadata extraction (tables, columns)| **Automated ETL script generation** |
| Basic schema annotation generation        | **Schema diff visualization** |
| CLI for local DB interaction               | **Cloud DB support (BigQuery, Snowflake)** |
| JSON output for integration with LLM tools | **REST API for remote access** |

---

## ⚙️ Installation
```bash
pip install autodw