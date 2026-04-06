# CSC502_Performance-Analysis-of-B-Tree-and-Bitmap-Indexing-Techniques
This project compares two database indexing strategies—B-Tree indexing and Bitmap indexing—using Python implementations and a synthetic dataset. The goal is to evaluate how both techniques behave under different data cardinalities and query workloads, with a focus on build time, query performance, storage usage, and scalability. The project report states that the study uses 50,000 synthetic records and compares age, salary, and gender attributes to represent medium-, high-, and low-cardinality data respectively. fileciteturn1file0
Project Overview
The project investigates how indexing improves query efficiency compared with a linear scan baseline. According to the report, B-Tree indexing is intended to support fast equality and range lookups, while Bitmap indexing is aimed at analytical filtering workloads, especially for low-cardinality attributes. The experiments evaluate equality queries, range queries, and a multi-condition query. fileciteturn1file6
Files
`btree_bitmap_project_advanced.py` — main Python implementation containing dataset generation, B-Tree index, Bitmap index, query benchmarking, storage estimation, and graph generation. fileciteturn1file1
`CSC502_Project_Report.pdf` — project report describing the methodology, experiments, results, conclusions, and references. fileciteturn1file0
Features
Synthetic dataset generation with configurable record count and random seed. The dataset includes `id`, `age`, `salary`, `gender`, and `department`. fileciteturn1file1
B-Tree implementation with insertion, equality search, and range search support. fileciteturn1file1
Bitmap index implementation using bit vectors for equality and range filtering. fileciteturn1file9
Linear scan baseline for correctness and performance comparison. fileciteturn1file9
Benchmarks for:
equality queries
range queries
multi-condition queries
index build time
estimated storage usage
dataset-size scalability. fileciteturn1file6turn1file8
Automatic graph generation for benchmark results. The script saves six image files when run. fileciteturn1file4
Dataset
The report describes a synthetic dataset with the following default properties:
Total records: 50,000
Unique age values: 48
Unique salary values: 41,167
Unique gender values: 2 fileciteturn1file6
These attributes were chosen to represent different cardinality levels:
`age` → medium cardinality
`salary` → high cardinality
`gender` → low cardinality. fileciteturn1file0
Queries Evaluated
The experiments include the following queries:
`age = 25`
`20 <= age <= 30`
`gender = M`
salary equality and range queries
`age = 25 AND gender = M` fileciteturn1file6
In the Python script, the default salary test values are:
equality query: `salary = 50000`
range query: `40000 <= salary <= 80000` fileciteturn1file4turn1file8
Requirements
Python 3.x
`matplotlib` for graph generation. The script imports `matplotlib.pyplot` inside the plotting functions and in the final graph display block. fileciteturn1file4turn1file8
Install the dependency with:
```bash
pip install matplotlib
```
How to Run
Run the main script from the project directory:
```bash
python btree_bitmap_project_advanced.py
```
The script executes the full benchmark pipeline by:
generating a dataset with 50,000 records,
building B-Tree and Bitmap indexes for age, gender, and salary,
running benchmark queries,
estimating storage usage,
printing result tables, and
generating benchmark graphs. fileciteturn1file4turn1file8
Output
When executed, the script prints:
dataset summary
build time and storage comparison
age query results
gender query results
salary query results
multi-condition query result. fileciteturn1file4
It also generates the following graph files:
`graph1_build_time_by_field.png`
`graph2_storage_by_field.png`
`graph3_age_queries.png`
`graph4_gender_vs_salary.png`
`graph5_multi_condition.png`
`graph6_dataset_size.png` fileciteturn1file4
Main Findings
The report concludes that:
B-Tree indexing delivered consistently strong performance across the tested query types and showed better overall scalability. fileciteturn1file5turn1file7
Bitmap indexing was most effective for low-cardinality data, but became expensive in build time and storage for high-cardinality fields such as salary. fileciteturn1file2turn1file5
B-Tree indexing performed especially well for ordered and range-based queries because keys are stored in sorted order. fileciteturn1file7
The project recommends choosing an index structure based on both data distribution and expected workload. fileciteturn1file5
Limitations
The report notes several limitations:
the dataset is synthetic rather than real-world,
the Bitmap implementation is uncompressed,
only a limited number of attributes and query types were evaluated. fileciteturn1file5
Real-World Relevance
According to the report:
B-Tree indexes are commonly suited for OLTP-style systems requiring fast lookups and range queries,
Bitmap indexes are more suitable for OLAP-style workloads involving categorical filtering. fileciteturn1file5
Reference Basis
The project report states that the B-Tree portion of the study was inspired by Goetz Graefe’s paper Modern B-Tree Techniques, alongside course materials for Bitmap indexing concepts. fileciteturn1file0turn1file5
