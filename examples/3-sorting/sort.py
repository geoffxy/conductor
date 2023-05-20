import argparse
import os
import random
import sys
import time

import conductor.lib as cond


def insertion_sort(arr):
    i = 1
    while i < len(arr):
        j = i
        while j > 0 and arr[j - 1] > arr[j]:
            arr[j - 1], arr[j] = arr[j], arr[j - 1]
            j -= 1
        i += 1


def merge_sort(arr):
    scratch = arr.copy()

    def merge_sort_helper(start, end):
        if start + 1 == end:
            # Trivially sorted.
            return
        mid = (end - start) // 2 + start
        merge_sort_helper(start, mid)
        merge_sort_helper(mid, end)

        o = 0
        i = start
        j = mid

        while i < mid and j < end:
            if arr[i] <= arr[j]:
                scratch[o] = arr[i]
                i += 1
            else:
                scratch[o] = arr[j]
                j += 1
            o += 1

        while i < mid:
            scratch[o] = arr[i]
            i += 1
            o += 1

        while j < end:
            scratch[o] = arr[j]
            j += 1
            o += 1

        i = start
        j = 0
        while i < end:
            arr[i] = scratch[j]
            i += 1
            j += 1

    merge_sort_helper(0, len(arr))


def check_sorted(arr):
    if len(arr) == 0:
        return True
    last = arr[0]
    for x in arr:
        if x < last:
            return False
        last = x
    return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--method", type=str, required=True)
    parser.add_argument("--size", type=int, required=True)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    print("Running {} on {} elements.".format(args.method, args.size), file=sys.stderr)

    data = list(range(args.size))
    random.seed(args.seed)
    random.shuffle(data)

    start, end = 0, 0

    if args.method == "isort":
        start = time.time()
        insertion_sort(data)
        end = time.time()
    elif args.method == "msort":
        start = time.time()
        merge_sort(data)
        end = time.time()

    elapsed = end - start

    if "COND_OUT" in os.environ:
        out = open(cond.get_output_path() / "results.csv", "w")
    else:
        out = sys.stdout

    print("method,size,run_time_ms", file=out)
    print("{},{},{:.4f}".format(args.method, args.size, elapsed * 1000), file=out)

    assert check_sorted(data)


if __name__ == "__main__":
    main()
