"""
Test Questions Dataset for Agent Evaluation.
30 business questions categorized by difficulty with expected SQL patterns.
"""

from typing import List, Dict, Any


class TestQuestions:
    """
    Curated test questions for evaluating the SQL agent.
    Each question has difficulty level and expected SQL patterns for validation.
    """
    
    # Easy: Simple aggregations, single table queries
    EASY = [
        {
            "id": 1,
            "question": "What is the total number of orders?",
            "difficulty": "easy",
            "expected_patterns": ["COUNT", "orders"],
            "expected_result_type": "single_value",
            "category": "aggregation"
        },
        {
            "id": 2,
            "question": "What is our total revenue?",
            "difficulty": "easy",
            "expected_patterns": ["SUM", "total_price", "orders"],
            "expected_result_type": "single_value",
            "category": "aggregation"
        },
        {
            "id": 3,
            "question": "How many unique customers do we have?",
            "difficulty": "easy",
            "expected_patterns": ["COUNT", "DISTINCT", "customer"],
            "expected_result_type": "single_value",
            "category": "aggregation"
        },
        {
            "id": 4,
            "question": "How many products are in our catalog?",
            "difficulty": "easy",
            "expected_patterns": ["COUNT", "products"],
            "expected_result_type": "single_value",
            "category": "aggregation"
        },
        {
            "id": 5,
            "question": "What is the average order value?",
            "difficulty": "easy",
            "expected_patterns": ["AVG", "total_price", "orders"],
            "expected_result_type": "single_value",
            "category": "aggregation"
        },
        {
            "id": 6,
            "question": "How many brands do we work with?",
            "difficulty": "easy",
            "expected_patterns": ["COUNT", "brands"],
            "expected_result_type": "single_value",
            "category": "aggregation"
        },
        {
            "id": 7,
            "question": "Show me all category names",
            "difficulty": "easy",
            "expected_patterns": ["SELECT", "category_name", "categories"],
            "expected_result_type": "list",
            "category": "simple_select"
        },
        {
            "id": 8,
            "question": "What is the highest order amount?",
            "difficulty": "easy",
            "expected_patterns": ["MAX", "total_price", "orders"],
            "expected_result_type": "single_value",
            "category": "aggregation"
        },
        {
            "id": 9,
            "question": "What is the lowest order amount?",
            "difficulty": "easy",
            "expected_patterns": ["MIN", "total_price", "orders"],
            "expected_result_type": "single_value",
            "category": "aggregation"
        },
        {
            "id": 10,
            "question": "How many orders were placed in total?",
            "difficulty": "easy",
            "expected_patterns": ["COUNT", "orders"],
            "expected_result_type": "single_value",
            "category": "aggregation"
        }
    ]
    
    # Medium: JOINs, GROUP BY, basic analytics
    MEDIUM = [
        {
            "id": 11,
            "question": "Show me the top 5 best-selling products",
            "difficulty": "medium",
            "expected_patterns": ["JOIN", "products", "SUM", "quantity", "LIMIT 5", "ORDER BY"],
            "expected_result_type": "top_n",
            "category": "ranking"
        },
        {
            "id": 12,
            "question": "What is the total revenue by category?",
            "difficulty": "medium",
            "expected_patterns": ["JOIN", "categories", "SUM", "GROUP BY"],
            "expected_result_type": "grouped",
            "category": "grouping"
        },
        {
            "id": 13,
            "question": "Which brands have the highest revenue?",
            "difficulty": "medium",
            "expected_patterns": ["JOIN", "brands", "SUM", "GROUP BY", "ORDER BY"],
            "expected_result_type": "ranked_list",
            "category": "ranking"
        },
        {
            "id": 14,
            "question": "How many customers are from each country?",
            "difficulty": "medium",
            "expected_patterns": ["SELECT", "customers", "COUNT", "GROUP BY", "country"],
            "expected_result_type": "grouped",
            "category": "grouping"
        },
        {
            "id": 15,
            "question": "What is the average order value by brand?",
            "difficulty": "medium",
            "expected_patterns": ["JOIN", "brands", "AVG", "GROUP BY"],
            "expected_result_type": "grouped",
            "category": "grouping"
        },
        {
            "id": 16,
            "question": "Show me the top 10 customers by total spending",
            "difficulty": "medium",
            "expected_patterns": ["customers", "SUM", "total_spent", "LIMIT 10", "ORDER BY"],
            "expected_result_type": "top_n",
            "category": "ranking"
        },
        {
            "id": 17,
            "question": "How many orders per category?",
            "difficulty": "medium",
            "expected_patterns": ["JOIN", "categories", "COUNT", "GROUP BY"],
            "expected_result_type": "grouped",
            "category": "grouping"
        },
        {
            "id": 18,
            "question": "What are the top 3 cities by number of orders?",
            "difficulty": "medium",
            "expected_patterns": ["customers", "COUNT", "city", "LIMIT 3", "ORDER BY"],
            "expected_result_type": "top_n",
            "category": "ranking"
        },
        {
            "id": 19,
            "question": "Show me revenue per month",
            "difficulty": "medium",
            "expected_patterns": ["SUM", "strftime", "GROUP BY", "order_date"],
            "expected_result_type": "time_series",
            "category": "temporal"
        },
        {
            "id": 20,
            "question": "Which category has the most products?",
            "difficulty": "medium",
            "expected_patterns": ["JOIN", "categories", "COUNT", "products", "GROUP BY", "ORDER BY"],
            "expected_result_type": "single_value",
            "category": "grouping"
        }
    ]
    
    # Hard: Complex JOINs, subqueries, advanced analytics
    HARD = [
        {
            "id": 21,
            "question": "Which category has the highest average order value?",
            "difficulty": "hard",
            "expected_patterns": ["JOIN", "categories", "AVG", "total_price", "GROUP BY", "ORDER BY"],
            "expected_result_type": "single_value",
            "category": "complex_aggregation"
        },
        {
            "id": 22,
            "question": "Compare total revenue between May and July 2023",
            "difficulty": "hard",
            "expected_patterns": ["SUM", "strftime", "2023-05", "2023-07"],
            "expected_result_type": "comparison",
            "category": "temporal_comparison"
        },
        {
            "id": 23,
            "question": "What is the revenue growth from May to June 2023?",
            "difficulty": "hard",
            "expected_patterns": ["SUM", "strftime", "2023-05", "2023-06"],
            "expected_result_type": "growth_rate",
            "category": "temporal_comparison"
        },
        {
            "id": 24,
            "question": "Which brand has the highest average order quantity?",
            "difficulty": "hard",
            "expected_patterns": ["JOIN", "brands", "AVG", "quantity", "GROUP BY", "ORDER BY"],
            "expected_result_type": "single_value",
            "category": "complex_aggregation"
        },
        {
            "id": 25,
            "question": "Show me the top 5 products by revenue in June 2023",
            "difficulty": "hard",
            "expected_patterns": ["JOIN", "products", "SUM", "2023-06", "LIMIT 5", "ORDER BY"],
            "expected_result_type": "top_n",
            "category": "filtered_ranking"
        },
        {
            "id": 26,
            "question": "What percentage of total revenue comes from the top category?",
            "difficulty": "hard",
            "expected_patterns": ["JOIN", "categories", "SUM", "GROUP BY"],
            "expected_result_type": "percentage",
            "category": "percentage_analysis"
        },
        {
            "id": 27,
            "question": "Which customers have made more than 10 orders?",
            "difficulty": "hard",
            "expected_patterns": ["customers", "total_orders", "WHERE", ">", "10"],
            "expected_result_type": "filtered_list",
            "category": "filtering"
        },
        {
            "id": 28,
            "question": "What is the average number of items per order by category?",
            "difficulty": "hard",
            "expected_patterns": ["JOIN", "categories", "AVG", "quantity", "GROUP BY"],
            "expected_result_type": "grouped",
            "category": "complex_aggregation"
        },
        {
            "id": 29,
            "question": "Show me brands that have more than 1000 total orders",
            "difficulty": "hard",
            "expected_patterns": ["JOIN", "brands", "COUNT", "GROUP BY", "HAVING", ">", "1000"],
            "expected_result_type": "filtered_list",
            "category": "filtering"
        },
        {
            "id": 30,
            "question": "What is the month-over-month revenue growth rate?",
            "difficulty": "hard",
            "expected_patterns": ["SUM", "strftime", "GROUP BY", "order_date"],
            "expected_result_type": "growth_series",
            "category": "temporal_comparison"
        }
    ]
    
    @classmethod
    def get_all_questions(cls) -> List[Dict[str, Any]]:
        """Get all test questions."""
        return cls.EASY + cls.MEDIUM + cls.HARD
    
    @classmethod
    def get_by_difficulty(cls, difficulty: str) -> List[Dict[str, Any]]:
        """Get questions by difficulty level."""
        if difficulty.lower() == "easy":
            return cls.EASY
        elif difficulty.lower() == "medium":
            return cls.MEDIUM
        elif difficulty.lower() == "hard":
            return cls.HARD
        else:
            raise ValueError(f"Invalid difficulty: {difficulty}")
    
    @classmethod
    def get_by_category(cls, category: str) -> List[Dict[str, Any]]:
        """Get questions by category."""
        all_questions = cls.get_all_questions()
        return [q for q in all_questions if q["category"] == category]
    
    @classmethod
    def get_question_by_id(cls, question_id: int) -> Dict[str, Any]:
        """Get a specific question by ID."""
        all_questions = cls.get_all_questions()
        for q in all_questions:
            if q["id"] == question_id:
                return q
        raise ValueError(f"Question ID {question_id} not found")
    
    @classmethod
    def get_summary(cls) -> Dict[str, Any]:
        """Get summary statistics about the test questions."""
        all_questions = cls.get_all_questions()
        
        return {
            "total_questions": len(all_questions),
            "by_difficulty": {
                "easy": len(cls.EASY),
                "medium": len(cls.MEDIUM),
                "hard": len(cls.HARD)
            },
            "categories": list(set(q["category"] for q in all_questions))
        }
