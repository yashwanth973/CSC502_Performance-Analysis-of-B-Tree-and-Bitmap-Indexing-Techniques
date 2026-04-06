import random
import time
import sys
from bisect import bisect_left, bisect_right
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple


# ============================================================
# DATASET GENERATION
# ============================================================

def generate_dataset(num_records: int = 50000, seed: int = 42) -> List[Dict[str, Any]]:
    random.seed(seed)
    dataset = []

    departments = ["CSE", "ECE", "MECH", "CIVIL", "EEE"]
    genders = ["M", "F"]

    for i in range(num_records):
        record = {
            "id": i,
            "age": random.randint(18, 65),               # medium cardinality
            "salary": random.randint(25000, 150000),     # high cardinality
            "gender": random.choice(genders),            # low cardinality
            "department": random.choice(departments),
        }
        dataset.append(record)

    return dataset


# ============================================================
# B-TREE IMPLEMENTATION
# ============================================================

class BTreeNode:
    def __init__(self, leaf: bool = False):
        self.leaf = leaf
        self.keys: List[Any] = []
        self.values: List[List[int]] = []
        self.children: List["BTreeNode"] = []


class BTree:
    def __init__(self, t: int = 16):
        if t < 2:
            raise ValueError("B-Tree minimum degree must be at least 2")
        self.t = t
        self.root = BTreeNode(leaf=True)

    def search(self, key: Any, node: Optional[BTreeNode] = None) -> List[int]:
        if node is None:
            node = self.root

        i = bisect_left(node.keys, key)

        if i < len(node.keys) and node.keys[i] == key:
            if node.leaf:
                return node.values[i]
            return self.search(key, node.children[i + 1])

        if node.leaf:
            return []

        return self.search(key, node.children[i])

    def range_search(self, low: Any, high: Any) -> List[int]:
        result: List[int] = []
        self._range_search_recursive(self.root, low, high, result)
        return result

    def _range_search_recursive(self, node: BTreeNode, low: Any, high: Any, result: List[int]) -> None:
        if node.leaf:
            start = bisect_left(node.keys, low)
            end = bisect_right(node.keys, high)
            for i in range(start, end):
                result.extend(node.values[i])
            return

        for i, key in enumerate(node.keys):
            if low < key:
                self._range_search_recursive(node.children[i], low, high, result)
            if key > high:
                return

        self._range_search_recursive(node.children[len(node.keys)], low, high, result)

    def insert(self, key: Any, row_id: int) -> None:
        root = self.root
        if len(root.keys) == (2 * self.t - 1):
            new_root = BTreeNode(leaf=False)
            new_root.children.append(root)
            self._split_child(new_root, 0)
            self.root = new_root
            self._insert_non_full(new_root, key, row_id)
        else:
            self._insert_non_full(root, key, row_id)

    def _split_child(self, parent: BTreeNode, index: int) -> None:
        t = self.t
        full_child = parent.children[index]
        new_child = BTreeNode(leaf=full_child.leaf)

        median_key = full_child.keys[t - 1]

        if full_child.leaf:
            new_child.keys = full_child.keys[t - 1:]
            new_child.values = full_child.values[t - 1:]
            full_child.keys = full_child.keys[:t - 1]
            full_child.values = full_child.values[:t - 1]

            parent.keys.insert(index, new_child.keys[0])
            parent.children.insert(index + 1, new_child)
        else:
            new_child.keys = full_child.keys[t:]
            full_child.keys = full_child.keys[:t - 1]

            new_child.children = full_child.children[t:]
            full_child.children = full_child.children[:t]

            parent.keys.insert(index, median_key)
            parent.children.insert(index + 1, new_child)

    def _insert_non_full(self, node: BTreeNode, key: Any, row_id: int) -> None:
        if node.leaf:
            i = bisect_left(node.keys, key)

            if i < len(node.keys) and node.keys[i] == key:
                node.values[i].append(row_id)
            else:
                node.keys.insert(i, key)
                node.values.insert(i, [row_id])
            return

        i = bisect_right(node.keys, key)
        child = node.children[i]

        if len(child.keys) == (2 * self.t - 1):
            self._split_child(node, i)
            if key >= node.keys[i]:
                i += 1

        self._insert_non_full(node.children[i], key, row_id)


# ============================================================
# BITMAP INDEX IMPLEMENTATION
# ============================================================

class BitmapIndex:
    def __init__(self):
        self.bitmaps: Dict[Any, int] = {}
        self.size = 0

    def build(self, dataset: List[Dict[str, Any]], field: str) -> None:
        self.size = len(dataset)
        self.bitmaps.clear()

        for row_id, row in enumerate(dataset):
            value = row[field]
            if value not in self.bitmaps:
                self.bitmaps[value] = 0
            self.bitmaps[value] |= (1 << row_id)

    def search(self, value: Any) -> List[int]:
        bitset = self.bitmaps.get(value, 0)
        return self._bitset_to_row_ids(bitset)

    def search_bitset(self, value: Any) -> int:
        return self.bitmaps.get(value, 0)

    def range_search(self, low: Any, high: Any) -> List[int]:
        combined = 0
        for value, bitset in self.bitmaps.items():
            if low <= value <= high:
                combined |= bitset
        return self._bitset_to_row_ids(combined)

    def range_search_bitset(self, low: Any, high: Any) -> int:
        combined = 0
        for value, bitset in self.bitmaps.items():
            if low <= value <= high:
                combined |= bitset
        return combined

    @staticmethod
    def _bitset_to_row_ids(bitset: int) -> List[int]:
        row_ids = []
        while bitset:
            lsb = bitset & -bitset
            row_id = lsb.bit_length() - 1
            row_ids.append(row_id)
            bitset ^= lsb
        return row_ids


# ============================================================
# LINEAR SCAN
# ============================================================

def linear_search(dataset: List[Dict[str, Any]], field: str, value: Any) -> List[int]:
    return [row["id"] for row in dataset if row[field] == value]


def linear_range_search(dataset: List[Dict[str, Any]], field: str, low: Any, high: Any) -> List[int]:
    return [row["id"] for row in dataset if low <= row[field] <= high]


def linear_multi_condition(dataset: List[Dict[str, Any]], age_value: int, gender_value: str) -> List[int]:
    return [row["id"] for row in dataset if row["age"] == age_value and row["gender"] == gender_value]


# ============================================================
# STORAGE ESTIMATION
# ============================================================

def estimate_btree_size(node: BTreeNode) -> int:
    size = sys.getsizeof(node)
    size += sys.getsizeof(node.keys)
    size += sys.getsizeof(node.values)
    size += sys.getsizeof(node.children)

    for key in node.keys:
        size += sys.getsizeof(key)

    for value_list in node.values:
        size += sys.getsizeof(value_list)
        for item in value_list:
            size += sys.getsizeof(item)

    for child in node.children:
        size += estimate_btree_size(child)

    return size


def estimate_bitmap_size(bitmap_index: BitmapIndex) -> int:
    size = sys.getsizeof(bitmap_index)
    size += sys.getsizeof(bitmap_index.bitmaps)
    for key, value in bitmap_index.bitmaps.items():
        size += sys.getsizeof(key)
        size += sys.getsizeof(value)
    return size


# ============================================================
# TIMING
# ============================================================

def measure_time(func, *args, repeats: int = 5, **kwargs) -> Tuple[float, Any]:
    total = 0.0
    output = None

    for _ in range(repeats):
        start = time.perf_counter()
        output = func(*args, **kwargs)
        end = time.perf_counter()
        total += (end - start)

    return (total / repeats) * 1000, output


# ============================================================
# BUILD INDEX HELPERS
# ============================================================

def build_btree_for_field(dataset: List[Dict[str, Any]], field: str, degree: int = 16) -> Tuple[BTree, float]:
    btree = BTree(t=degree)
    start = time.perf_counter()
    for row in dataset:
        btree.insert(row[field], row["id"])
    build_ms = (time.perf_counter() - start) * 1000
    return btree, build_ms


def build_bitmap_for_field(dataset: List[Dict[str, Any]], field: str) -> Tuple[BitmapIndex, float]:
    bitmap = BitmapIndex()
    start = time.perf_counter()
    bitmap.build(dataset, field)
    build_ms = (time.perf_counter() - start) * 1000
    return bitmap, build_ms


# ============================================================
# BENCHMARKS
# ============================================================

@dataclass
class QueryResult:
    label: str
    btree_ms: float
    bitmap_ms: float
    linear_ms: float
    matches: int


def benchmark_field_queries(
    dataset: List[Dict[str, Any]],
    field: str,
    equality_value: Any,
    range_low: Optional[Any] = None,
    range_high: Optional[Any] = None
) -> Tuple[List[QueryResult], BTree, BitmapIndex, float, float]:
    btree, btree_build_ms = build_btree_for_field(dataset, field)
    bitmap, bitmap_build_ms = build_bitmap_for_field(dataset, field)

    results: List[QueryResult] = []

    # Equality query
    btree_eq_ms, btree_eq_out = measure_time(btree.search, equality_value)
    bitmap_eq_ms, bitmap_eq_out = measure_time(bitmap.search, equality_value)
    linear_eq_ms, linear_eq_out = measure_time(linear_search, dataset, field, equality_value)

    if sorted(btree_eq_out) != sorted(bitmap_eq_out) or sorted(bitmap_eq_out) != sorted(linear_eq_out):
        raise ValueError(f"Equality query mismatch for field {field}")

    results.append(
        QueryResult(
            label=f"{field} = {equality_value}",
            btree_ms=btree_eq_ms,
            bitmap_ms=bitmap_eq_ms,
            linear_ms=linear_eq_ms,
            matches=len(btree_eq_out),
        )
    )

    # Range query only for numeric fields
    if range_low is not None and range_high is not None:
        btree_range_ms, btree_range_out = measure_time(btree.range_search, range_low, range_high)
        bitmap_range_ms, bitmap_range_out = measure_time(bitmap.range_search, range_low, range_high)
        linear_range_ms, linear_range_out = measure_time(linear_range_search, dataset, field, range_low, range_high)

        if sorted(btree_range_out) != sorted(bitmap_range_out) or sorted(bitmap_range_out) != sorted(linear_range_out):
            raise ValueError(f"Range query mismatch for field {field}")

        results.append(
            QueryResult(
                label=f"{range_low} <= {field} <= {range_high}",
                btree_ms=btree_range_ms,
                bitmap_ms=bitmap_range_ms,
                linear_ms=linear_range_ms,
                matches=len(btree_range_out),
            )
        )

    return results, btree, bitmap, btree_build_ms, bitmap_build_ms


def bitmap_multi_condition(age_bitmap: BitmapIndex, gender_bitmap: BitmapIndex, age_value: int, gender_value: str) -> List[int]:
    combined = age_bitmap.search_bitset(age_value) & gender_bitmap.search_bitset(gender_value)
    return BitmapIndex._bitset_to_row_ids(combined)


def btree_multi_condition(dataset: List[Dict[str, Any]], age_btree: BTree, age_value: int, gender_value: str) -> List[int]:
    candidate_ids = age_btree.search(age_value)
    return [row_id for row_id in candidate_ids if dataset[row_id]["gender"] == gender_value]


def benchmark_multi_condition(
    dataset: List[Dict[str, Any]],
    age_btree: BTree,
    age_bitmap: BitmapIndex,
    gender_bitmap: BitmapIndex,
    age_value: int,
    gender_value: str
) -> QueryResult:
    btree_ms, btree_out = measure_time(btree_multi_condition, dataset, age_btree, age_value, gender_value)
    bitmap_ms, bitmap_out = measure_time(bitmap_multi_condition, age_bitmap, gender_bitmap, age_value, gender_value)
    linear_ms, linear_out = measure_time(linear_multi_condition, dataset, age_value, gender_value)

    if sorted(btree_out) != sorted(bitmap_out) or sorted(bitmap_out) != sorted(linear_out):
        raise ValueError("Multi-condition query mismatch")

    return QueryResult(
        label=f"age = {age_value} AND gender = {gender_value}",
        btree_ms=btree_ms,
        bitmap_ms=bitmap_ms,
        linear_ms=linear_ms,
        matches=len(btree_out),
    )


# ============================================================
# REPORTING
# ============================================================

def print_dataset_summary(dataset: List[Dict[str, Any]]) -> None:
    ages = [row["age"] for row in dataset]
    salaries = [row["salary"] for row in dataset]
    genders = [row["gender"] for row in dataset]

    print("\n" + "=" * 70)
    print("DATASET SUMMARY")
    print("=" * 70)
    print(f"Total records       : {len(dataset)}")
    print(f"Age range           : {min(ages)} to {max(ages)}")
    print(f"Unique ages         : {len(set(ages))}")
    print(f"Unique salary values: {len(set(salaries))}")
    print(f"Unique genders      : {len(set(genders))}")
    print("\nSample records:")
    for row in dataset[:5]:
        print(row)


def print_query_results(title: str, results: List[QueryResult]) -> None:
    print("\n" + "=" * 100)
    print(title)
    print("=" * 100)
    print(f"{'Query':<35}{'B-Tree (ms)':<15}{'Bitmap (ms)':<15}{'Linear (ms)':<15}{'Matches':<10}")
    print("-" * 100)

    for r in results:
        print(f"{r.label:<35}{r.btree_ms:<15.3f}{r.bitmap_ms:<15.3f}{r.linear_ms:<15.3f}{r.matches:<10}")


def print_build_and_storage_stats(
    age_btree_build: float, age_bitmap_build: float,
    gender_btree_build: float, gender_bitmap_build: float,
    salary_btree_build: float, salary_bitmap_build: float,
    age_btree_size: int, age_bitmap_size: int,
    gender_btree_size: int, gender_bitmap_size: int,
    salary_btree_size: int, salary_bitmap_size: int
) -> None:
    print("\n" + "=" * 100)
    print("BUILD TIME AND STORAGE COMPARISON")
    print("=" * 100)
    print(f"{'Field':<12}{'Index':<12}{'Build Time (ms)':<18}{'Estimated Size (bytes)':<25}")
    print("-" * 100)

    rows = [
        ("Age", "B-Tree", age_btree_build, age_btree_size),
        ("Age", "Bitmap", age_bitmap_build, age_bitmap_size),
        ("Gender", "B-Tree", gender_btree_build, gender_btree_size),
        ("Gender", "Bitmap", gender_bitmap_build, gender_bitmap_size),
        ("Salary", "B-Tree", salary_btree_build, salary_btree_size),
        ("Salary", "Bitmap", salary_bitmap_build, salary_bitmap_size),
    ]

    for field, index_name, build_ms, storage in rows:
        print(f"{field:<12}{index_name:<12}{build_ms:<18.3f}{storage:<25}")


# ============================================================
# PLOTTING
# ============================================================

def save_or_show():
    import matplotlib.pyplot as plt
    plt.tight_layout()
    plt.show(block=False)


def plot_build_time_by_field(age_btree_build, age_bitmap_build, gender_btree_build, gender_bitmap_build, salary_btree_build, salary_bitmap_build):
    import matplotlib.pyplot as plt

    fields = ["Age", "Gender", "Salary"]
    btree_vals = [age_btree_build, gender_btree_build, salary_btree_build]
    bitmap_vals = [age_bitmap_build, gender_bitmap_build, salary_bitmap_build]

    x = range(len(fields))
    width = 0.35

    plt.figure(figsize=(8, 5))
    plt.bar([i - width / 2 for i in x], btree_vals, width=width, label="B-Tree")
    plt.bar([i + width / 2 for i in x], bitmap_vals, width=width, label="Bitmap")
    plt.xticks(list(x), fields)
    plt.ylabel("Build Time (ms)")
    plt.title("Build Time by Field")
    plt.legend()
    plt.savefig("graph1_build_time_by_field.png")
    save_or_show()


def plot_storage_by_field(age_btree_size, age_bitmap_size, gender_btree_size, gender_bitmap_size, salary_btree_size, salary_bitmap_size):
    import matplotlib.pyplot as plt

    fields = ["Age", "Gender", "Salary"]
    btree_vals = [age_btree_size, gender_btree_size, salary_btree_size]
    bitmap_vals = [age_bitmap_size, gender_bitmap_size, salary_bitmap_size]

    x = range(len(fields))
    width = 0.35

    plt.figure(figsize=(8, 5))
    plt.bar([i - width / 2 for i in x], btree_vals, width=width, label="B-Tree")
    plt.bar([i + width / 2 for i in x], bitmap_vals, width=width, label="Bitmap")
    plt.xticks(list(x), fields)
    plt.ylabel("Estimated Size (bytes)")
    plt.title("Storage Usage by Field")
    plt.legend()
    plt.savefig("graph2_storage_by_field.png")
    save_or_show()


def plot_age_queries(age_results: List[QueryResult]):
    import matplotlib.pyplot as plt

    labels = [r.label for r in age_results]
    btree_vals = [r.btree_ms for r in age_results]
    bitmap_vals = [r.bitmap_ms for r in age_results]
    linear_vals = [r.linear_ms for r in age_results]

    x = range(len(labels))
    width = 0.25

    plt.figure(figsize=(10, 5))
    plt.bar([i - width for i in x], btree_vals, width=width, label="B-Tree")
    plt.bar(list(x), bitmap_vals, width=width, label="Bitmap")
    plt.bar([i + width for i in x], linear_vals, width=width, label="Linear Scan")
    plt.xticks(list(x), labels, rotation=15)
    plt.ylabel("Query Time (ms)")
    plt.title("Age Query Performance")
    plt.legend()
    plt.savefig("graph3_age_queries.png")
    save_or_show()


def plot_gender_vs_salary_equality(gender_results: List[QueryResult], salary_results: List[QueryResult]):
    import matplotlib.pyplot as plt

    labels = [gender_results[0].label, salary_results[0].label]
    btree_vals = [gender_results[0].btree_ms, salary_results[0].btree_ms]
    bitmap_vals = [gender_results[0].bitmap_ms, salary_results[0].bitmap_ms]
    linear_vals = [gender_results[0].linear_ms, salary_results[0].linear_ms]

    x = range(len(labels))
    width = 0.25

    plt.figure(figsize=(10, 5))
    plt.bar([i - width for i in x], btree_vals, width=width, label="B-Tree")
    plt.bar(list(x), bitmap_vals, width=width, label="Bitmap")
    plt.bar([i + width for i in x], linear_vals, width=width, label="Linear Scan")
    plt.xticks(list(x), labels, rotation=10)
    plt.ylabel("Query Time (ms)")
    plt.title("Gender vs Salary Equality Query Comparison")
    plt.legend()
    plt.savefig("graph4_gender_vs_salary.png")
    save_or_show()


def plot_multi_condition(result: QueryResult):
    import matplotlib.pyplot as plt

    labels = ["B-Tree", "Bitmap", "Linear Scan"]
    values = [result.btree_ms, result.bitmap_ms, result.linear_ms]

    plt.figure(figsize=(8, 5))
    plt.bar(labels, values)
    plt.ylabel("Query Time (ms)")
    plt.title(f"Multi-Condition Query: {result.label}")
    plt.savefig("graph5_multi_condition.png")
    save_or_show()


def benchmark_different_dataset_sizes():
    import matplotlib.pyplot as plt

    dataset_sizes = [1000, 5000, 10000, 50000]
    age_btree_times = []
    age_bitmap_times = []

    for size in dataset_sizes:
        dataset = generate_dataset(num_records=size, seed=42)

        _, btree_build_ms = build_btree_for_field(dataset, "age")
        _, bitmap_build_ms = build_bitmap_for_field(dataset, "age")

        age_btree_times.append(btree_build_ms)
        age_bitmap_times.append(bitmap_build_ms)

    plt.figure(figsize=(8, 5))
    plt.plot(dataset_sizes, age_btree_times, marker="o", label="B-Tree (Age)")
    plt.plot(dataset_sizes, age_bitmap_times, marker="o", label="Bitmap (Age)")
    plt.xlabel("Dataset Size")
    plt.ylabel("Build Time (ms)")
    plt.title("Build Time vs Dataset Size")
    plt.legend()
    plt.savefig("graph6_dataset_size.png")
    save_or_show()


# ============================================================
# MAIN
# ============================================================

def main():
    dataset = generate_dataset(num_records=50000, seed=42)
    print_dataset_summary(dataset)

    # Age benchmarks
    age_results, age_btree, age_bitmap, age_btree_build, age_bitmap_build = benchmark_field_queries(
        dataset=dataset,
        field="age",
        equality_value=25,
        range_low=20,
        range_high=30,
    )

    # Gender benchmarks
    gender_results, gender_btree, gender_bitmap, gender_btree_build, gender_bitmap_build = benchmark_field_queries(
        dataset=dataset,
        field="gender",
        equality_value="M",
    )

    # Salary benchmarks
    salary_results, salary_btree, salary_bitmap, salary_btree_build, salary_bitmap_build = benchmark_field_queries(
        dataset=dataset,
        field="salary",
        equality_value=50000,
        range_low=40000,
        range_high=80000,
    )

    # Multi-condition benchmark
    multi_result = benchmark_multi_condition(
        dataset=dataset,
        age_btree=age_btree,
        age_bitmap=age_bitmap,
        gender_bitmap=gender_bitmap,
        age_value=25,
        gender_value="M",
    )

    # Storage
    age_btree_size = estimate_btree_size(age_btree.root)
    age_bitmap_size = estimate_bitmap_size(age_bitmap)

    gender_btree_size = estimate_btree_size(gender_btree.root)
    gender_bitmap_size = estimate_bitmap_size(gender_bitmap)

    salary_btree_size = estimate_btree_size(salary_btree.root)
    salary_bitmap_size = estimate_bitmap_size(salary_bitmap)

    # Print results
    print_build_and_storage_stats(
        age_btree_build, age_bitmap_build,
        gender_btree_build, gender_bitmap_build,
        salary_btree_build, salary_bitmap_build,
        age_btree_size, age_bitmap_size,
        gender_btree_size, gender_bitmap_size,
        salary_btree_size, salary_bitmap_size
    )

    print_query_results("AGE QUERY RESULTS", age_results)
    print_query_results("GENDER QUERY RESULTS", gender_results)
    print_query_results("SALARY QUERY RESULTS", salary_results)
    print_query_results("MULTI-CONDITION QUERY RESULT", [multi_result])

    # Graphs
    plot_build_time_by_field(
        age_btree_build, age_bitmap_build,
        gender_btree_build, gender_bitmap_build,
        salary_btree_build, salary_bitmap_build
    )

    plot_storage_by_field(
        age_btree_size, age_bitmap_size,
        gender_btree_size, gender_bitmap_size,
        salary_btree_size, salary_bitmap_size
    )

    plot_age_queries(age_results)
    plot_gender_vs_salary_equality(gender_results, salary_results)
    plot_multi_condition(multi_result)
    benchmark_different_dataset_sizes()

    # Keep graphs open
    try:
        import matplotlib.pyplot as plt
        print("\nGenerated graph files:")
        print("- graph1_build_time_by_field.png")
        print("- graph2_storage_by_field.png")
        print("- graph3_age_queries.png")
        print("- graph4_gender_vs_salary.png")
        print("- graph5_multi_condition.png")
        print("- graph6_dataset_size.png")
        plt.show()
    except ImportError:
        pass


if __name__ == "__main__":
    main()