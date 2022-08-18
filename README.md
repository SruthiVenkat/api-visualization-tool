This is the VizAPI tool which uses a modified version of Python's [d3graph](https://github.com/erdogant/d3graph) library to generate a d3js visualization of library API usage by clients.

The tool takes a list of projects as input, which are either clients or libraries.
It expects a JSON file called `input.json` as input. It should be an array of objects with one of the following formats:
```
{
  "url": Github link to repo,
  "commit": Commit ID,
  "artifact": artifact ID of project,
  "type": "client" or "library"
}
```
or
```
{
  "artifact": artifact ID of project,
  "type": "client" or "library"
}
```
Our existing data can be found [here](https://zenodo.org/record/6951140). The directory `apis-data` needs to be copied to the root of this repository.

If URLs and commit IDs are not provided as input, it is assumed that the data for the project already exists in `apis-data`. If the data does not exist, then both "url" and "commit" needs to be provided for the project. If "url" and "commit" are provided, then the repository is cloned into `./projects`, our instrumentation tool is run for that project and the data is generated in `./repos/api-surface-data`. 

Note: If `input.json` contains only one object of type "library", then VizAPI searches for its clients in `apis-data` and generates the graph.

The final graph is generated with the name `api-usage.html`.

The command to run the tool and generate the graph without Docker is `python api-viz.py`. In this case, some Python libraries need to be installed and all paths starting with `/api-visualization-tool` need to be modified to point to this repo.

The following are the commands to run the tool using Docker:

1. ```sudo docker build -t img_name .``` from within this repo.

2. ```sudo docker run -v /path/to/this/repo/api-visualization-tool:/api-visualization-tool img_name```
