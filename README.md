# BenchmarkPCG

## Overview

Repository containing the Benchmark for Video Game Level Generators developed in the Bachelor Thesis **'Evolución de las técnicas de Generación Automática de Niveles en Videojuegos: De algoritmos tradicionales a modelos avanzados de Deep Learning'**.

This README provides some guidelines on how to build and run the benchmark software tool.

## Prerequisites

Make sure you have installed a conda distribution before building and running any project.

## General guidelines

In order to use the software tool, follow these build process:

1. Create a conda environment from the file `environment.yml` with the following command:

```bash
conda env create -f environment.yml
```

2. Activate the conda environment.

```bash
conda activate env_evaluation
```

3. Include the sets of levels to evaluate in the `levels` folder. In order to do that, you must create (inside the `levels` folder) a folder for each set of levels. An example of structure would be the following:

```bash
levels
  set_1
    level_1_1.txt
    level_1_2.txt
    ...
    level_1_n.txt
  set_2
    level_2_1.txt
    level_2_2.txt
    ...
    level_2_n.txt
  ...
  set_m
    level_m_1.txt
    level_m_2.txt
    ...
    level_m_n.txt
```

Apart from the levels' files, each folder created inside the `levels` folder must contain one (or, optionally, two) more file:

* `properties.json` (mandatory): This file must include a dictionary with the following fields:
  * "Generator Name" (mandatory) : Name of the generator (string).
  * "Game Name" (mandatory): Name of the game the set of levels correspond to.
  * "Ignore" (optional): Boolean field indicating if the corresponding set of levels must be ignored in the evaluation process.
  
The optional `times.csv` file must contain the data associated to the time each level of the set required to be generated. The file must have two columns; the first must register the name of each level file, the second must register the nanoseconds required to generate the level.

**Note**: You can use the current structure of the `levels` folder as a reference.

4. Execute the software tool in order to evaluate the levels included in the `levels` folder. For example, you can execute the following command:

```bash
python src/evaluate_levels.py --continue_evaluation --create_figures
```

**Note:**: The previous command have different optional arguments:
   * `--continue_evaluation` : When this argument is present, the program uses the _initial\_stats_ already computed to save resources.
   * `--create-figures` : When this argument is present, the program creates a table and a bar chart for each evaluation specified in the folder `evaluations`.
   * `--do_not_use_parallelization` : When this argument is present, it deactivates the program's multithreading capabilities. However, this is not recommended. The program is much more efficient when using parallelization.
   * `--max_workers <integer>` : When this argument is present, it sets the number of threads to use for multithreading parallelization. When it is not present, the program chooses a number of threads adapted to the capabilities of the computer.
