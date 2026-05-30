"""
Benchmark Dataset
------------------
Labeled resume/JD pairs with known relevance scores.
Used to evaluate matcher quality objectively.

Relevance scale:
  3 = perfect match (strong candidate)
  2 = good match (viable candidate)
  1 = partial match (weak candidate)
  0 = no match (irrelevant)

In a production system this would come from:
  - Recruiter feedback (did they interview this candidate?)
  - Historical hiring data
  - Human annotation

For portfolio purposes we use synthetic but realistic pairs.
"""

BENCHMARK_DATA = [
    # ── Query 1: Senior ML Engineer ──────────────────────────────────────────
    {
        "query_id": 1,
        "job_description": """
        Senior Machine Learning Engineer required. Must have 5+ years Python experience,
        strong PyTorch or TensorFlow background, experience deploying ML models to
        production on AWS or GCP. MLOps experience with MLflow or Kubeflow required.
        Strong NLP background preferred. Docker and Kubernetes experience needed.
        Team leadership experience a plus.
        """,
        "candidates": [
            {
                "id": 101,
                "relevance": 3,
                "resume": """
                Senior ML Engineer with 7 years Python experience. Led team of 5 engineers
                building NLP models using PyTorch and Transformers. Deployed 12 models to
                AWS SageMaker using Docker and Kubernetes. Set up MLflow tracking for entire
                ML team. Strong background in BERT, GPT fine-tuning. TensorFlow experience.
                Reduced model inference latency by 40% through ONNX optimization.
                """
            },
            {
                "id": 102,
                "relevance": 2,
                "resume": """
                ML Engineer with 4 years experience. Python, scikit-learn, PyTorch.
                Deployed models to AWS EC2. Some Docker experience. Built recommendation
                systems and classification models. Experience with pandas, numpy.
                Familiar with MLflow for experiment tracking. No Kubernetes experience.
                """
            },
            {
                "id": 103,
                "relevance": 1,
                "resume": """
                Data Analyst with 3 years experience. Python, SQL, Tableau.
                Some machine learning with scikit-learn. Built dashboards and reports.
                Currently learning PyTorch through online courses. No production ML experience.
                Familiar with AWS basics.
                """
            },
            {
                "id": 104,
                "relevance": 0,
                "resume": """
                Frontend Developer with 5 years React and JavaScript experience.
                Built responsive web applications. Some Python scripting.
                No machine learning experience. HTML, CSS, TypeScript expert.
                """
            },
        ]
    },

    # ── Query 2: Data Scientist ───────────────────────────────────────────────
    {
        "query_id": 2,
        "job_description": """
        Data Scientist with strong statistics background. Python required,
        R preferred. Experience with A/B testing, hypothesis testing, regression
        analysis. SQL proficiency required. Experience with Spark or Databricks.
        Visualization skills with Tableau or Power BI. Business communication skills.
        """,
        "candidates": [
            {
                "id": 201,
                "relevance": 3,
                "resume": """
                Data Scientist with 5 years experience. Expert in Python and R.
                Led A/B testing framework used by 3M daily users. Strong statistics
                background — hypothesis testing, regression, time series analysis.
                Advanced SQL, Spark, Databricks. Tableau certified. Presented findings
                to C-suite executives. PhD in Statistics.
                """
            },
            {
                "id": 202,
                "relevance": 2,
                "resume": """
                Data Scientist with 3 years Python experience. Good statistics knowledge.
                Built regression and classification models. SQL proficient. Some A/B testing.
                Matplotlib and seaborn for visualization. Learning Tableau. Familiar with
                basic Spark operations.
                """
            },
            {
                "id": 203,
                "relevance": 1,
                "resume": """
                Business Analyst with SQL and Excel experience. Some Python scripting.
                Created reports and dashboards in Power BI. Familiar with basic statistics.
                No machine learning or A/B testing experience. Strong communication skills.
                """
            },
            {
                "id": 204,
                "relevance": 0,
                "resume": """
                DevOps Engineer with Kubernetes, Terraform, and CI/CD experience.
                Strong Linux background. Docker expert. No data science experience.
                Python scripting for automation only.
                """
            },
        ]
    },

    # ── Query 3: NLP Engineer ─────────────────────────────────────────────────
    {
        "query_id": 3,
        "job_description": """
        NLP Engineer with deep expertise in transformer models. BERT, GPT, T5
        fine-tuning experience required. Hugging Face ecosystem proficiency.
        Python and PyTorch required. Experience with named entity recognition,
        text classification, semantic search. Vector databases (Pinecone, Qdrant,
        Weaviate) experience preferred. Production NLP deployment experience.
        """,
        "candidates": [
            {
                "id": 301,
                "relevance": 3,
                "resume": """
                NLP Engineer with 4 years transformer model experience. Fine-tuned BERT,
                RoBERTa, T5 for multiple production tasks. Hugging Face contributor.
                Built semantic search system using Qdrant and sentence-transformers.
                Named entity recognition pipeline serving 1M requests daily. PyTorch expert.
                Deployed models using FastAPI and Docker on AWS.
                """
            },
            {
                "id": 302,
                "relevance": 2,
                "resume": """
                ML Engineer with NLP focus. Python, PyTorch, Hugging Face experience.
                Used BERT for text classification. Some fine-tuning experience.
                Built basic semantic search. No vector database production experience.
                Familiar with spaCy for NER tasks.
                """
            },
            {
                "id": 303,
                "relevance": 1,
                "resume": """
                Software Engineer with some NLP interest. Python developer.
                Used NLTK and basic regex for text processing. No transformer experience.
                Interested in learning NLP. Strong software engineering background.
                """
            },
            {
                "id": 304,
                "relevance": 0,
                "resume": """
                Android Developer with Java and Kotlin experience.
                Built mobile applications. Some Python basics. No NLP experience.
                """
            },
        ]
    },
]


def get_benchmark_queries():
    """Return all benchmark queries."""
    return BENCHMARK_DATA


def get_query_by_id(query_id: int):
    """Return a specific benchmark query."""
    for query in BENCHMARK_DATA:
        if query["query_id"] == query_id:
            return query
    return None