import subprocess
from tqdm import tqdm
import argparse
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from time import time

def upload_file(path: Path, gcs_path: str):
    subprocess.run(["gsutil", "-q", "cp", str(path), gcs_path], check=True)

def upload_worker(file: Path, gcs_base: str):
    # Put vertices and edges in separate subdirectories
    subdir = "vertices" if "vertices" in str(file) else "edges"
    upload_file(file, f"{gcs_base}/{subdir}/{file.name}")
    print(f"✔ Uploaded: {subdir}/{file.name}")

def get_files_from_disk(disk_num: int, file_type: str) -> list:
    """Get all CSV files of specified type from a disk."""
    data_dir = Path(f"/mnt/data{disk_num}/{file_type}")
    if data_dir.exists():
        if file_type == "vertices":
            return list(data_dir.glob("vertices_*_*.csv"))
        else:
            return list(data_dir.glob("edges_*_part_*_*.csv"))
    return []

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--gcs", required=True, help="gs://bucket/path/")
    parser.add_argument("--threads", type=int, default=8, help="Parallel upload threads")
    parser.add_argument("--disks", type=int, default=24)
    args = parser.parse_args()

    start = time()
    
    # Collect both vertex and edge files
    vertex_files = []
    edge_files = []

    for i in range(1, args.disks + 1):
        vertex_files.extend(get_files_from_disk(i, "vertices"))
        edge_files.extend(get_files_from_disk(i, "edges"))

    total_files = len(vertex_files) + len(edge_files)
    print(f"\n📦 Found across {args.disks} disks:")
    print(f"   • {len(vertex_files)} vertex files")
    print(f"   • {len(edge_files)} edge files")
    print(f"   • {total_files} total files")

    # Upload all files
    with ThreadPoolExecutor(max_workers=args.threads) as executor:
        futures = {
            executor.submit(upload_worker, f, args.gcs): f
            for f in vertex_files + edge_files
        }
        for _ in tqdm(as_completed(futures), total=len(futures), desc="Uploading"):
            pass

    print(f"\n✅ Completed upload in {(time() - start):.2f} seconds")

if __name__ == "__main__":
    main()