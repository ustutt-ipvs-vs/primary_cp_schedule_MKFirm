# CP-based-TSN-scheduling

Constraint programming based scheduler for time-sensitive networks (TSN) using CPLEX.


When using this code, please cite:

**TODO add reference to our paper**
```

```

## Requirements
- Python (tested with 3.10)
- docplex (tested with 2.25.236)
- CPLEX (tested with 22.1)

## Usage

```
usage: main.py [-h] [-n NETWORK] [-s SCENARIO] [-t TIMELIMIT] [--threads THREADS] [-v] [--raw-output] [-o OUTPUT]
               [--cplex CPLEX]

options:
  -h, --help            show this help message and exit
  -n NETWORK, --network NETWORK
                        Path to the network graph file
  -s SCENARIO, --scenario SCENARIO
                        Path to the scenario file
  -t TIMELIMIT, --timelimit TIMELIMIT
                        solver time limit in seconds. Use negative values for unlimited.
  --threads THREADS     Number of threads to be used at most
  -v, --verbose         print a lot of debug outputs on the console. Can be overwritten by the raw flag.
  --raw-output          If set, the console output will be in a raw format. Overwrites the verbose flag.
  -o OUTPUT, --output OUTPUT
                        Filename and path to store the output in.
  --cplex CPLEX         Path to cplex executable. Provide if it is not in the path variable.
```

### Example

```
python main.py -n dummy_data/small_graph.json -s dummy_data/small_scenario.json -t 10
```

### Input Data

To get more input data, you can use the generation scripts in our adjacent repository ([here]()**TODO add link**).

Inputs files must adhere the format from the generation scripts. Example files are provided in the `dummy_data` folder.