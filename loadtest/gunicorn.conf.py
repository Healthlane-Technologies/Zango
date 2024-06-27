import multiprocessing
import gc

bind = "0.0.0.0:8000"
workers = multiprocessing.cpu_count() * 2 + 1
