import time


def get_key_index(key_name):
    mapping = {
        "ID": 0,
        "Title": 1,
        "Company": 2,
        "Location": 3,
        "Salary": 4,
        "Experience": 5,
        "Skills": 6,
        "Job Type": 7,
        "Posted Date": 8
    }
    return mapping.get(key_name, 4)


# ---------------- QUICK SORT ----------------

def quick_sort(arr, key_index):
    if len(arr) <= 1:
        return arr

    pivot = arr[len(arr)//2][key_index]
    left = [x for x in arr if x[key_index] < pivot]
    middle = [x for x in arr if x[key_index] == pivot]
    right = [x for x in arr if x[key_index] > pivot]

    return quick_sort(left, key_index) + middle + quick_sort(right, key_index)


# ---------------- MERGE SORT ----------------

def merge_sort(arr, key_index):
    if len(arr) <= 1:
        return arr

    mid = len(arr) // 2
    left = merge_sort(arr[:mid], key_index)
    right = merge_sort(arr[mid:], key_index)

    return merge(left, right, key_index)


def merge(left, right, key_index):
    result = []
    i = j = 0

    while i < len(left) and j < len(right):
        if left[i][key_index] < right[j][key_index]:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1

    result.extend(left[i:])
    result.extend(right[j:])
    return result


# ---------------- BUBBLE SORT ----------------

def bubble_sort(arr, key_index):
    arr = arr.copy()
    n = len(arr)

    for i in range(n):
        for j in range(0, n - i - 1):
            if arr[j][key_index] > arr[j + 1][key_index]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]

    return arr


# ---------------- TIM SORT (Built-in) ----------------

def tim_sort(arr, key_index):
    return sorted(arr, key=lambda x: x[key_index])


# ---------------- MASTER FUNCTION ----------------

def sort_jobs(job_list, key_name, algorithm_name):
    key_index = get_key_index(key_name)
    start = time.perf_counter()

    if algorithm_name == "Quick Sort":
        sorted_list = quick_sort(job_list, key_index)
    elif algorithm_name == "Merge Sort":
        sorted_list = merge_sort(job_list, key_index)
    elif algorithm_name == "Bubble Sort":
        sorted_list = bubble_sort(job_list, key_index)
    elif algorithm_name == "Tim Sort":
        sorted_list = tim_sort(job_list, key_index)
    else:
        sorted_list = job_list

    end = time.perf_counter()
    execution_time = end - start

    return sorted_list, execution_time