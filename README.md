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

An example input is present in `input.json`. Another example is as follows:
```
{
		"artifact": "fastjson",
		"type": "library"
}
```


Our existing data can be found [here](https://zenodo.org/record/7023872). The directory `apis-data` needs to be copied to the root of this repository. The size of the data is around 2.6 GB.

If URLs and commit IDs are not provided as input, it is assumed that the data for the project already exists in `apis-data`. If the data does not exist, then both "url" and "commit" needs to be provided for the project. If "url" and "commit" are provided, then the repository is cloned into `./projects`, our instrumentation tool is run for that project and the data is generated in `./repos/api-surface-data`. 

Note: If `input.json` contains only one object of type "library", then VizAPI searches for its clients in `apis-data` and generates the graph.

The final graph is generated with the name `api-usage.html`.

The command to run the tool and generate the graph without Docker is `python api-viz.py`. In this case, some Python libraries (pandas, jupyterlab_server, networkx, colourmap, python-louvain, sklearn, ismember, d3graph, PyGithub)  need to be installed. All paths starting with `/api-visualization-tool` need to be modified to point to this repo, in the files `api-viz.py` and `config/config.properties`.

The following are the commands to run the tool using Docker:

1. ```docker build -t img_name .``` from within this repo.

2. ```docker run -v /path/to/this/repo/api-visualization-tool:/api-visualization-tool img_name``` The path before the `:` in the command is your local path to the repo. The path after the `:` in the command is the path in the container, which is `/api-visualization-tool`.

The size of the Docker image is around 4.1 GB.

The following are the input.json contents needed to reproduce the graphs [here](https://sruthivenkat.github.io/VizAPI-graph/).
1. Graph 1 
```
[{
		"artifact": "dataprocessor",
		"type": "client"
}]
```
2. Graph 2 (This graph looks a little different since we pushed some code to not display irrelevant nodes)
```
[
	{
			"artifact": "jsoup",
			"type": "library"
	},
	{
			"artifact": "ez-vcard",
			"type": "client"
	},
	{
			"artifact": "JsoupXpath",
			"type": "client"
	}
]
```
