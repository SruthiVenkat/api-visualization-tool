function d3graphscript(config = {
  // Default values
  width: 1000,
  height: 800,
  charge: -250,
  distance: 0,
  directed: false,
  collision: 0.5
}) {
  console.log('d3graphscript config = ', config);

  //Constants for the SVG
  var width = config.width;
  var height = config.height;

  //Set up the colour scale and shape
  var color = d3.scale.category20();
  var symbol = d3.svg.symbol();
 
  var force = d3.layout.force()
    .charge(config.charge)
    .linkDistance((d) => config.distance > 0 ? config.distance : d.edge_weight)
    .size([width, height]);


  //Append a SVG to the body of the html page. Assign this SVG as an object to svg
 d3.select("body")
    .append("div")
    .style("left", (width/2)-4*graph.graphLbl.length+"px") 
        .style("position", 'absolute')            
        .style("top", '40px')
        .style("text-anchor", "middle")  
        .style("font-size", "18px") 
        .text(graph.graphLbl);
  var legend = d3.select("body").append("div").attr("class", "rcorner1")
  var legendLines = legend.append("div")
  legendLines.append('span').html('<svg width="70%" height="2"><rect rx="20" ry="20"  width="90%" height="10" style="fill:#A91F01;stroke-width:3;stroke:#A91F01" /></svg> static').append("path")
      .attr("d", "M0,-5L10,0L0,5 L10,0 L0, -5")
      .style("stroke", "grey") // ARROWHEAD GREY
      .style("opacity", "0.6")
      .style("stroke-width", '1.5');
  legendLines.append('span').html('<svg width="70%" height="2"><rect rx="20" ry="20"  width="90%" height="10" style="fill:#625fad;stroke-width:3;stroke:#625fad" /></svg> dynamic')
  legendLines.append('span').html('<svg width="70%" height="2"><rect rx="20" ry="20"  width="90%" height="10" style="fill:#000000;stroke-width:3;stroke:#000000" /></svg> both')

  var legend2 = d3.select("body").append("div").attr("class", "rcorner2")
  var legendLines2 = legend2.append("div")
  //legendLines2.append('span').attr("height", "10%").html('<svg style="display: block;vertical-align:top" viewBox="-15 -15 300 300"><circle class="circLegend" r="10" style="fill:#FFFFFF;stroke-width:4;stroke:#CAB2C8" /><text class="textLegend" x="40%" y="4%" dy=".4em"> client </text></svg>')
  legendLines2.append('span').html('<svg viewBox="17 17.5 50 5" width="80%"><circle class="circLegend" r="2" stroke="#CAB2C8" stroke-width="1" fill="#FFFFFF" cx="20" cy="20"></circle></svg><span style="z-index: 2;/* right: 10%; */left: 30%;position: absolute;">client</span>')
  legendLines2.append('span').html('<svg viewBox="17 17.5 50 5" width="80%"><circle class="circLegend" r="2" stroke="#000000" stroke-width="1" fill="#CAB2C8" cx="20" cy="20"></circle></svg><span style="z-index: 2;/* right: 10%; */left: 30%;position: absolute;">library</span>')
  legendLines2.append('span').html('<svg viewBox="17 17.5 50 5" width="80%"><circle class="circLegend" r="2.2" stroke="#000000" stroke-width="0.1" fill="#CAB2C8" cx="20" cy="20"></circle></svg><span style="z-index: 2;/* right: 10%; */left: 30%;position: absolute;">dependency</span>')

  var showLblCheckbox = d3.select("h3").append("div").style("margin", "1em");
  showLblCheckbox.append("input")
    .attr("type", "checkbox").attr("id", "showLblCheckbox").attr("name", "showLblCheckbox").attr("value", "Show Package Names")
    .on('change', showLbls);
  showLblCheckbox.append("label")
    .attr("for", "showLblCheckbox").html('Show Package Names')


  var svg = d3.select("body").append("svg")
    .attr("width", width)
    .attr("height", height)
  //.on("dblclick", threshold); // EXPLODE ALL CONNECTED POINTS

  graphRec = JSON.parse(JSON.stringify(graph));

  //Creates the graph data structure out of the json data
  for (i = 0; i < graph.nodes.length; i++) {
    var fixedDict = JSON.parse(graph.nodes[i].fixedPos);
    if (fixedDict.isFixed === 'true') {
      graph.nodes[i].x = fixedDict.x;
      graph.nodes[i].y = fixedDict.y;
      graph.nodes[i].fixed = true;
    }
  };
// graph.nodes[0].x = 10;
//graph.nodes[0].y = height / 2;
//graph.nodes[0].fixed = true;
  force.nodes(graph.nodes)
    .links(graph.links)
    .start();

  //Create all the line svgs but without locations yet
  var link = svg.selectAll(".link")
    .data(graph.links)
    .enter().append("line")
    .attr("class", function(d) {return d.style;})
    .style("marker-end", () => config.directed ? "url(#suit)" : "none") // ARROWS IN EDGES
    .style("stroke-width", function(d) {return d.edge_width;}) // LINK-WIDTH
    .style("stroke", function(d) {return d.color;})  
    
  ;
  link.append("title")
    .text((d) => d['hover'])

  //  .style("stroke-width", 1); // WIDTH OF THE LINKS

  //Do the same with the circles for the nodes
  var node = svg.selectAll(".node")
    .data(graph.nodes)
    .enter().append("g")
    .attr("class", "node")
    .call(force.drag)
    .on('dblclick', connectedNodes); //Highliht ON/OFF

  node.append("circle")
    .attr("r", function(d) { return d.node_size; })					// NODE SIZE
    .style("fill", function(d) {return d.node_color;})				// NODE-COLOR
    .style("stroke-width", function(d) { return d.node_size_edge;})	// NODE-EDGE-SIZE
    .style("stroke", function(d) {return d.node_color_edge;})		// NODE-COLOR-EDGE

  // Text in nodes
  node.append("text")
    .attr("dx", 10)
    .attr("dy", ".35em")
    .text(function(d) {return d.node_name}) // NODE-TEXT
  //  .style("stroke", "gray");

  let showInHover = ["node_hover"]; // HOVER OVER TEXT
  node.append("title")
      .text((d) => Object.keys(d)
          .filter((key) => showInHover.indexOf(key) !== -1)
          .map((key) => `${d[key]}`)
          .join('\n')
      )

  //Now we are giving the SVGs co-ordinates - the force layout is generating the co-ordinates which this code is using to update the attributes of the SVG elements
  force.on("tick", function() {
    link.attr("x1", function(d) {
        return d.source.x;
      })
      .attr("y1", function(d) {
        return d.source.y;
      })
      .attr("x2", function(d) {
        return d.target.x;
      })
      .attr("y2", function(d) {
        return d.target.y;
      });
    d3.selectAll("circle:not(.circLegend)").attr("cx", function(d) {
        return d.x;
      })
      .attr("cy", function(d) {
        return d.y;
      });
    d3.selectAll("text:not(.textLegend)").attr("x", function(d) {
        return d.x;
      })
      .attr("y", function(d) {
        return d.y;
      });

    node.each(collide(config.collision)); //COLLISION DETECTION. High means a big fight to get untouchable nodes (default=0.5)

  });

  // --------- Directed lines -----------
  svg.append("defs").selectAll("marker")
      .data(["suit", "licensing", "resolved"])
    .enter().append("marker")
      .attr("id", function(d) { return d; })
      .attr("viewBox", "0 -5 10 10")
      .attr("refX", 25)
      .attr("refY", 0)
      .attr("markerWidth", 10)
      .attr("markerHeight", 10)
      .attr("orient", "auto")
      .attr("markerUnits", "userSpaceOnUse") // MAKE FIXED ARROW WIDTH
    .append("path")
      .attr("d", "M0,-5L10,0L0,5 L10,0 L0, -5")
      .style("stroke", "grey") // ARROWHEAD GREY
      .style("opacity", "0.6")
      .style("stroke-width", '1.5'); // THICKNESS OF ARROWHEAD
      

  // --------- End directed lines -----------

  //---Insert-------


  // collision detection

  var padding = 1, // separation between circles
    radius = 8;

  function collide(alpha) {
    var quadtree = d3.geom.quadtree(graph.nodes);
    return function(d) {
      var rb = 2 * radius + padding,
        nx1 = d.x - rb,
        nx2 = d.x + rb,
        ny1 = d.y - rb,
        ny2 = d.y + rb;
      quadtree.visit(function(quad, x1, y1, x2, y2) {
        if (quad.point && (quad.point !== d)) {
          var x = d.x - quad.point.x,
            y = d.y - quad.point.y,
            l = Math.sqrt(x * x + y * y);
          if (l < rb) {
            l = (l - rb) / l * alpha;
            d.x -= x *= l;
            d.y -= y *= l;
            quad.point.x += x;
            quad.point.y += y;
          }
        }
        return x1 > nx2 || x2 < nx1 || y1 > ny2 || y2 < ny1;
      });
    };
  }
  // collision detection end


  //Toggle stores whether the highlighting is on **********************
  var toggle = 0;
  //Create an array logging what is connected to what
  var linkedByIndex = {};
  for (i = 0; i < graph.nodes.length; i++) {
    linkedByIndex[i + "," + i] = 1;
  };
  graph.links.forEach(function(d) {
    linkedByIndex[d.source.index + "," + d.target.index] = 1;
  });
  //This function looks up whether a pair are neighbours
  function neighboring(a, b) {
    return linkedByIndex[a.index + "," + b.index];
  }

  function showLbls() {
    if (d3.select("#showLblCheckbox").node().checked == true){
      d3.selectAll("text:not(.textLegend)").text(function(o) {return o.node_hover});
    } else {
      d3.selectAll("text:not(.textLegend)").text("");
    }
  }

  function connectedNodes() {
    if (toggle == 0) {
      //Reduce the opacity of all but the neighbouring nodes
      d = d3.select(this).node().__data__;
      console.log(node.text);
      console.log(node.style);
      node.style("opacity", function(o) {
        return neighboring(d, o) | neighboring(o, d) ? 1 : 0.1;
      });
      link.style("opacity", function(o) {
        return d.index == o.source.index | d.index == o.target.index ? 1 : 0.1;
      });
      
      
      d3.selectAll("text:not(.textLegend)").text(function(o) {return neighboring(d, o) | neighboring(o, d) ? o.node_hover : ''}) // NODE-TEXT  */
      toggle = 1;
    } else {
      //Put them back to opacity=1
      node.style("opacity", 1);
      link.style("opacity", 1);
      d3.selectAll("text:not(.textLegend)").text(function(o) {return ''})
      toggle = 0;
    }
  }
  //*************************************************************


  //adjust threshold
  function threshold() {
    let thresh = this.value;

    console.log('Setting threshold', thresh)
    graph.links.splice(0, graph.links.length);

    for (var i = 0; i < graphRec.links.length; i++) {
      if (graphRec.links[i].edge_weight > thresh) {
        graph.links.push(graphRec.links[i]);
      }
    }
    restart();
  }

  d3.select("#thresholdSlider").on("change", threshold);

  //Restart the visualisation after any node and link changes
  function restart() {

    link = link.data(graph.links);
    link.exit().remove();
    link.enter().insert("line", ".node").attr("class", "link");
    link.style("stroke-width", function(d) {return d.edge_width;}); // WIDTH OF THE LINKS AFTER BREAKING WITH SLIDER
    link.style("marker-end", () => config.directed ? "url(#suit)" : "none") // ARROWS IN EDGES
    node = node.data(graph.nodes);
    node.enter().insert("circle", ".cursor").attr("class", "node").attr("r", 5).call(force.drag);
    force.start();
  }

  function arrow(p1,p2){
    var h1=15 // line thickness
    var h2=35 // arrow height
    var w2=22 // arrow width
    var deg = Math.atan2(p1.y - p2.y, p1.x - p2.x) * (180 / Math.PI);
    var len = Math.sqrt(Math.pow(p1.y - p2.y,2)+Math.pow(p1.x - p2.x,2))
    var arr = document.createElementNS(svgns,"path")
    var d = `M${p1.x} ${p1.y-h1/2}v${h1}h${h2/2-len}v${(h2-h1)/2}l${-w2} ${-h2/2}l${w2} ${-h2/2}v${(h2-h1)/2}z`
    arr.setAttribute("d",d)
    arr.setAttribute("transform",`rotate(${deg} ${p1.x} ${p1.y})`)
    arr.classList.add("arrow")
    return arr
  }

}
