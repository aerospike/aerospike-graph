# How to use Generator

python ./generate-ags-csv.py --nodes 17000000 --median 20 --sigma 1.5 --workers 4  --out-dir ./output

python ./generate-ags-csv.py \
--nodes 17000000 \
--median 20.0 \
--sigma 1.0 \
--workers 224 \
--out_dirs /mnt/disk1,/mnt/disk2,/mnt/disk3 \
--seed 42 \
--dist lognormal \
--schema-file schema.csv \

# VM CMDs for loading

## Partition the 24x SSD Disks:
for i in {1..24}; do
dev="/dev/nvme0n$i"
dir="/mnt/data$i"
sudo mkfs.ext4 -F "$dev" && \
sudo mkdir -p "$dir" && \
sudo mount "$dev" "$dir" && \
sudo chown $USER:$USER "$dir"
done

## Get data size after run:
for i in {1..24}; do
du -sh /mnt/data$i
done

## Clean mounts before running
for i in {1..24}; do
echo "🧹 Cleaning /mnt/data$i..."
sudo rm -rf /mnt/data$i/edges /mnt/data$i/vertices
done
