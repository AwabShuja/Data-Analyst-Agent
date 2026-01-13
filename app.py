"""
AI Data Analyst Agent - Streamlit Interface
A well-organized UI to query the database using natural language.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from agent.sql_agent import SQLAgent
except ImportError:
    from src.agent.sql_agent import SQLAgent

# Page configuration
st.set_page_config(
    page_title="AI Data Analyst Agent",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 1rem;
        text-align: center;
    }
    .sql-box {
        background-color: #1e1e1e;
        color: #d4d4d4;
        padding: 1rem;
        border-radius: 5px;
        font-family: 'Courier New', monospace;
    }
    .success-badge {
        background-color: #28a745;
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 15px;
        font-size: 0.85rem;
    }
    .error-badge {
        background-color: #dc3545;
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 15px;
        font-size: 0.85rem;
    }
    .stTextArea textarea {
        font-size: 1.1rem;
    }
</style>
""", unsafe_allow_html=True)


def init_agent():
    """Initialize the SQL Agent (cached for performance)."""
    if 'agent' not in st.session_state:
        with st.spinner("🚀 Initializing AI Agent..."):
            st.session_state.agent = SQLAgent(db_path="data/processed/orders.db")
    return st.session_state.agent


def init_session_state():
    """Initialize session state variables."""
    if 'query_history' not in st.session_state:
        st.session_state.query_history = []
    if 'current_results' not in st.session_state:
        st.session_state.current_results = None


def render_sidebar():
    """Render the sidebar with database info and settings."""
    with st.sidebar:
        st.markdown("## 🗄️ Database Info")
        
        agent = init_agent()
        schema = agent.engine.get_schema_info()
        
        # Database statistics
        st.markdown("### 📊 Tables")
        for table_name, table_info in schema['tables'].items():
            with st.expander(f"📋 {table_name} ({table_info['row_count']:,} rows)"):
                st.markdown("**Columns:**")
                for col in table_info['columns']:
                    st.markdown(f"- `{col}`")
        
        st.markdown("---")
        
        # Example questions
        st.markdown("### 💡 Example Questions")
        example_questions = [
            "How many total orders are there?",
            "What is the average order amount?",
            "Show top 5 customers by total spending",
            "What are the sales by category?",
            "Which brand has the most orders?",
            "Show monthly order trends",
        ]
        
        for question in example_questions:
            if st.button(question, key=f"example_{question[:20]}", use_container_width=True):
                st.session_state.selected_question = question
        
        st.markdown("---")
        
        # Session statistics
        st.markdown("### 📈 Session Stats")
        if st.session_state.query_history:
            total = len(st.session_state.query_history)
            successful = sum(1 for q in st.session_state.query_history if q['success'])
            st.metric("Total Queries", total)
            st.metric("Success Rate", f"{(successful/total*100):.0f}%")
        else:
            st.info("No queries yet")
        
        if st.button("🗑️ Clear History", use_container_width=True):
            st.session_state.query_history = []
            st.session_state.current_results = None
            st.rerun()


def render_main_interface():
    """Render the main query interface."""
    # Header
    st.markdown('<p class="main-header">📊 AI Data Analyst Agent</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Ask questions about your data in natural language</p>', unsafe_allow_html=True)
    
    # Query input
    col1, col2 = st.columns([5, 1])
    
    with col1:
        # Check if an example question was selected
        default_question = st.session_state.get('selected_question', '')
        if default_question:
            del st.session_state.selected_question
        
        question = st.text_area(
            "🔍 Ask a question about your data:",
            value=default_question,
            placeholder="e.g., What are the top 10 selling products by revenue?",
            height=80,
            key="question_input"
        )
    
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        submit_button = st.button("🚀 Analyze", type="primary", use_container_width=True)
    
    # Process query
    if submit_button and question:
        process_query(question)
    
    # Display results
    if st.session_state.current_results:
        render_results(st.session_state.current_results)
    
    # Query history
    render_query_history()


def process_query(question: str):
    """Process the user's question using the SQL Agent."""
    agent = init_agent()
    
    with st.spinner("🤔 Analyzing your question..."):
        response = agent.ask(question)
    
    # Store in session state
    st.session_state.current_results = response
    st.session_state.query_history.append(response)


def render_results(response: dict):
    """Render the query results."""
    st.markdown("---")
    
    # Status header
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        if response['success']:
            st.success("✅ Query executed successfully!")
        else:
            st.error(f"❌ Query failed: {response.get('error', 'Unknown error')}")
    
    with col2:
        st.metric("Retries", response.get('retries', 0))
    
    with col3:
        exec_time = response.get('execution_time_ms', 0)
        st.metric("Execution Time", f"{exec_time:.0f}ms")
    
    # SQL Query
    st.markdown("### 🔧 Generated SQL")
    sql_query = response.get('sql_query', 'No SQL generated')
    st.code(sql_query, language="sql")
    
    # Results
    if response['success'] and response.get('results') is not None:
        results_df = response['results']
        
        st.markdown("### 📋 Results")
        
        # Results tabs
        tab1, tab2, tab3 = st.tabs(["📊 Data Table", "📈 Visualization", "💬 Interpretation"])
        
        with tab1:
            st.dataframe(results_df, use_container_width=True, height=400)
            
            # Download button
            csv = results_df.to_csv(index=False)
            st.download_button(
                label="📥 Download as CSV",
                data=csv,
                file_name=f"query_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        
        with tab2:
            render_visualization(results_df)
        
        with tab3:
            interpretation = response.get('interpretation', 'No interpretation available')
            st.markdown(f"""
            <div style="background-color: #f0f8ff; padding: 1.5rem; border-radius: 10px; border-left: 4px solid #1f77b4;">
                <h4 style="margin-top: 0;">💡 AI Interpretation</h4>
                <p style="font-size: 1.1rem; line-height: 1.6;">{interpretation}</p>
            </div>
            """, unsafe_allow_html=True)


def render_visualization(df: pd.DataFrame):
    """Render automatic visualization based on data type."""
    if df.empty:
        st.info("No data to visualize")
        return
    
    # Detect data types
    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
    
    if len(df) == 1:
        # Single row - show as metrics
        st.markdown("**Single Result:**")
        cols = st.columns(min(len(df.columns), 4))
        for i, col in enumerate(df.columns):
            with cols[i % len(cols)]:
                value = df[col].iloc[0]
                if isinstance(value, (int, float)):
                    st.metric(col, f"{value:,.2f}" if isinstance(value, float) else f"{value:,}")
                else:
                    st.metric(col, str(value))
    
    elif len(categorical_cols) >= 1 and len(numeric_cols) >= 1:
        # Create bar chart
        cat_col = categorical_cols[0]
        num_col = numeric_cols[0]
        
        chart_type = st.selectbox("Chart Type", ["Bar Chart", "Pie Chart", "Line Chart"])
        
        if chart_type == "Bar Chart":
            fig = px.bar(
                df.head(20), 
                x=cat_col, 
                y=num_col,
                title=f"{num_col} by {cat_col}",
                color=num_col,
                color_continuous_scale="Blues"
            )
        elif chart_type == "Pie Chart":
            fig = px.pie(
                df.head(10), 
                names=cat_col, 
                values=num_col,
                title=f"{num_col} Distribution by {cat_col}"
            )
        else:
            fig = px.line(
                df.head(50), 
                x=cat_col, 
                y=num_col,
                title=f"{num_col} Trend",
                markers=True
            )
        
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    elif len(numeric_cols) >= 2:
        # Scatter plot for multiple numeric columns
        fig = px.scatter(
            df,
            x=numeric_cols[0],
            y=numeric_cols[1],
            title=f"{numeric_cols[1]} vs {numeric_cols[0]}"
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    else:
        st.info("📊 Auto-visualization not available for this data structure. View the data table instead.")


def render_query_history():
    """Render the query history section."""
    if not st.session_state.query_history:
        return
    
    st.markdown("---")
    st.markdown("### 📜 Query History")
    
    # Show history in reverse order (most recent first)
    for i, query in enumerate(reversed(st.session_state.query_history)):
        idx = len(st.session_state.query_history) - i
        status = "✅" if query['success'] else "❌"
        
        with st.expander(f"{status} Query #{idx}: {query['question'][:60]}..."):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"**Question:** {query['question']}")
                st.code(query.get('sql_query', 'N/A'), language="sql")
            
            with col2:
                st.metric("Retries", query.get('retries', 0))
                st.metric("Time", f"{query.get('execution_time_ms', 0):.0f}ms")
            
            if not query['success']:
                st.error(f"Error: {query.get('error', 'Unknown')}")


def render_help_page():
    """Render the help/documentation page."""
    st.markdown("## 📚 Help & Documentation")
    
    st.markdown("""
    ### How to Use This App
    
    1. **Ask a Question**: Type your question in natural language in the text box
    2. **Click Analyze**: The AI will generate SQL and fetch results
    3. **View Results**: See the data table, visualizations, and AI interpretation
    
    ### Example Questions
    
    | Category | Example |
    |----------|---------|
    | **Aggregations** | "What is the total revenue?" |
    | **Top N** | "Show top 5 customers by order count" |
    | **Grouping** | "What are the sales by category?" |
    | **Filtering** | "Show orders above $1000" |
    | **Trends** | "Show monthly order trends" |
    | **Joins** | "Which brand has the highest average order value?" |
    
    ### Database Schema
    
    The database contains these tables:
    - **orders**: Order transactions with amounts and dates
    - **customers**: Customer information
    - **products**: Product catalog
    - **brands**: Brand information
    - **categories**: Product categories
    
    ### Tips
    
    - Be specific with your questions
    - Use column names when you know them
    - Ask for "top N" results to limit data
    - Check the SQL tab to understand the generated query
    """)


def main():
    """Main application entry point."""
    init_session_state()
    
    # Navigation
    page = st.sidebar.radio(
        "Navigation",
        ["🔍 Query Interface", "📚 Help"],
        label_visibility="collapsed"
    )
    
    # Render sidebar (always visible)
    render_sidebar()
    
    # Render main content based on navigation
    if page == "🔍 Query Interface":
        render_main_interface()
    else:
        render_help_page()


if __name__ == "__main__":
    main()
