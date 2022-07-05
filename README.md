This is the VizAPI tool which uses a modified version of Python's [d3graph](https://github.com/erdogant/d3graph) library to generate a d3js visualization of library API usage by clients.

The tool takes a list of projects as input, which are either clients or libraries.
It expects a JSON file called `input.json` as input. It should be an array of objects with one of the following formats:
```
{
  "url": Github link to repo,
  "commit": Commit ID,
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

If URLs and commit IDs are provided as input, then these repositories are cloned into `./repos`. The data is generated in `./repos/api-surface-data` and the graph is generated.

If the artifact is provided as input, then the data is expected to be in `./repos/api-surface-data` and the graph is generated. Any existing data (expected to be formatted) can be placed in `./repos/api-surface-data`.

The command to run the tool and generate the graph is `python api-viz.py`.
