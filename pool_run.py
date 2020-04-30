import argparse
import os
from multiprocessing import Pool
from progressbar import progressbar
import subprocess
import time


parser = argparse.ArgumentParser()
parser.add_argument('-d', type=int, help='Device to be used')
parser.add_argument('-N', type=int, help='Number of jobs', default=3)
parser.add_argument('--models', help='Model path', default='../ShapeNet/ShapeNetCore.v2')
parser.add_argument('--textures', help='Texture path', default='../Texture')
parser.add_argument('--output', help='Output path', default='../output/render')
parser.add_argument('--yaml', help='Path to a list of yaml files')
parser.add_argument('--start', type=int, help='Position to start running', default=0)
args = parser.parse_args()

start = time.time()

def work(func_arg):
    yaml = func_arg[0]
    i = func_arg[1]

    yaml_path = os.path.join(args.yaml, yaml)
    print('Starting working on ', yaml_path, '...')
    command = 'CUDA_DEVICE_ORDER=PCI_BUS_ID CUDA_VISIBLE_DEVICES=%d python run.py --fast %s %s %s %s' % (args.d, yaml_path, args.models, args.textures, args.output)
    this_subprocess = subprocess.Popen(command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    this_subprocess.wait()

    time_ela = time.time() - start
    time_ela = time.strftime("%H:%M:%S", time.gmtime(time_ela))

    print('Finished %s. %d/%d %s' % (yaml, i+1, len(yaml_files), time_ela))


yaml_files = os.listdir(args.yaml)
yaml_files = sorted([f for f in yaml_files if '.yaml' in f])

print('Starting from %d out of %d files.' % (args.start, len(yaml_files)))
yaml_files = yaml_files[args.start:]

func_args = [(y,i) for i, y in enumerate(yaml_files)]

pool = Pool(args.N)
chunksize = 1
for _ in progressbar(pool.map(work, func_args, chunksize), redirect_stdout=True):
    pass


print('All done.')