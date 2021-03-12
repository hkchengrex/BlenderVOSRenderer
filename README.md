# Blender VOS Renderer

This is a fork of [BlenderProc](https://github.com/DLR-RM/BlenderProc).
It is used to generate the BL30K dataset.

## BL30K

BL30K is a synthetic dataset rendered using ShapeNet data and Blender. We break the dataset into six segments, each with approximately 5K videos. We noted that using probably half of the data is sufficient to reach full performance (although we still used all), and using one-sixth (5K) is insufficient.

Download here: [One Drive](https://hkustconnect-my.sharepoint.com/:f:/g/personal/hkchengad_connect_ust_hk/EhQLhKWJcVVGgTSWIpwYaGgBTbG7fDeHh8hgLsBTKBGvBA?e=eU9R5l)

Examples (not cherry-picked):
| Image | Annotation |
| :---: | :---: |
| ![image1](demo/00000.jpg) | ![image2](demo/00000.png) |
| ![image1](demo/00001.jpg) | ![image2](demo/00001.png) |
| ![image1](demo/00002jpg) | ![image2](demo/00002.png) |
| ![image1](demo/00003.jpg) | ![image2](demo/00003.png) |

## Generation

1. First download all required data and generate a list of yaml files. [Instructions here](https://github.com/hkchengrex/MiVOS/#generation).
2. Run the following command:

```bash
python pool_run.py --models <path_to/ShapeNetCore.v2> --textures <path_to/Texture> --yaml <path_to/yaml> --output <output directory> -d <GPU ID> -N <Number of parallel processes>
```

## Citation

Please cite our paper (and the original BlenderProc) if you find this repo/data useful!

```bibtex
@inproceedings{MiVOS_2021,
  title={Modular Interactive Video Object Segmentation: Interaction-to-Mask, Propagation and Difference-Aware Fusion},
  author={Cheng, Ho Kei and Tai, Yu-Wing and Tang, Chi-Keung},
  booktitle={CVPR},
  year={2021}
}
```
